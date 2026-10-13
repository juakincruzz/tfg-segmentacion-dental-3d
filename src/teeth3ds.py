"""Lectura de escaneos de Teeth3DS y utilidades sobre la numeración FDI.

Cada escaneo es un par <id>_<arcada>.obj / <id>_<arcada>.json. El JSON trae
una etiqueta FDI por vértice en "labels" (0 = encía) y un identificador de
diente por vértice en "instances" (0 = encía).
"""

import json
from pathlib import Path

import numpy as np

# Arcada completa en notación FDI: cuadrante (1-4) seguido de posición (1-8).
# Superior: cuadrantes 1 y 2. Inferior: cuadrantes 3 y 4.
FDI_SUPERIOR = [c * 10 + p for c in (1, 2) for p in range(1, 9)]
FDI_INFERIOR = [c * 10 + p for c in (3, 4) for p in range(1, 9)]
FDI_POR_ARCADA = {"upper": FDI_SUPERIOR, "lower": FDI_INFERIOR}


def es_tercer_molar(fdi):
    """Indica si el diente es un tercer molar (posición 8: 18, 28, 38, 48)."""
    return fdi % 10 == 8


def leer_anotacion(ruta_json):
    """Lee el JSON de un escaneo y convierte labels e instances en arrays.

    Devuelve el diccionario del JSON tal cual, con las claves "id_patient",
    "jaw" ("upper" o "lower"), "labels" e "instances".
    """
    with open(ruta_json) as f:
        anotacion = json.load(f)
    anotacion["labels"] = np.asarray(anotacion["labels"], dtype=np.int64)
    anotacion["instances"] = np.asarray(anotacion["instances"], dtype=np.int64)
    return anotacion


def dientes_presentes(labels):
    """Números FDI que aparecen en el escaneo, sin la encía, ordenados."""
    return sorted(int(x) for x in np.unique(labels) if x != 0)


def dientes_ausentes(presentes, arcada):
    """Números FDI de la arcada completa que no aparecen en el escaneo."""
    return [d for d in FDI_POR_ARCADA[arcada] if d not in set(presentes)]


def listar_escaneos(raiz):
    """Devuelve las rutas a los JSON de todos los escaneos bajo raiz.

    Espera la estructura de Teeth3DS: raiz/<arcada>/<id>/<id>_<arcada>.json.
    """
    return sorted(Path(raiz).glob("*/*/*.json"))


def cargar_data_pyg(ruta_obj, ruta_json):
    """Carga un escaneo como torch_geometric.data.Data.

    pos:  coordenadas de los vértices (N, 3)
    face: triángulos de la malla (3, F), el formato que espera PyG
    y:    etiqueta FDI de cada vértice (N,)
    """
    import torch
    import trimesh
    from torch_geometric.data import Data

    # process=False es imprescindible: si trimesh fusiona o reordena
    # vértices, las etiquetas del JSON dejan de corresponder a su vértice.
    malla = trimesh.load(ruta_obj, process=False)
    anotacion = leer_anotacion(ruta_json)

    if len(anotacion["labels"]) != len(malla.vertices):
        raise ValueError(
            f"{ruta_json}: {len(anotacion['labels'])} etiquetas para "
            f"{len(malla.vertices)} vértices"
        )

    return Data(
        pos=torch.tensor(malla.vertices, dtype=torch.float),
        face=torch.tensor(malla.faces, dtype=torch.long).t().contiguous(),
        y=torch.from_numpy(anotacion["labels"]),
    )
