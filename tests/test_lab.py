"""
Pruebas unitarias del módulo lab.py
"""
import pytest
from app.core.lab import create_laboratory, Laboratory


def test_create_laboratory_ok():
    lab = create_laboratory("Lab-Test", "Laboratorio de prueba")
    assert lab.name == "Lab-Test"
    assert lab.description == "Laboratorio de prueba"
    assert lab.analyst == ""
    assert lab.scope == ""
    assert lab.created_at  # no vacío


def test_create_laboratory_with_optional_fields():
    lab = create_laboratory("Lab-A", "Desc", analyst="Analista1", scope="192.168.0.0/24")
    assert lab.analyst == "Analista1"
    assert lab.scope == "192.168.0.0/24"


def test_create_laboratory_strips_whitespace():
    lab = create_laboratory("  Lab-B  ", "  Desc B  ")
    assert lab.name == "Lab-B"
    assert lab.description == "Desc B"


def test_create_laboratory_empty_name_raises():
    with pytest.raises(ValueError, match="nombre"):
        create_laboratory("", "Descripción válida")


def test_create_laboratory_empty_description_raises():
    with pytest.raises(ValueError, match="descripción"):
        create_laboratory("Lab-C", "")


def test_create_laboratory_whitespace_name_raises():
    with pytest.raises(ValueError, match="nombre"):
        create_laboratory("   ", "Descripción")


def test_laboratory_to_dict():
    lab = create_laboratory("Lab-D", "Descripción D")
    d = lab.to_dict()
    assert d["name"] == "Lab-D"
    assert d["description"] == "Descripción D"
    assert "created_at" in d


def test_laboratory_to_json():
    lab = create_laboratory("Lab-E", "Descripción E")
    j = lab.to_json()
    assert "Lab-E" in j
    assert "Descripción E" in j


def test_laboratory_from_dict():
    data = {
        "name": "Lab-F",
        "description": "Desc F",
        "created_at": "2024-01-01T00:00:00",
        "analyst": "Ana",
        "scope": "10.0.0.0/8",
    }
    lab = Laboratory.from_dict(data)
    assert lab.name == "Lab-F"
    assert lab.analyst == "Ana"
    assert lab.scope == "10.0.0.0/8"
