"""PointNet++ para la segmentación semántica de escaneos intraorales.

Uso:
    python src/modelo.py --batch-size 8

La red recibe un lote de escaneos de PyTorch Geometric con:
    pos:   coordenadas normalizadas de los puntos (N_total, 3).
    batch: identificador del escaneo al que pertenece cada punto.

Devuelve:
    logits: puntuaciones de las 33 clases para cada punto (N_total, 33).

Arquitectura basada en PointNet++ (Qi et al., 2017) y adaptada de los
ejemplos oficiales de PyTorch Geometric:
    examples/pointnet2_segmentation.py
    examples/pointnet2_classification.py

Utiliza tres niveles de set abstraction, uno global y cuatro niveles de
feature propagation. La salida no aplica softmax porque se utilizará 
torch.nn.functional.cross_entropy durante el entrenamiento.
"""

import argparse
from pathlib import Path

import torch
import torch.nn.functional as F
from torch_geometric.loader import DataLoader
from torch_geometric.nn import (MLP, PointNetConv, fps, global_max_pool, knn_interpolate, radius)

from dataset import N_CLASES, EscaneosProcesados


class SAModule(torch.nn.Module):
    """Set abstraction: FPS, agrupación por radio y PointNetConv."""

    def __init__(self, ratio, r, nn):
        super().__init__()

        self.ratio = ratio
        self.r = r

        self.conv = PointNetConv(nn, add_self_loops = False)

    def forward(self, x, pos, batch):
        # 1. Seleccionar centros mediante FPS.
        # Durante la evaluación se utiliza un inicio fijo.
        idx = fps(pos, batch, ratio = self.ratio, random_start = self.training)

        # 2. Buscar los vecinos de cada centro dentro del radio.
        row, col = radius(pos, pos[idx], self.r, batch, batch[idx], max_num_neighbors = 64)

        # 3. Construir las conexiones entre vecinos y centros.
        edge_index = torch.stack([col, row], dim = 0)

        # 4. Obtener las características de los centros.
        x_dest = None if x is None else x[idx]

        # 5. Aplicar PointNetConv.
        x = self.conv((x, x_dest), (pos, pos[idx]), edge_index)

        return x, pos[idx], batch[idx]


class GlobalSAModule(torch.nn.Module):
    """Resume cada escaneo mediante un único vector de características."""

    def __init__(self, nn):
        super().__init__()

        self.nn = nn

    def forward(self, x, pos, batch):
        # Concatenar características y coordenadas.
        x = torch.cat([x, pos], dim = 1)

        # Aplicar la MLP.
        x = self.nn(x)

        # Obtener un vector por escaneo.
        x = global_max_pool(x, batch)

        # Crear una posición ficticia por escaneo.
        pos = pos.new_zeros((x.size(0), 3))

        batch = torch.arange(x.size(0), device = batch.device)

        return x, pos, batch


class FPModule(torch.nn.Module):
    """Feature propagation: interpolación y conexiones skip."""

    def __init__(self, k, nn):
        super().__init__()

        self.k = k
        self.nn = nn

    def forward(self, x, pos, batch, x_skip, pos_skip, batch_skip):
        # 1. Interpolar hacia los puntos del nivel anterior (más denso).
        x = knn_interpolate(x, pos, pos_skip, batch, batch_skip, k = self.k)

        # 2. Concatenar las características del nivel anterior.
        if x_skip is not None: x = torch.cat([x, x_skip], dim = 1)

        # 3. Aplicar la MLP.
        x = self.nn(x)

        return x, pos_skip, batch_skip


class PointNet2Seg(torch.nn.Module):
    """PointNet++ con tres niveles SA y cuatro niveles FP."""

    def __init__(self, n_clases = N_CLASES):
        super().__init__()

        # ---------------------------------------------------
        # SET ABSTRACTION (SA)
        # ---------------------------------------------------

        # SA1: 16000 -> 4000 puntos.
        # Sin características iniciales: solo coordenadas relativas.
        self.sa1 = SAModule(
            ratio = 0.25,
            r = 0.05,
            nn = MLP([3, 64, 64, 128])
        )

        # SA2: 4000 -> 1000 puntos.
        self.sa2 = SAModule(
            ratio = 0.25,
            r = 0.1,
            nn = MLP([128 + 3, 128, 128, 256])
        )

        # SA3: 1000 -> 250 puntos.
        self.sa3 = SAModule(
            ratio = 0.25,
            r = 0.2,
            nn = MLP([256 + 3, 256, 256, 512])
        )

        # SA global: 250 -> 1 vector por escaneo.
        self.sa_global = GlobalSAModule(
            MLP([512 + 3, 512, 1024])
        )

        # ---------------------------------------------------
        # FEATURE PROPAGATION (FP)
        # ---------------------------------------------------

        # Global -> SA3.
        # 1024 canales + 512 del skip.
        self.fp4 = FPModule(
            k = 1,
            nn = MLP([1024 + 512, 512, 256])
        )

        # SA3 -> SA2.
        # 256 canales + 256 del skip.
        self.fp3 = FPModule(
            k = 3,
            nn = MLP([256 + 256, 256, 256])
        )

        # SA2 -> SA1.
        # 256 canales + 128 del skip.
        self.fp2 = FPModule(
            k = 3,
            nn = MLP([256 + 128, 256, 128])
        )

        # SA1 -> puntos originales.
        # No hay características iniciales para concatenar.
        self.fp1 = FPModule(
            k = 3,
            nn = MLP([128, 128, 128, 128])
        )

        # ---------------------------------------------------
        # CABEZA DE SEGMENTACIÓN
        # ---------------------------------------------------

        self.mlp = MLP(
            [128, 128, 128, n_clases],
            dropout = 0.5,
            norm = None
        )

    def forward(self, data):
        # Nivel inicial: únicamente las posiciones.
        # DataLoader proporciona el vector batch.
        sa0 = (None, data.pos, data.batch)

        # ---------------------------------------------------
        # CAMINO DESCENDENTE
        # ---------------------------------------------------

        sa1 = self.sa1(*sa0)
        sa2 = self.sa2(*sa1)
        sa3 = self.sa3(*sa2)
        sa4 = self.sa_global(*sa3)

        # ---------------------------------------------------
        # CAMINO ASCENDENTE
        # ---------------------------------------------------

        fp4 = self.fp4(*sa4, *sa3)
        fp3 = self.fp3(*fp4, *sa2)
        fp2 = self.fp2(*fp3, *sa1)
        fp1 = self.fp1(*fp2, *sa0)

        x, _, _ = fp1

        # Logits por punto, sin softmax.
        return self.mlp(x)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description = "Prueba de PointNet++ con escaneos de Teeth3DS"
    )

    parser.add_argument(
        "--split", type = Path, default = Path("data/splits/propio/train.txt"),
        help = "fichero con los identificadores de los escaneos"
    )

    parser.add_argument(
        "--procesado", type = Path, default = Path("data/procesado"),
        help = "carpeta con los archivos .pt"
    )

    parser.add_argument(
        "--batch-size", type = int, default = 8, help = "número de escaneos por lote"
    )

    args = parser.parse_args()

    if args.batch_size < 1: parser.error("--batch-size debe ser positivo")

    # Semilla para reproducibilidad.
    torch.manual_seed(42)

    dispositivo = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"Dispositivo: {dispositivo}")
    print(f"Número de clases: {N_CLASES}")

    # ---------------------------------------------------
    # 1. Cargar los escaneos
    # ---------------------------------------------------

    dataset = EscaneosProcesados(
        args.split,
        args.procesado
    )

    loader = DataLoader(
        dataset,
        batch_size = args.batch_size,
        shuffle = True
    )

    batch = next(iter(loader)).to(dispositivo)

    print(f"Escaneos en el lote: {batch.num_graphs}")
    print(f"Puntos de entrada: {batch.pos.shape}")

    # ---------------------------------------------------
    # 2. Crear el modelo
    # ---------------------------------------------------

    modelo = PointNet2Seg().to(dispositivo)
    modelo.train()

    n_parametros = sum(p.numel() for p in modelo.parameters())

    print(f"Parámetros del modelo: {n_parametros:,}")

    # ---------------------------------------------------
    # 3. Forward
    # ---------------------------------------------------

    if dispositivo.type == "cuda": 
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()

    salida = modelo(batch)

    print(f"Forma de salida: {salida.shape}")

    assert salida.shape == (
        batch.pos.size(0),
        N_CLASES,
    ), "La salida no tiene las dimensiones esperadas"

    # ---------------------------------------------------
    # 4. Backward de pruebas
    # ---------------------------------------------------

    perdida = F.cross_entropy(salida, batch.y)

    perdida.backward()

    print(f"Pérdida de prueba: {perdida.item():.4f}")
    print("Backward completado correctamente")

    # ---------------------------------------------------
    # 5. Memoria utilizada
    # ---------------------------------------------------

    if dispositivo.type == "cuda":
        torch.cuda.synchronize()

        memoria_maxima = (torch.cuda.max_memory_allocated() / 1e9)

        memoria_reservada = (torch.cuda.max_memory_reserved() / 1e9)

        print(f"Memoria máxima asignada: {memoria_maxima:.2f} GB")
        print(f"Memoria máxima reservada: {memoria_reservada:.2f} GB")
    else:
        print("Memoria GPU: no disponible (ejecución en CPU)")