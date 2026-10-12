"""Pruebas de src/teeth3ds.py con datos sintéticos (Teeth3DS no se versiona)."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teeth3ds import (  # noqa: E402
    FDI_INFERIOR,
    FDI_SUPERIOR,
    cargar_data_pyg,
    dientes_ausentes,
    dientes_presentes,
    es_tercer_molar,
)


def test_arcadas_completas_tienen_16_dientes():
    assert len(FDI_SUPERIOR) == 16
    assert len(FDI_INFERIOR) == 16
    assert FDI_SUPERIOR[0] == 11 and FDI_SUPERIOR[-1] == 28
    assert FDI_INFERIOR[0] == 31 and FDI_INFERIOR[-1] == 48


def test_dientes_presentes_ignora_encia_y_repeticiones():
    labels = np.array([0, 0, 11, 11, 21, 0, 18])
    assert dientes_presentes(labels) == [11, 18, 21]


def test_dientes_ausentes():
    presentes = [d for d in FDI_INFERIOR if d not in (38, 48, 36)]
    assert dientes_ausentes(presentes, "lower") == [36, 38, 48]


def test_es_tercer_molar():
    assert es_tercer_molar(18) and es_tercer_molar(48)
    assert not es_tercer_molar(17)


def _escribir_escaneo(carpeta, labels):
    # Malla mínima: un tetraedro de 4 vértices y 4 caras.
    obj = carpeta / "X_lower.obj"
    obj.write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
        "f 1 2 3\nf 1 2 4\nf 1 3 4\nf 2 3 4\n"
    )
    anotacion = carpeta / "X_lower.json"
    anotacion.write_text(json.dumps({
        "id_patient": "X", "jaw": "lower",
        "labels": labels, "instances": [1 if x else 0 for x in labels],
    }))
    return obj, anotacion


def test_cargar_data_pyg(tmp_path):
    obj, anotacion = _escribir_escaneo(tmp_path, [0, 31, 31, 0])
    data = cargar_data_pyg(obj, anotacion)
    assert data.pos.shape == (4, 3)
    assert data.face.shape == (3, 4)
    assert data.y.tolist() == [0, 31, 31, 0]


def test_cargar_data_pyg_rechaza_etiquetas_descuadradas(tmp_path):
    obj, anotacion = _escribir_escaneo(tmp_path, [0, 31, 31])
    with pytest.raises(ValueError):
        cargar_data_pyg(obj, anotacion)
