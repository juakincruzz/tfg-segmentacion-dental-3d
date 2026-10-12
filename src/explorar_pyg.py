"""Carga un escaneo de Teeth3DS en PyTorch Geometric y muestra su estructura.

Uso:
    python src/explorar_pyg.py data/lower/OEIWQQMQ
"""

import sys
from pathlib import Path

import torch
import torch_geometric.transforms as T

from teeth3ds import cargar_data_pyg

carpeta = Path(sys.argv[1])
ruta_obj = next(carpeta.glob("*.obj"))
ruta_json = next(carpeta.glob("*.json"))

data = cargar_data_pyg(ruta_obj, ruta_json)
print("Escaneo como malla:")
print(" ", data)
print(f"  vértices: {data.num_nodes}, triángulos: {data.face.size(1)}")
print(f"  etiquetas FDI presentes: {torch.unique(data.y).tolist()}")
print(f"  vértices de encía: {(data.y == 0).float().mean():.1%}")

# Las GNN trabajan con aristas, no con caras: FaceToEdge convierte cada
# triángulo en sus tres aristas y genera edge_index (2, E).
grafo = T.FaceToEdge(remove_faces=False)(data.clone())
print("\nEscaneo como grafo:")
print(" ", grafo)
print(f"  aristas (dirigidas): {grafo.num_edges}")
print(f"  grado medio: {grafo.num_edges / grafo.num_nodes:.2f}")

# Alternativa sin la malla: nube de puntos con k vecinos más cercanos.
# KNNGraph necesita torch_cluster; si no está instalado, se indica.
try:
    nube = T.KNNGraph(k=16)(data.clone())
    print("\nEscaneo como nube de puntos con k=16 vecinos:")
    print(" ", nube)
except ImportError as e:
    print(f"\nKNNGraph no disponible ({e}).")

grafo.validate(raise_on_error=True)
print("\nLa estructura del grafo es válida.")
