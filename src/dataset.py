"""Dataset de PyTorch Geometric con los escaneos preprocesados de Teeth3DS.

Uso:
    python src/dataset.py data/splits/propio/train.txt data/procesado

Lee los identificadores de un fichero de split y carga los archivos .pt correspondientes
desde la carpeta de procesado.

Los escaneos descartados se identifican mediante descartados.txt y se excluyen automáticamente.

Todos los datos se cargan en memoria para evitar lecturas de disco durante cada época de entrenamiento.

Cada elemento es un objeto Data de PyTorch Geometric con:
    pos: coordenadas normalizadas (N, 3)
    y:   etiquetas de clase (N,), entre 0 y 32.
    id:  identificador del escaneo.

Se admite una transformación opcional, aplicada sobre una copia de los datos.
"""

import argparse
from pathlib import Path

import torch
from torch.utils.data import Dataset
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader

# Encía (0) + 32 dientes permanentes (1-32).
N_CLASES = 33

class EscaneosProcesados(Dataset):
    """Escaneos de un split (train, val o test) cargados desde los .pt."""

    def __init__(self, ruta_split, carpeta_procesado, transform = None):
        self.ruta_split = Path(ruta_split)
        self.carpeta_procesado = Path(carpeta_procesado)
        self.transform = transform

        # 1. Leer los identificadores del split.
        identificadores = [
            linea.strip()
            for linea in self.ruta_split.read_text(encoding = "utf-8").splitlines()
            if linea.strip()
        ]

        # Comprobar que no haya escaneos repetidos.
        if len(identificadores) != len(set(identificadores)):
            raise ValueError(f"Hay identificadores duplicados en {self.ruta_split}")

        # 2. Leer los escaneos descartados durante el preprocesado.
        ruta_descartado = self.carpeta_procesado / "descartados.txt"

        if ruta_descartado.exists():
            descartados = set(
                linea.strip()
                for linea in ruta_descartado.read_text(encoding = "utf-8").splitlines()
                if linea.strip()
            )
        else:
            descartados = set()

        # 3. Excluir los descartados que pertenecen a este split.
        self.descartados_en_split = [
            identificador 
            for identificador in identificadores
            if identificador in descartados
        ]

        identificadores_validos = [
            identificador
            for identificador in identificadores
            if identificador not in descartados
        ]

        # 4. Comprobar que existen todos los .pt necesarios.
        faltantes = [
            identificador
            for identificador in identificadores_validos
            if not (self.carpeta_procesado / f"{identificador}.pt").is_file()
        ]

        if faltantes:
            raise FileNotFoundError(
                f"Faltan {len(faltantes)} escaneos preprocesados "
                f"que no están en descartados.txt. "
                f"Ejemplos: {faltantes[:5]}"
            )

        # 5. Cargar todos los escaneos en memoria.
        self.datos = []

        for identificador in identificadores_validos:
            ruta_pt = self.carpeta_procesado / f"{identificador}.pt"

            contenido = torch.load(ruta_pt, map_location = "cpu", weights_only = True)

            # Comprobar que el identificador coincide.
            if contenido["id"] != identificador:
                raise ValueError(
                    f"Identificador incorrecto en {ruta_pt}: "
                    f"{contenido['id']} != {identificador}"
                )

            pos = contenido["pos"]
            y = contenido["y"]

            # Comprobar las dimensiones.
            if pos.ndim != 2 or pos.shape[1] != 3: raise ValueError(f"{ruta_pt}: pos debe tener forma (N, 3)")

            if y.ndim != 1 or len(y) != len(pos): 
                raise ValueError(
                    f"{ruta_pt}: dimensiones incompatibles "
                    f"entre pos e y"
                )

            # Las etiquetas deben ser enteros entre 0 y N_CLASES - 1.
            if y.dtype != torch.long: raise ValueError(f"{ruta_pt}: las etiquetas deben ser torch.long")

            if torch.any((y < 0) | (y >= N_CLASES)): raise ValueError(f"{ruta_pt}: hay etiquetas fuera del rango 0-{N_CLASES - 1}")

            # 6. Crear el objeto Data de PyTorch Geometric.
            data = Data(
                pos = pos,
                y = y,
                id = identificador
            )

            self.datos.append(data)

    def __len__(self):
        """Devuelve el número de escaneos válidos."""
        return len(self.datos)

    def __getitem__(self, i):
        """Devuelve un escaneo y aplica una transformación opcional."""
        data = self.datos[i]

        if self.transform is not None:
            data = self.transform(data.clone())

        return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description = __doc__.splitlines()[0]
    )

    parser.add_argument(
        "split", type = Path, help = "fichero train.txt, val.txt o test.txt"
    )

    parser.add_argument(
        "procesado", type = Path, help = "carpeta con los escaneos .pt"
    )

    args = parser.parse_args()

    # 1. Cargar el dataset.
    dataset = EscaneosProcesados(args.split, args.procesado)

    print("=== DATASET ===")
    print(f"Split: {args.split}")
    print(f"Escaneos válidos: {len(dataset)}")
    print(f"Descartados del split: {len(dataset.descartados_en_split)}")

    # 2. Crear un DataLoader de PyTorch Geometric.
    loader = DataLoader(dataset, batch_size = 8, shuffle = True)

    # 3. Obtener el primer lote.
    batch = next(iter(loader))

    print("\n=== PRIMER LOTE ===")
    print(f"Batch: {batch}")
    print(f"Posiciones: {batch.pos.shape}")
    print(f"Etiquetas: {batch.y.shape}")
    print(f"Escaneos del lote: {batch.batch.unique()}")