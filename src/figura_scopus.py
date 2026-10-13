"""Dibuja el número de publicaciones por año a partir del CSV de Scopus.

Uso:
    python src/figura_scopus.py Scopus-Analyze-Year.csv figura.png --anio-busqueda 2026

El CSV es el que exporta Scopus en "Analyze results" -> "Documents by year".
Los años posteriores al de la búsqueda (artículos en prensa) se descartan, y
el año de la búsqueda se marca como incompleto.
"""

import argparse
import csv

import matplotlib.pyplot as plt


def leer_csv_scopus(ruta):
    """Devuelve {año: número de documentos} ignorando la cabecera de Scopus.

    Scopus añade líneas de texto antes de los datos; solo se conservan las
    filas cuyas dos primeras columnas son números. utf-8-sig quita el BOM.
    """
    conteo = {}
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        for fila in csv.reader(f):
            if len(fila) >= 2 and fila[0].isdigit() and fila[1].isdigit():
                conteo[int(fila[0])] = int(fila[1])
    return conteo


def dibujar(conteo, anio_busqueda, ruta_salida):
    """Dibuja el diagrama de barras y lo guarda en ruta_salida.

    El eje va del primer año del CSV al de la búsqueda: así se descartan
    los años posteriores y los años sin publicaciones aparecen con 0.
    """
    anios = list(range(min(conteo), anio_busqueda + 1))
    valores = [conteo.get(a, 0) for a in anios]

    fig, ax = plt.subplots(figsize=(7, 3.5))
    barras = ax.bar(anios, valores, color="#4C72B0", edgecolor="white")
    # El año en curso está incompleto: se dibuja más claro y rayado.
    # El rayado toma el color del borde, así que el borde va en azul oscuro.
    barras[-1].set_facecolor("#D5DEED")
    barras[-1].set_hatch("//")
    barras[-1].set_edgecolor("#4C72B0")

    ax.set_xlabel("Año de publicación")
    ax.set_ylabel("Número de documentos")
    ax.set_xticks(anios[::2] if len(anios) > 15 else anios)
    ax.tick_params(axis="x", rotation=45)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(ruta_salida, dpi=200)
    print(f"Figura guardada en {ruta_salida} "
          f"({sum(valores)} documentos entre {anios[0]} y {anio_busqueda})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv", help="CSV exportado de Scopus")
    parser.add_argument("salida", help="ruta de la figura (.png o .pdf)")
    parser.add_argument("--anio-busqueda", type=int, required=True,
                        help="año en que se hizo la búsqueda; se marca incompleto")
    args = parser.parse_args()

    dibujar(leer_csv_scopus(args.csv), args.anio_busqueda, args.salida)
