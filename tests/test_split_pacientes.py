"""Pruebas de la división estratificada por paciente con datos sintéticos."""
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from split_pacientes import dividir_estratificado, estrato  # noqa: E402

def crear_pacientes(n = 900):
    """Crea pacientes ficticios con la distribución de ausencias de Teeth3DS."""
    pacientes = [f"P{i:04d}" for i in range(n)]

    ausencias = {}

    for i, paciente in enumerate(pacientes):
        if i < 449: ausencias[paciente] = 0
        elif i < 559: ausencias[paciente] = 1
        else: ausencias[paciente] = 2

    estratos = {p: estrato(ausencias[p]) for p in pacientes}

    return pacientes, estratos

def crear_splits(n = 900, semilla = 42):
    """Genera train, val y test con las proporciones del proyecto."""
    pacientes, estratos = crear_pacientes(n)

    desarrollo, test = dividir_estratificado(pacientes, estratos, 0.8, semilla)
    train, val = dividir_estratificado(desarrollo, estratos, 0.8, semilla + 1)

    return train, val, test

def test_pacientes_no_se_repiten():
    """Ningún paciente puede aparecer en dos particiones."""
    train, val, test = crear_splits()

    assert set(train).isdisjoint(val)
    assert set(train).isdisjoint(test)
    assert set(val).isdisjoint(test)

def test_todos_los_pacientes_estan_incluidos():
    """La unión de las particiones contiene todos los pacientes."""
    pacientes, _ = crear_pacientes()
    train, val, test = crear_splits()

    assert set(train) | set(val) | set(test) == set(pacientes)
    assert len(train) + len(val) + len(test) == len(pacientes)

def test_misma_semilla_mismo_resultado():
    """Una misma semilla debe producir exactamente la misma división."""
    resultado_1 = crear_splits(semilla = 42)
    resultado_2 = crear_splits(semilla = 42)

    assert resultado_1 == resultado_2

def test_distintas_semillas_distintos_resultados():
    """Semillas diferentes deben producir divisiones diferentes."""
    resultado_1 = crear_splits(semilla = 42)
    resultado_2 = crear_splits(semilla = 43)

    assert resultado_1 != resultado_2

def test_distribucion_pacientes():
    """Comprueba la distribución real de ausencias de Teeth3DS."""
    _, estratos = crear_pacientes()

    conteo = Counter(estratos.values())

    assert conteo["0"] == 449
    assert conteo["1"] == 110
    assert conteo["2+"] == 341

def test_redondeo_tamanos():
    """Comprueba los tamaños cuando el redondeo cambia el resultado."""
    train, val, test = crear_splits(n = 900)

    # Sin el ajuste del mayor resto, train tendría 575 pacientes.
    assert len(train) == 576
    assert len(val) == 144
    assert len(test) == 180

    # Con 899 pacientes se comprueba el redondeo del tamaño total.
    train, val, test = crear_splits(n = 899)

    assert len(train) == 575
    assert len(val) == 144
    assert len(test) == 180

def test_estratificacion():
    """Las proporciones de los estratos deben mantenerse aproximadamente."""
    pacientes, estratos = crear_pacientes()
    train, val, test = crear_splits()

    for grupo in (train, val, test):
        for e in ("0", "1", "2+"):
            proporcion_original = sum(estratos[p] == e for p in pacientes) / len(pacientes)
            proporcion_grupo = sum(estratos[p] == e for p in grupo) / len(grupo)

            assert abs(proporcion_original - proporcion_grupo) < 0.02