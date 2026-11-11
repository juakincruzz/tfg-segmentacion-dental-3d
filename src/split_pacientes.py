"""Genera la división de Teeth3DS por paciente, estratificada por ausencias.

Uso:
    python src/split_pacientes.py data --salida data/splits/propio --semilla ...

Divide 80/20 entre desarrollo y prueba y, después, 80/20 entre entrenamiento (80 % del desarrollo)
y validación (20 % del desarrollo).

Resultado final: 64 % entrenamiento, 16 % validación y 20 % prueba.
"""

import argparse
import random
from pathlib import Path
from collections import Counter, defaultdict

from teeth3ds import (dientes_ausentes,
                      dientes_presentes,
                      es_tercer_molar,
                      leer_anotacion,
                      listar_escaneos
                    )


def ausencias_por_paciente(raiz):
    """Devuelve {id_paciente: número de ausencias sin terceros molares}.
    
    Suma las ausencias de sus dos arcadas.
    """
    ausencias = defaultdict(int)
    arcadas = defaultdict(set)
    rutas = listar_escaneos(raiz)

    if not rutas:
        raise FileNotFoundError(f"No se encontraron anotaciones JSON en {raiz}")

    for ruta in rutas:
        anotacion = leer_anotacion(ruta)
        paciente = str(anotacion['id_patient'])
        arcada = anotacion["jaw"]

        if arcada not in ("upper", "lower"): raise ValueError(f"Arcada desconocida en {ruta}: {arcada!r}")
        if arcada in arcadas[paciente]: raise ValueError(f"Arcada {arcada} duplicada para {paciente}")
        if ruta.stem != f"{paciente}_{arcada}": raise ValueError(
            f"Nombre de escaneo inesperado: {ruta.stem}; "
            f"se esperaba {paciente}_{arcada}"
        )

        presentes = dientes_presentes(anotacion["labels"])
        ausentes = dientes_ausentes(presentes, arcada)
        ausencias[paciente] += sum(not es_tercer_molar(d) for d in ausentes)
        arcadas[paciente].add(arcada)

    incompletos = sorted(
        paciente for paciente, jaws in arcadas.items()
        if jaws != {"upper", "lower"}
    )

    if incompletos:
        raise ValueError(
            f"Hay {len(incompletos)} pacientes sin las dos arcadas; "
            f"ejemplos: {incompletos[:5]}. "
            "Revisa las anotaciones antes de generar los splits."
        )

    return dict(ausencias)


def estrato(n_ausencias):
    """ Devuelve el estrato del paciente: '0', '1' o '2+'."""
    if n_ausencias < 0: raise ValueError("El número de ausencias no puede ser negativo")
    if n_ausencias == 0: return "0"
    if n_ausencias == 1: return "1"

    return "2+"


def dividir_estratificado(pacientes, estratos, proporcion, semilla):
    """Divide pacientes manteniendo, aproximadamente, la proporción por estrato.
    
    ``proporcion`` es la fracción asignada al primer grupo.
    Ajusta los redondeos para obtener el tamaño total previsto.
    """
    if not 0 <= proporcion <= 1: raise ValueError("La proporción debe estar entre 0 y 1")
    if len(pacientes) != len(set(pacientes)): raise ValueError("Hay identificadores de paciente repetidos")

    por_estrato = defaultdict(list)

    for paciente in pacientes: por_estrato[estratos[paciente]].append(paciente)

    generador = random.Random(semilla)

    for grupo in por_estrato.values():
        grupo.sort()
        generador.shuffle(grupo)

    # El mayor resto asigna los redondeos pendientes a los estratos
    # con mayor parte decimal, conservando el tamaño exacto del grupo A.
    cuotas = {e: len(grupo) * proporcion for e, grupo in por_estrato.items()}
    cortes = {e: int(cuota) for e, cuota in cuotas.items()}
    pendientes = round(len(pacientes) * proporcion) - sum(cortes.values())
    orden = sorted(cuotas, key = lambda e: cuotas[e] - cortes[e], reverse = True)

    for e in orden[:pendientes]: cortes[e] += 1

    grupo_a, grupo_b = [], []

    for e in sorted(por_estrato):
        grupo = por_estrato[e]
        grupo_a.extend(grupo[:cortes[e]])
        grupo_b.extend(grupo[cortes[e]:])

    return sorted(grupo_a), sorted(grupo_b)


def guardar(pacientes, ruta):
    """Escribe un escaneo por línea: <id>_upper e <id>_lower."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents = True, exist_ok = True)
    
    with ruta.open("w", encoding = "utf-8") as fichero:
        for paciente in sorted(pacientes):
            fichero.write(f"{paciente}_upper\n")
            fichero.write(f"{paciente}_lower\n")


def resumen(grupos, ausencias):
    """Imprime el número de pacientes y el porcentaje de cada estrato."""
    print(f"Total: {len(ausencias)} pacientes ({2 * len(ausencias)} escaneos)")

    for nombre, pacientes in grupos.items():
        conteo = Counter(estrato(ausencias[p]) for p in pacientes)
        n = len(pacientes)
        detalle = ", ".join(f"{e}: {conteo[e]} ({conteo[e] / n:.1%})" 
                            for e in ("0", "1", "2+")
                            ) if n else "sin pacientes"

        print(f"{nombre}: {n} pacientes, {2 * n} escaneos | {detalle}")
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = __doc__.splitlines()[0])
    parser.add_argument("raiz", type = Path, help = "carpeta con upper/ y lower/")
    parser.add_argument("--salida", type = Path, required = True, help = "directorio donde crear train.txt, val.txt y test.txt")
    parser.add_argument("--semilla", type = int, default = 42, help = "semilla (por defecto 42)")

    args = parser.parse_args()

    ausencias = ausencias_por_paciente(args.raiz)
    pacientes = sorted(ausencias)
    estratos = {p: estrato(ausencias[p]) for p in pacientes}

    desarrollo, test = dividir_estratificado(pacientes, estratos, 0.8, args.semilla)
    train, val = dividir_estratificado(desarrollo, estratos, 0.8, args.semilla + 1)

    grupos = {"train": train, "val": val, "test": test}
    assert sum(map(len, grupos.values())) == len(pacientes)
    assert all(set(grupos[a]).isdisjoint(grupos[b]) for a, b in (("train", "val"), ("train", "test"), ("val", "test"))
                ), "Un paciente aparece en más de una partición"
    
    for nombre, grupo in grupos.items(): guardar(grupo, args.salida / f"{nombre}.txt")

    resumen(grupos, ausencias)

    print(f"Ficheros guardados en: {args.salida}")