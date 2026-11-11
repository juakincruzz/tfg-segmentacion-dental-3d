"""Genera train/val/test a partir del split oficial de 3DTeethSeg22.

Uso:
    python src/split_oficial.py data --salida data/splits/oficial

Utiliza los ficheros de public-training-set-1.txt y public-training-set-2.txt como conjunto de desarrollo (600 pacientes),
y private-testing-set.txt como conjunto de prueba (300 pacientes).

El desarrollo se divide en entrenamiento (80 %) y validación (20 %), estratificando por el número de ausencias dentales
sin terceros molares.
"""

import argparse
from collections import defaultdict
from pathlib import Path

from split_pacientes import (ausencias_por_paciente, dividir_estratificado, estrato, guardar, resumen)

CARPETA_OFICIAL = Path("splits/3DTeethSeg22")

FICHEROS_ENTRENAMIENTO = ("public-training-set-1.txt", "public-training-set-2.txt")

FICHERO_PRUEBA = "private-testing-set.txt"


def leer_pacientes(*rutas):
    """Lee los pacientes y comprueba que tengan ambas arcadas.
    
    Cada línea contiene un identificador con el formato: 
    <id_paciente>_upper o <id_paciente>_lower.

    Devuelve un conjunto de identificadores de paciente.
    """
    arcadas = defaultdict(set)

    for ruta in rutas:
        ruta = Path(ruta)

        with ruta.open("r", encoding = "utf-8") as fichero:
            for numero_linea, linea in enumerate(fichero, start = 1):
                escaneo = linea.strip()

                if not escaneo: continue

                if "_" not in escaneo:
                    raise ValueError(
                        f"{ruta}:{numero_linea}: "
                        f"identificador incorrecto: {escaneo}"
                    )

                paciente, arcada = escaneo.rsplit("_", 1)

                if arcada not in ("upper", "lower"): raise ValueError(f"{ruta}:{numero_linea}: arcada desconocida: {escaneo}")
                if arcada in arcadas[paciente]: raise ValueError(f"Escaneo duplicado: {escaneo}")

                arcadas[paciente].add(arcada)

    incompletos = sorted(paciente for paciente, jaws in arcadas.items() if jaws != {"upper", "lower"})

    if incompletos: 
        raise ValueError(
            f"Hay {len(incompletos)} pacientes sin ambas arcadas. "
            f"Ejemplos: {incompletos[:5]}"
        )

    return set(arcadas)


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(
        description = __doc__.splitlines()[0]
    )

    parser.add_argument(
        "raiz", type = Path, help = "carpeta raíz de Teeth3DS"
    )

    parser.add_argument(
        "--salida", type = Path, required = True, help = "directorio donde guardar train.txt, val.txt y test.txt"
    )

    parser.add_argument(
        "--semilla", type = int, default = 42, help = "semilla aleatoria (por defecto: 42)"
    )

    args = parser.parse_args()

    # 1. Calcular las ausencias de cada paciente.
    ausencias = ausencias_por_paciente(args.raiz)

    # 2. Localizar los ficheros oficiales del reto.
    carpeta = args.raiz / CARPETA_OFICIAL

    rutas_entrenamiento = [carpeta / nombre for nombre in FICHEROS_ENTRENAMIENTO]

    ruta_prueba = carpeta / FICHERO_PRUEBA

    # 3. Leer los pacientes del entrenamiento y la prueba oficiales.
    entrenamiento_reto = leer_pacientes(*rutas_entrenamiento)
    test = leer_pacientes(ruta_prueba)

    # 4. Comprobar que no haya pacientes compartidos.
    solapados = entrenamiento_reto & test

    if solapados:
        raise ValueError(
            f"Hay {len(solapados)} pacientes en entrenamiento "
            f"y prueba. Ejemplos: {sorted(solapados)[:5]}"
        )

    # 5. Comprobar que aparecen todos los pacientes de Teeth3DS.
    pacientes_oficiales = entrenamiento_reto | test
    pacientes_datos = set(ausencias)

    faltantes = pacientes_datos - pacientes_oficiales
    desconocidos = pacientes_oficiales - pacientes_datos

    if faltantes or desconocidos:
        raise ValueError(
            f"El split oficial no coincide con los pacientes "
            f"de Teeth3DS.\n"
            f"Pacientes sin asignar: {len(faltantes)}.\n"
            f"Pacientes desconocidos: {len(desconocidos)}. "
        )

    # 6. Comprobar los tamaños oficiales.
    if len(entrenamiento_reto) != 600 or len(test) != 300:
        raise ValueError(
            "Tamaños inesperados en el split oficial: "
            f"{len(entrenamiento_reto)} entrenamiento, "
            f"{len(test)} prueba. "
        )

    # 7. Clasificar los pacientes por número de ausencias.
    estratos = {paciente: estrato(n_ausencias) for paciente, n_ausencias in ausencias.items()}

    # 8. Dividir el entrenamiento oficial en train y val (80/20).
    # La validación se estratifica igual que en el split propio.
    train, val = dividir_estratificado(sorted(entrenamiento_reto), estratos, 0.8, args.semilla)

    # 9. Reunir los tres conjuntos.
    grupos = {
        "train": train,
        "val": val,
        "test": sorted(test)
    }

    # 10. Comprobar los tamaños finales.
    if len(train) != 480 or len(val) != 120 or len(test) != 300:
        raise ValueError(
            "Tamaños inesperados después de dividir: "
            f"train = {len(train)}, val = {len(val)}, test = {len(test)}"
        )

    # 11. Comprobar que ningún paciente aparece en varios grupos.
    assert all(
        set(grupos[a]).isdisjoint(grupos[b])
        for a, b in (
            ("train", "val"),
            ("train", "test"),
            ("val", "test")
        )
    ), "Un paciente aparece en más de una partición"

    # 12. Guardar los ficheros con el mismo formato que el split propio.
    for nombre, pacientes in grupos.items(): guardar(pacientes, args.salida / f"{nombre}.txt")

    # 13. Mostrar el resumen.
    print("\n=== SPLIT OFICIAL 3DTeethSeg22 ===")
    print(f"Semilla: {args.semilla}")
    print("Validación estratificada por ausencias: sí\n")

    resumen(grupos, ausencias)

    print(f"\nFicheros guardados en: {args.salida}")