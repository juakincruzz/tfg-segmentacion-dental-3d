"""Cuenta los dientes presentes en cada escaneo de Teeth3DS.

Uso:
    python src/conteo_dientes.py data [--histograma figura.png]

Imprime cuántos dientes tiene cada escaneo de media, cuántos tienen la
arcada completa y qué dientes faltan con más frecuencia.
"""

import argparse
from collections import Counter

import numpy as np

from teeth3ds import (
    FDI_POR_ARCADA,
    dientes_ausentes,
    dientes_presentes,
    es_tercer_molar,
    leer_anotacion,
    listar_escaneos,
)


def contar(raiz):
    """Devuelve una fila por escaneo con sus dientes presentes y ausentes.

    n_instancias se guarda aparte para comprobar después que cada diente
    tiene un número FDI distinto.
    """
    filas = []
    for ruta in listar_escaneos(raiz):
        anotacion = leer_anotacion(ruta)
        arcada = anotacion["jaw"]
        presentes = dientes_presentes(anotacion["labels"])
        n_instancias = len(set(anotacion["instances"].tolist()) - {0})
        filas.append({
            "id": anotacion["id_patient"],
            "arcada": arcada,
            "presentes": presentes,
            "ausentes": dientes_ausentes(presentes, arcada),
            "n_instancias": n_instancias,
        })
    return filas


def resumir(filas):
    """Imprime el resumen y devuelve el número de dientes de cada escaneo.

    Los porcentajes se dan también sin terceros molares, porque faltan con
    mucha frecuencia (sobre todo en pacientes jóvenes) e inflarían la tasa
    de ausencias.
    """
    n = np.array([len(f["presentes"]) for f in filas])
    sin_terceros = np.array(
        [sum(not es_tercer_molar(d) for d in f["presentes"]) for f in filas]
    )
    print(f"Escaneos: {len(filas)} "
          f"({sum(f['arcada'] == 'upper' for f in filas)} superiores, "
          f"{sum(f['arcada'] == 'lower' for f in filas)} inferiores)")
    print(f"Dientes por escaneo: media {n.mean():.2f}, "
          f"mediana {np.median(n):.0f}, mín {n.min()}, máx {n.max()} (de 16)")
    print(f"Sin contar terceros molares: media {sin_terceros.mean():.2f} (de 14)")
    print(f"Arcada completa (16): {(n == 16).mean():.1%}")
    print(f"Arcada completa sin terceros molares (14): "
          f"{(sin_terceros == 14).mean():.1%}")

    discrepancias = [f["id"] for f in filas
                     if f["n_instancias"] != len(f["presentes"])]
    print(f"Escaneos con distinto número de instancias que de etiquetas: "
          f"{len(discrepancias)}")

    for arcada, fdi in FDI_POR_ARCADA.items():
        de_arcada = [f for f in filas if f["arcada"] == arcada]
        ausencias = Counter(d for f in de_arcada for d in f["ausentes"])
        print(f"\nAusencias por diente, arcada {arcada} ({len(de_arcada)} escaneos):")
        for d in fdi:
            print(f"  {d}: {ausencias[d] / len(de_arcada):6.1%}")
    return n


def dibujar_histograma(n, ruta):
    """Guarda el histograma de dientes por escaneo en ruta."""
    # matplotlib solo hace falta si se pide la figura.
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 3.5))
    # Bordes desplazados 0.5 para que cada barra quede centrada en un entero.
    ax.hist(n, bins=np.arange(n.min(), 18) - 0.5, edgecolor="white")
    ax.set_xlabel("Dientes presentes en el escaneo")
    ax.set_ylabel("Número de escaneos")
    ax.set_xticks(range(n.min(), 17))
    fig.tight_layout()
    fig.savefig(ruta, dpi=200)
    print(f"\nHistograma guardado en {ruta}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("raiz", help="carpeta con las subcarpetas upper/ y lower/")
    parser.add_argument("--histograma", help="ruta donde guardar el histograma")
    args = parser.parse_args()

    n = resumir(contar(args.raiz))
    if args.histograma:
        dibujar_histograma(n, args.histograma)
