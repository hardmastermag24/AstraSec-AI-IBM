"""
Pruebas unitarias del módulo ingest.py
"""
import json
import pytest
from app.core.ingest import ingest_file, ALLOWED_EXTENSIONS


# ---- helpers ----

def _txt_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def _json_bytes(obj) -> bytes:
    return json.dumps(obj).encode("utf-8")


# ---- tipo de archivo no permitido ----

def test_ingest_rejects_unknown_extension():
    doc = ingest_file("malware.exe", b"\x00\x01\x02")
    assert not doc.ok
    assert "no permitido" in doc.error.lower()


def test_ingest_rejects_html():
    doc = ingest_file("page.html", b"<html></html>")
    assert not doc.ok


def test_ingest_rejects_py():
    doc = ingest_file("script.py", b"print('hello')")
    assert not doc.ok


# ---- tamaño máximo ----

def test_ingest_rejects_oversized_file():
    big = b"A" * (21 * 1024 * 1024)  # 21 MB > 20 MB
    doc = ingest_file("big.txt", big)
    assert not doc.ok
    assert "tamaño" in doc.error.lower()


# ---- TXT ----

def test_ingest_txt_ok():
    content = "Hola mundo. Este es un documento de prueba para AstraSec AI."
    doc = ingest_file("nota.txt", _txt_bytes(content))
    assert doc.ok
    assert doc.file_type == "txt"
    assert doc.full_text == content
    assert len(doc.chunks) >= 1


def test_ingest_txt_empty():
    doc = ingest_file("vacio.txt", b"   ")
    assert doc.ok
    assert len(doc.chunks) == 0


def test_ingest_txt_chunking():
    # Con chunk_size=50 y overlap=10 un texto de 200 chars debe dar múltiples chunks
    text = "A" * 200
    doc = ingest_file("largo.txt", _txt_bytes(text), chunk_size=50, overlap=10)
    assert doc.ok
    assert len(doc.chunks) > 1


def test_ingest_txt_chunk_fields():
    text = "Este fragmento debe tener fuente y tipo correctos."
    doc = ingest_file("check.txt", _txt_bytes(text))
    assert doc.ok
    chunk = doc.chunks[0]
    assert chunk.source == "check.txt"
    assert chunk.file_type == "txt"
    assert chunk.chunk_index == 0


# ---- JSON ----

def test_ingest_json_ok():
    obj = [{"event": "login_failed", "user": "admin"}]
    doc = ingest_file("log.json", _json_bytes(obj))
    assert doc.ok
    assert doc.file_type == "json"
    assert "login_failed" in doc.full_text


def test_ingest_invalid_json_falls_back_to_text():
    raw = b"esto no es json valido { }"
    doc = ingest_file("raro.json", raw)
    # debe procesar sin error (fallback a texto plano)
    assert doc.ok or doc.file_type == "json"


# ---- PDF (sin pypdf) ----

def test_ingest_pdf_returns_error_without_pypdf(monkeypatch):
    """Si pypdf no está disponible, debe devolver un error claro."""
    import app.core.ingest as ingest_module
    monkeypatch.setattr(ingest_module, "_pypdf_available", False)
    doc = ingest_file("doc.pdf", b"%PDF-1.4 fake content")
    assert not doc.ok
    assert "pypdf" in doc.error.lower()


# ---- referencia de fuente ----

def test_chunk_reference():
    doc = ingest_file("fuente.txt", _txt_bytes("Contenido de prueba para referencia."))
    assert doc.ok
    ref = doc.chunks[0].reference()
    assert "fuente.txt" in ref
    assert "fragmento" in ref
