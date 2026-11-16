"""Dibuja las curvas de entrenamiento de PointNet++ con los dos splits.

Uso:
    python src/figura_curvas.py resultados/pointnet2_propio/registro.csv \
        resultados/pointnet2_oficial/registro.csv --salida figura_curvas.png

Panel izquierdo: pérdida de entrenamiento por época.
Panel derecho: mIoU de validación sin terceros molares por época.

Se marca la mejor época de cada split, correspondiente al máximo mIoU
de validación sin terceros molares.
"""

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Colores y estilos de línea para distinguir los splits.
ESTILOS = {
    "propio": {
        "color": "#2a78d6",
        "linestyle": "-",
        "label": "Split propio",
    },
    "oficial": {
        "color": "#eb6834",
        "linestyle": "--",
        "label": "Split oficial",
    }
}

def leer_registro(ruta):
    """Devuelve las épocas, la pérdida de train y el mIoU sin terceros molares."""
    epocas = []
    perdidas = []
    mious = []

    with open(ruta, newline="", encoding="utf-8") as fichero:
        lector = csv.DictReader(fichero)

        for fila in lector:
            epocas.append(int(fila["epoca"]))
            perdidas.append(float(fila["perdida_train"]))
            mious.append(float(fila["miou_val_sin_3m"]))

    if not epocas:
        raise ValueError(f"El registro está vacío: {ruta}")

    return epocas, perdidas, mious

def dibujar(registros, ruta_salida):
    """Dibuja los dos paneles y guarda la figura"""

    fig, (ax_perdida, ax_miou) = plt.subplots(1, 2, figsize=(9, 3.5), sharex = True)

    for split, (epocas, perdidas, mious) in registros.items():
        estilo = ESTILOS[split]

        # Panel izquierdo: pérdida de entrenamiento.
        ax_perdida.plot(
            epocas,
            perdidas,
            linewidth = 2,
            **estilo
        )

        # Panel derecho: mIoU de validación sin terceros molares.
        ax_miou.plot(
            epocas,
            mious,
            linewidth = 2,
            **estilo
        )

        # Encontrar la época con mayor mIoU.
        mejor_indice = max(
            range(len(mious)), key = lambda i: mious[i]
        )

        mejor_epoca = epocas[mejor_indice]
        mejor_miou = mious[mejor_indice]

        # Marcar la mejor época con un punto.
        ax_miou.scatter(
            mejor_epoca,
            mejor_miou,
            s = 45,
            color = estilo["color"],
            edgecolor = "white",
            linewidth = 0.8,
            zorder = 3
        )

        # Etiqueta con el valor y la época.
        etiqueta = (
            f"{mejor_miou:.3f}".replace(".", ",")
            + f" (ép. {mejor_epoca})"
        )

        # Desplazamientos distintos para evitar solapamientos.
        desplazamiento = (
            (0, -16) if split == "propio" else (0, 8)
        )

        ax_miou.annotate(
            etiqueta,
            xy = (mejor_epoca, mejor_miou),
            xytext = desplazamiento,
            textcoords = "offset points",
            fontsize = 8,
            color = "#333333",
            ha = "center"
        )

        print(
            f"{estilo['label']}: "
            f"mejor época = {mejor_epoca}, "
            f"mIoU = {mejor_miou:.6f}"
        )

    # Etiquetas de los ejes.
    ax_perdida.set_xlabel("Época")
    ax_perdida.set_ylabel("Pérdida de entrenamiento")

    ax_miou.set_xlabel("Época")
    ax_miou.set_ylabel("mIoU de validación (sin terceros molares)")

    # Una sola leyenda, en el panel izquierdo.
    ax_perdida.legend(
        frameon = False,
        loc = "upper right"
    )

    # Formato común de los dos paneles.
    for ax in (ax_perdida, ax_miou):
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(
            axis = "y",
            color = "#e0e0e0",
            linewidth = 0.8
        )
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ","))
        )
        ax.set_axisbelow(True)

    # Mantener automática la escala vertical de cada panel.
    fig.tight_layout()

    # Guardar como PDF vectorial o PNG de alta resolución.
    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents = True, exist_ok = True)

    fig.savefig(
        ruta_salida,
        dpi = 200,
        bbox_inches = "tight"
    )

    plt.close(fig)

    print(f"Figura guardada en {ruta_salida}")


def main():
    parser = argparse.ArgumentParser(
        description = __doc__.splitlines()[0]
    )

    parser.add_argument(
        "propio",
        type = Path,
        help = "registro.csv del split propio"
    )

    parser.add_argument(
        "oficial",
        type = Path,
        help = "registro.csv del split oficial"
    )

    parser.add_argument(
        "--salida",
        default = Path("resultados/figura_curvas.pdf"),
        help = "ruta de salida de la figura"
    )

    args = parser.parse_args()

    registros = {
        "propio": leer_registro(args.propio),
        "oficial": leer_registro(args.oficial)
    }

    dibujar(registros, args.salida)


if __name__ == "__main__":
    main()