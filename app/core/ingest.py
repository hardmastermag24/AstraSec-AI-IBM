"""
AstraSec AI — Carga, validación y chunking de archivos.

Responsabilidades:
- Validar tipo y tamaño de archivos admitidos (PDF, TXT, JSON).
- Extraer texto plano de manera segura.
- Dividir el texto en fragmentos (chunks) para consulta.

RESTRICCIÓN DE SEGURIDAD:
El contenido de los archivos se trata únicamente como datos de texto.
Ningún fragmento de texto puede desencadenar acciones del sistema.
"""

from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass, field
from typing import List

# pypdf se importa de forma diferida para no fallar si no está instalado
_pypdf_available: bool | None = None


def _check_pypdf() -> bool:
    global _pypdf_available
    if _pypdf_available is None:
        try:
            import pypdf  # noqa: F401
            _pypdf_available = True
        except ImportError:
            _pypdf_available = False
    return _pypdf_available


ALLOWED_EXTENSIONS = {".pdf", ".txt", ".json"}
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@dataclass
class DocumentChunk:
    source: str          # nombre del archivo de origen
    chunk_index: int     # posición del fragmento en el documento
    text: str            # contenido del fragmento
    file_type: str       # "pdf", "txt", "json"

    def reference(self) -> str:
        return f"{self.source} · fragmento {self.chunk_index + 1}"


@dataclass
class IngestedDocument:
    filename: str
    file_type: str
    full_text: str
    chunks: List[DocumentChunk] = field(default_factory=list)
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error


def _extract_text_pdf(data: bytes) -> str:
    """Extrae texto de un PDF usando pypdf."""
    if not _check_pypdf():
        raise ImportError("pypdf no está instalado. Ejecuta: pip install pypdf")
    import pypdf  # noqa: PLC0415

    reader = pypdf.PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n\n".join(pages)


def _extract_text_txt(data: bytes) -> str:
    """Decodifica texto plano con fallback a latin-1."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


def _extract_text_json(data: bytes) -> str:
    """Convierte JSON a texto legible para el agente (dato, no código)."""
    try:
        obj = json.loads(data.decode("utf-8"))
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Si no es JSON válido, lo trata como texto plano
        return _extract_text_txt(data)


def _split_into_chunks(text: str, chunk_size: int, overlap: int, source: str, file_type: str) -> List[DocumentChunk]:
    """Divide el texto en fragmentos con solapamiento."""
    chunks: List[DocumentChunk] = []
    if not text.strip():
        return chunks
    step = max(1, chunk_size - overlap)
    idx = 0
    chunk_index = 0
    while idx < len(text):
        fragment = text[idx : idx + chunk_size]
        if fragment.strip():
            chunks.append(DocumentChunk(
                source=source,
                chunk_index=chunk_index,
                text=fragment,
                file_type=file_type,
            ))
            chunk_index += 1
        idx += step
    return chunks


def ingest_file(
    filename: str,
    data: bytes,
    chunk_size: int = 1500,
    overlap: int = 200,
) -> IngestedDocument:
    """
    Procesa un archivo cargado por el usuario.

    Args:
        filename: Nombre original del archivo.
        data: Contenido binario del archivo.
        chunk_size: Tamaño máximo de cada fragmento en caracteres.
        overlap: Caracteres de solapamiento entre fragmentos consecutivos.

    Returns:
        IngestedDocument con los fragmentos extraídos o con un campo error.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return IngestedDocument(
            filename=filename,
            file_type=ext.lstrip(".") or "desconocido",
            full_text="",
            error=f"Tipo de archivo no permitido: '{ext}'. Permitidos: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    if len(data) > MAX_FILE_SIZE_BYTES:
        return IngestedDocument(
            filename=filename,
            file_type=ext.lstrip("."),
            full_text="",
            error=f"El archivo supera el tamaño máximo permitido ({MAX_FILE_SIZE_MB} MB).",
        )

    file_type = ext.lstrip(".")

    try:
        if ext == ".pdf":
            full_text = _extract_text_pdf(data)
        elif ext == ".txt":
            full_text = _extract_text_txt(data)
        elif ext == ".json":
            full_text = _extract_text_json(data)
        else:
            full_text = ""
    except Exception as exc:  # noqa: BLE001
        return IngestedDocument(
            filename=filename,
            file_type=file_type,
            full_text="",
            error=f"Error al extraer texto: {exc}",
        )

    chunks = _split_into_chunks(full_text, chunk_size, overlap, source=filename, file_type=file_type)

    return IngestedDocument(
        filename=filename,
        file_type=file_type,
        full_text=full_text,
        chunks=chunks,
    )
