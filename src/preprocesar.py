"""Preprocesa Teeth3DS para la red: FPS, normalización y etiquetas de 33 clases.

Uso: 
    python src/preprocesar.py data --salida data/procesado --puntos 16000

Cada escaneo se guarda como un archivo .pt con:
    pos:        coordenadas normalizadas de los puntos muestreados (M, 3).
    y:          etiquetas de clase de los puntos muestreados (M,), entre 0 y 32.
    indices:    índices de los puntos seleccionados en la malla original (M,).
    M = min(--puntos, número de vértices de la malla).
    centroide:  centroide de todos los vértices originales (3,).
    escala:     factor utilizado para normalizar las coordenadas.
    id:         identificador del escaneo (<paciente>_<arcada>)

El preprocesado se calcula una sola vez para evitar repetir el FPS durante cada época de entrenamiento.

Las 33 clases corresponden a la encía (0) y los 32 dientes permanentes (1-32).
Se utiliza el mismo mapa de clases para ambas arcadas porque los identificadores FDI
son únicos: 11-28 corresponden a la superior y 31-48 a la inferior.
"""

import argparse
import time
from pathlib import Path

import torch
import trimesh
from torch_geometric.nn import fps

from teeth3ds import (FDI_INFERIOR, FDI_SUPERIOR, leer_anotacion, listar_escaneos)


# Conversión de etiquetas FDI a clases consecutivas
FDI_A_CLASE = {0: 0}
for clase, fdi in enumerate(FDI_SUPERIOR + FDI_INFERIOR, start = 1): FDI_A_CLASE[fdi] = clase

TABLA_CLASES = torch.full((49,), -1, dtype = torch.long)
for fdi, clase in FDI_A_CLASE.items(): TABLA_CLASES[fdi] = clase


def tiene_fdi_repetido(labels, instances):
    """True si un número FDI aparece en más de una instancia dental."""
    if len(labels) != len(instances): raise ValueError("Las etiquetas y las instancias tienen distinta longitud")

    for fdi in set(labels.tolist()) - {0}:
        instancias = set(instances[labels == fdi].tolist())

        if len(instancias) > 1: return True

    return False


def normalizar(pos):
    """Centra en el origen y escala a la esfera unidad.
    
    El centroide y la escala se calculan utilizando los vértices, independientemente
    del número de puntos que muestreen.
    
    Devuelve:
        pos_normalizado: coordenadas centradas y escaladas.
        centroide: media de las coordenadas originales.
        escala: máxima distancia al centroide.
    """
    centroide = pos.mean(dim = 0)

    pos_centrado = pos - centroide

    distancias = torch.linalg.vector_norm(pos_centrado, dim = 1)
    escala = distancias.max()

    if escala.item() == 0: raise ValueError("No se puede normalizar una malla sin extensión espacial")

    pos_normalizado = pos_centrado / escala

    return pos_normalizado, centroide, escala


def procesar_escaneo(ruta_json, n_puntos, dispositivo):
    """Preprocesa un escaneo y devuelve sus datos o None si se descarta."""
    ruta_json = Path(ruta_json)
    ruta_obj = ruta_json.with_suffix(".obj")

    # 1. Leer las anotaciones.
    anotacion = leer_anotacion(ruta_json)

    labels = anotacion["labels"]
    instances = anotacion["instances"]

    # 2. Descartar escaneos con etiquetas FDI duplicadas.
    if tiene_fdi_repetido(labels, instances): return None

    # 3. Cargar la malla sin modificar el orden de sus vértices.
    malla = trimesh.load(ruta_obj, process = False)

    if not isinstance(malla, trimesh.Trimesh): raise ValueError(f"No se ha cargado una malla válida: {ruta_obj}")

    pos = torch.as_tensor(
        malla.vertices.copy(), 
        dtype = torch.float32
    )

    etiquetas = torch.as_tensor(labels, dtype = torch.long)

    # 4. Comprobar que vértices y etiquetas coinciden.
    n_vertices = pos.size(0)

    if n_vertices != len(etiquetas):
        raise ValueError(
            f"{ruta_json}: {n_vertices} vértices y "
            f"{len(etiquetas)} etiquetas"
        )

    # 5. Comprobar que las etiquetas FDI son válidas.
    etiquetas_presentes = set(etiquetas.unique().tolist())
    etiquetas_invalidas = etiquetas_presentes - set(FDI_A_CLASE)

    if etiquetas_invalidas:
        raise ValueError(
            f"{ruta_json}: etiquetas FDI desconocidas: "
            f"{sorted(etiquetas_invalidas)}"
        )

    # 6. Normalizar utilizando todos los vértices originales.
    pos_normalizado, centroide, escala = normalizar(pos)

    # 7. Aplicar FPS sobre las coordenadas normalizadas.
    # Si la malla tiene n_puntos vértices o menos (9 de los 1.800 escaneos),
    # se usan todos sin muestrear: PointNet++ en PyG admite nubes de distinto tamaño.
    # random_start = False permite obtener resultados reproducibles.
    if n_vertices <= n_puntos: indices = torch.arange(n_vertices, dtype = torch.long)
    else: 
        pos_gpu = pos_normalizado.to(dispositivo)

        # El FPS calcula el número de muestras mediante redondeo hacia arriba.
        # Restar 0.5 evita que los errores de coma flotante produzcan ocasionalmente un punto adicional.
        proporcion = (n_puntos - 0.5) / n_vertices

        indices = fps(
            pos_gpu, 
            ratio = proporcion,
            random_start = False
        ).cpu().long()

        if len(indices) != n_puntos:
            raise RuntimeError(
                f"{ruta_json}: FPS devolvió {len(indices)} puntos "
                f"en lugar de {n_puntos}"
            )

    # 8. Seleccionar puntos y etiquetas con los mismos índices.
    pos_muestreado = pos_normalizado[indices]
    etiquetas_muestreadas = etiquetas[indices]

    # 9. Convertir etiquetas FDI a clases consecutivas de 0 a 32.
    y = TABLA_CLASES[etiquetas_muestreadas]

    if y.min() < 0: raise RuntimeError(f"{ruta_json}: hay puntos sin clase asignada")

    # 10. Identificador del escaneo.
    identificador = (f"{anotacion['id_patient']}_{anotacion['jaw']}")

    # 11. Devuelve todo en CPU para guardarlo.
    return {
        "pos":       pos_muestreado.cpu(),
        "y":         y.cpu(),
        "indices":   indices.cpu(),
        "centroide": centroide.cpu(),
        "escala":    escala.cpu(),
        "id":        identificador
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description = __doc__.splitlines()[0]
    )

    parser.add_argument(
        "raiz", type = Path, help = "carpeta raíz de Teeth3DS"
    )

    parser.add_argument(
        "--salida", type = Path, default = Path("data/procesado"), help = "directorio donde guardar los archivos .pt"
    )

    parser.add_argument(
        "--puntos", type = int, default = 16000, help = "número de puntos seleccionados mediante FPS"
    )

    parser.add_argument(
        "--limite", type = int, default = None, help = "número máximo de escaneos que procesar (para pruebas)"
    )

    args = parser.parse_args() 

    if args.puntos <= 0: parser.error("--puntos debe ser un entero positivo")

    args.salida.mkdir(parents = True, exist_ok = True)

    # Utilizar la GPU si está disponible.
    dispositivo = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"Dispositivo: {dispositivo}")
    print(f"Puntos por escaneo: {args.puntos}")

    # Localizar los escaneos.
    escaneos = listar_escaneos(args.raiz)

    if args.limite is not None: escaneos = escaneos[:args.limite]

    print(f"Escaneos encontrados: {len(escaneos)}")

    # Recuperar descartes anteriores para permitir reanudar el proceso.
    ruta_descartados = args.salida / "descartados.txt"

    descartados = set()

    if ruta_descartados.exists(): 
        descartados = set(ruta_descartados.read_text(encoding = "utf-8").splitlines())

    procesados, existentes = 0, 0

    inicio_total = time.perf_counter()

    for i, ruta_json in enumerate(escaneos, start = 1):
        identificador = ruta_json.stem
        ruta_salida = args.salida / f"{identificador}.pt"

        # No repetir el FPS si el archivo ya existe.
        if ruta_salida.exists():
            existentes += 1

            print(f"[{i}/{len(escaneos)}] Ya existe: {identificador}")

            continue

        inicio = time.perf_counter()

        resultado = procesar_escaneo(ruta_json, args.puntos, dispositivo)

        if resultado is None:
            descartados.add(identificador)

            print(
                f"[{i}/{len(escaneos)}] DESCARTADO: "
                f"{identificador} (FDI duplicado)"
            )

            continue

        # Si una anotación se ha corregido, deja de estar descartada.
        descartados.discard(identificador)

        if resultado["id"] != identificador: raise ValueError(f"Identificador incorrecto: {resultado['id']} != {identificador}")

        # Guardar el resultado.
        torch.save(resultado, ruta_salida)

        procesados += 1

        if dispositivo.type == "cuda": torch.cuda.synchronize()

        duracion = time.perf_counter() - inicio

        print(
            f"[{i}/{len(escaneos)}] {identificador} "
            f"{len(resultado['pos'])} puntos, {duracion:.2f} s"
        )

    # Guardar identificadores de escaneos descartados.
    ruta_descartados.write_text(
        "".join(f"{identificador}\n" for identificador in sorted(descartados)),
        encoding = "utf-8"
    )

    duracion_total = time.perf_counter() - inicio_total


    print("\n=== RESUMEN DEL PREPROCESADO ===")
    print(f"Procesados nuevos: {procesados}")
    print(f"Ya existentes: {existentes}")
    print(f"Descartados registrados: {len(descartados)}")
    print(f"Tiempo total: {duracion_total:.2f} s")
    print(f"Directorio de salida: {args.salida}")

    if descartados: 
        print("\nEscaneos descartados:")

        for identificador in sorted(descartados):
            print(f"  {identificador}")

    print(f"\nLista de descartados: {ruta_descartados}")