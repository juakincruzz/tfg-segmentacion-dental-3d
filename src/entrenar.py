"""Entrena PointNet++ para la segmentación semántica de Teeth3DS.

Uso:
    python src/entrenar.py --epocas 2

El entrenamiento utiliza los escaneos preprocesados de train.txt y evalúa el modelo 
al final de cada época utilizando val.txt.

Guarda en el directorio de salida:
    mejor.pt:       pesos del modelo con mayor mIoU de validación sin terceros molares.
    registro.csv:   pérdida, exactitud, mIoU, learning rate, tiempo y
                    memoria de GPU de cada época.
    iou_mejor.csv:  IoU de cada clase del mejor modelo.

La pérdida utilizada es cross_entropy sin pesos por clase.

El mIoU se calcula sobre los puntos muestreados, no sobre los vértices
originales de las mallas. Las métricas oficiales del reto se calcularán 
posteriormente sobre las mallas completas.

El conjunto de prueba no se utiliza durante el entrenamiento.
"""

import argparse
import csv
import math
import random
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from torch_geometric.loader import DataLoader

from dataset import EscaneosProcesados
from modelo import N_CLASES, PointNet2Seg
from teeth3ds import FDI_INFERIOR, FDI_SUPERIOR

# Clases de los terceros molares: 18, 28, 38, 48.
TERCEROS_MOLARES = [
    clase
    for clase, fdi in enumerate(FDI_SUPERIOR + FDI_INFERIOR, start = 1)
    if fdi % 10 == 8
]

def matriz_confusion(pred, y, n_clases = N_CLASES):
    """Calcula la matriz de confusión.
    
    Filas: clases reales.
    Columnas: clases predichas.
    
    Devuelve un tensor de forma (n_clases, n_clases)
    """
    indices = y.long() * n_clases + pred.long()

    confusion = torch.bincount(
        indices, 
        minlength = n_clases ** 2
    )

    return confusion.reshape(n_clases, n_clases)


def metricas(confusion):
    """Calcula exactitud global, IoU por clase, mIoU y mIoU sin terceros molares.
    
    El mIoU solo incluye las clases presentes en las etiquetas reales.
    Las clases ausentes reciben NaN en el vector de IoU y no intervienen
    en la media.

    El mIoU sin terceros molares excluye además las clases 18, 28, 38 y 48,
    que faltan en la mayoría de los escaneos. Es el que se usa para elegir el mejor modelo.
    """
    confusion = confusion.to(torch.float64)

    # Aciertos de cada clase: diagonal de la matriz.
    aciertos = confusion.diag()

    # Total de puntos.
    total = confusion.sum()

    exactitud = (
        (aciertos.sum() / total).item()
        if total > 0 else float("nan")
    )

    # Total de puntos reales y predichos de cada clase.
    reales = confusion.sum(dim = 1)
    predichos = confusion.sum(dim = 0)

    # Intersección / unión.
    union = reales + predichos - aciertos

    # Solo considerar clases que aparecen en las etiquetas reales.
    presentes = reales > 0

    iou = torch.full((confusion.size(0),), float("nan"), dtype = torch.float64, device = confusion.device)

    iou[presentes] = aciertos[presentes] / union[presentes]

    miou = (
        iou[presentes].mean().item()
        if presentes.any() else float("nan")
    )

    # mIoU sin terceros molares.
    es_tercero = torch.zeros(
        confusion.size(0), dtype = torch.bool, device = confusion.device
    )

    es_tercero[TERCEROS_MOLARES] = True

    seleccion = presentes & ~es_tercero

    miou_sin_terceros = (
        iou[seleccion].mean().item()
        if seleccion.any() else float("nan")
    )

    return exactitud, iou, miou, miou_sin_terceros


def entrenar_epoca(modelo, loader, optimizador, dispositivo):
    """Entrena una época y devuelve la pérdida media por punto."""
    modelo.train()

    perdida_acumulada = 0.0
    puntos_totales = 0

    for batch in loader:
        batch = batch.to(dispositivo)

        # Reiniciar gradientes.
        optimizador.zero_grad()

        # Predicción de logits.
        salida = modelo(batch)

        # Entropía cruzada sin pesos por clase.
        perdida = F.cross_entropy(
            salida,
            batch.y,
        )

        # Retropropagación.
        perdida.backward()

        # Actualizar los parámetros.
        optimizador.step()

        # Acumular la pérdida ponderada por el número de puntos.
        n_puntos = batch.y.numel()

        perdida_acumulada += perdida.item() * n_puntos
        puntos_totales += n_puntos

    return perdida_acumulada / puntos_totales


@torch.no_grad()
def evaluar(modelo, loader, dispositivo):
    """Evalúa el modelo acumulando la matriz de confusión."""
    modelo.eval()

    confusion = torch.zeros(
        (N_CLASES, N_CLASES), 
        dtype = torch.long, 
        device = dispositivo
    )

    for batch in loader:
        batch = batch.to(dispositivo)

        # Obtener logits y clases predichas.
        salida = modelo(batch)
        pred = salida.argmax(dim = 1)

        # Acumular la matriz de confusión del lote.
        confusion += matriz_confusion(pred, batch.y)

    return metricas(confusion)


def guardar_iou(iou, ruta):
    """Guarda el IoU por clase, indicando su etiqueta FDI."""
    fdi = FDI_SUPERIOR + FDI_INFERIOR

    with ruta.open("w", encoding = "utf-8", newline = "") as fichero:
        escritor = csv.writer(fichero)

        escritor.writerow(["clase", "etiqueta", "iou"])

        for clase, valor in enumerate(iou.tolist()):
            etiqueta = "encia" if clase == 0 else str(fdi[clase - 1])

            # Las clases ausentes se guardan sin valor.
            valor_csv = (
                f"{valor:.6f}" 
                if not math.isnan(valor)
                else ""
            )

            escritor.writerow([clase, etiqueta, valor_csv])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description = __doc__.splitlines()[0]
    )

    parser.add_argument(
        "--splits", type = Path, default = Path("data/splits/propio"), 
        help = "carpeta que contiene train.txt y val.txt"
    )

    parser.add_argument(
        "--procesado", type = Path, default = Path("data/procesado"),
        help = "carpeta con los escaneos .pt"
    )

    parser.add_argument(
        "--epocas", type = int, default = 30, help = "número de épocas de entrenamiento"
    )

    parser.add_argument(
        "--batch-size", type = int, default = 8, help = "número de escaneos por lote"
    )

    parser.add_argument(
        "--lr", type = float, default = 1e-3, help = "tasa de aprendizaje inicial"
    )

    parser.add_argument(
        "--salida", type = Path, default = Path("runs/pointnet2_propio"), 
        help = "directorio donde guardar los resultados"
    )

    parser.add_argument(
        "--semilla", type = int, default = 42, help = "semilla aleatoria"
    )

    parser.add_argument(
        "--sobreescribir", action = "store_true", help = "permite sobreescribir los resultados de una ejecución anterior"
    )

    args = parser.parse_args()

    if args.epocas < 1: parser.error("--epocas debe ser positivo")

    if args.batch_size < 1: parser.error("--batch-size debe ser positivo")

    if args.lr <= 0: parser.error("--lr debe ser positivo")

    # ------------------------------------------------------------
    # 1. Configuración
    # ------------------------------------------------------------

    random.seed(args.semilla)
    torch.manual_seed(args.semilla)

    if (args.salida / "registro.csv").exists() and not args.sobreescribir:
        parser.error(
            f"{args.salida} ya contiene resultados; "
            "usa otra --salida o añade --sobreescribir"
        )

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.semilla)

    dispositivo = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    args.salida.mkdir(parents = True, exist_ok = True)

    print("=== CONFIGURACIÓN ===")
    print(f"Dispositivo: {dispositivo}")
    print(f"Semilla: {args.semilla}")
    print(f"Splits: {args.splits}")
    print(f"Épocas: {args.epocas}")
    print(f"Batch size: {args.batch_size}")
    print(f"Learning rate: {args.lr}")

    # ------------------------------------------------------------
    # 2. Cargar los datasets
    # ------------------------------------------------------------

    train_dataset = EscaneosProcesados(
        args.splits / "train.txt",
        args.procesado
    )

    val_dataset = EscaneosProcesados(
        args.splits / "val.txt",
        args.procesado
    )

    if len(train_dataset) == 0 or len(val_dataset) == 0:
        raise ValueError("Los conjuntos de entrenamiento y validación deben contener al menos un escaneo.")

    print("\n=== DATOS ===")
    print(f"Entrenamiento: {len(train_dataset)} escaneos")
    print(f"Validación: {len(val_dataset)} escaneos")

    print(
        "Descartados entrenamiento: "
        f"{len(train_dataset.descartados_en_split)}"
    )

    print(
        "Descartados validación: "
        f"{len(val_dataset.descartados_en_split)}"
    )

    # Generador con semilla para el orden de los lotes.
    generador = torch.Generator()
    generador.manual_seed(args.semilla)

    train_loader = DataLoader(
        train_dataset,
        batch_size = args.batch_size,
        shuffle = True,
        generator = generador
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size = args.batch_size,
        shuffle = False
    )

    # ------------------------------------------------------------
    # 3. Modelo y optimizador
    # ------------------------------------------------------------

    modelo = PointNet2Seg(n_clases = N_CLASES).to(dispositivo)

    optimizador = torch.optim.Adam(
        modelo.parameters(),
        lr = args.lr
    )

    # Reducir el learning rate a la mitad cada 10 épocas.
    planificador = torch.optim.lr_scheduler.StepLR(
        optimizador,
        step_size = 10,
        gamma = 0.5
    )

    n_parametros = sum(
        p.numel() for p in modelo.parameters()
    )

    print(f"\nParámetros del modelo: {n_parametros:,}")

    # ------------------------------------------------------------
    # 4. Preparar el registro CSV
    # ------------------------------------------------------------

    ruta_registro = args.salida / "registro.csv"
    ruta_mejor = args.salida / "mejor.pt"
    ruta_iou = args.salida / "iou_mejor.csv"

    columnas = [
        "epoca", 
        "perdida_train",
        "exactitud_val",
        "miou_val",
        "miou_val_sin_3m",
        "lr",
        "segundos",
        "memoria_GB"
    ]

    with ruta_registro.open("w", newline = "", encoding = "utf-8") as fichero:
        escritor = csv.writer(fichero)
        escritor.writerow(columnas)

    # ------------------------------------------------------------
    # 5. Entrenamiento
    # ------------------------------------------------------------

    mejor_miou_sin_terceros = -1.0
    mejor_miou_33 = None
    mejor_epoca = 0
    mejor_iou = None

    print("\n=== ENTRENAMIENTO ===")

    for epoca in range(1, args.epocas + 1):

        # Sincronizar antes de medir tiempo.
        if dispositivo.type == "cuda":
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()

        inicio = time.perf_counter()

        # Learning rate utilizado esta época.
        lr_actual = optimizador.param_groups[0]["lr"]

        # Entrenamiento.
        perdida_train = entrenar_epoca(
            modelo, train_loader, optimizador, dispositivo
        )

        # Evaluación en validación.
        exactitud_val, iou_val, miou_val, miou_sin_terceros = evaluar(
            modelo, val_loader, dispositivo
        )

        # Sincronizar para medir correctamente el tiempo.
        if dispositivo.type == "cuda":
            torch.cuda.synchronize()

        segundos = time.perf_counter() - inicio

        # Memoria máxima de GPU durante la época.
        if dispositivo.type == "cuda":
            memoria_gb = torch.cuda.max_memory_allocated() / 1e9
        else:
            memoria_gb = None

        # ------------------------------------------------------------
        # 6. Guardar el mejor modelo
        # ------------------------------------------------------------

        mejora = miou_sin_terceros > mejor_miou_sin_terceros

        if mejora:
            mejor_miou_sin_terceros = miou_sin_terceros
            mejor_miou_33 = miou_val
            mejor_epoca = epoca
            mejor_iou = iou_val.cpu().clone()

            torch.save(modelo.state_dict(), ruta_mejor)

            guardar_iou(mejor_iou, ruta_iou)

        # ------------------------------------------------------------
        # 7. Registrar la época
        # ------------------------------------------------------------

        with ruta_registro.open("a", newline = "", encoding = "utf-8") as fichero:
            escritor = csv.writer(fichero)

            escritor.writerow([
                epoca,
                f"{perdida_train:.6f}",
                f"{exactitud_val:.6f}",
                f"{miou_val:.6f}",
                f"{miou_sin_terceros:.6f}",
                f"{lr_actual:.8f}",
                f"{segundos:.2f}",
                (
                    f"{memoria_gb:.3f}" if memoria_gb is not None else ""
                )
            ])

        # Actualizar el learning rate para la siguiente época.
        planificador.step()

        # ------------------------------------------------------------
        # 8. Mostrar progreso
        # ------------------------------------------------------------

        mensaje = (
            f"Época {epoca}/{args.epocas} | "
            f"Loss: {perdida_train:.4f} | "
            f"Acc val: {exactitud_val:.4f} | "
            f"mIoU val: {miou_val:.4f} | "
            f"mIoU sin 3M: {miou_sin_terceros:.4f} | "
            f"LR: {lr_actual:.6f} | "
            f"Tiempo: {segundos:.1f} s"
        )

        if memoria_gb is not None:
            mensaje += f" | GPU: {memoria_gb:.2f} GB"

        if mejora:
            mensaje += " | MEJOR"

        print(mensaje, flush = True)

    # ------------------------------------------------------------
    # 9. Resumen final
    # ------------------------------------------------------------

    print("\n=== RESULTADO FINAL ===")
    print(f"Mejor época: {mejor_epoca}")
    print(f"mIoU de 33 clases: {mejor_miou_33:.4f}")
    print(f"mIoU sin terceros molares: {mejor_miou_sin_terceros:.4f}")
    print(f"Modelo guardado en: {ruta_mejor}")
    print(f"Registro guardado en: {ruta_registro}")
    print(f"IoU por clase guardado en: {ruta_iou}")

    if mejor_iou is not None:
        print("\n=== IoU POR CLASE DEL MEJOR MODELO ===")

        fdi = FDI_SUPERIOR + FDI_INFERIOR

        for clase, valor in enumerate(mejor_iou.tolist()):
            etiqueta = "Encia" if clase == 0 else str(fdi[clase - 1])

            if math.isnan(valor):
                print(f"Clase {clase:02d} ({etiqueta}): ausente")
            else:
                print(
                    f"Clase {clase:02d} ({etiqueta}): "
                    f"{valor:.4f}"
                )