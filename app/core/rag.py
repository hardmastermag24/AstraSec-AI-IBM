"""
AstraSec AI — Recuperación de contexto relevante (RAG simplificado).

En el MVP se usa búsqueda textual por frecuencia de términos.
No se requieren librerías vectoriales externas.

Responsabilidades:
- Recibir una consulta en lenguaje natural.
- Devolver los fragmentos más relevantes con referencia de fuente.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from app.core.ingest import DocumentChunk


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    score: float

    def reference(self) -> str:
        return self.chunk.reference()


def _tokenize(text: str) -> List[str]:
    """Convierte texto a lista de tokens en minúsculas."""
    return re.findall(r"(?:\d{1,3}\.){3}\d{1,3}|[a-z]+(?:-[a-z0-9]+)+|\b\w+\b", text.lower())


def _score_chunk(query_tokens: List[str], chunk_text: str) -> float:
    """
    Puntuación simple: proporción de tokens de la consulta que aparecen en el fragmento.
    Valor entre 0.0 y 1.0.
    """
    if not query_tokens:
        return 0.0
    chunk_tokens = set(_tokenize(chunk_text))
    matches = sum(1 for t in query_tokens if t in chunk_tokens)
    return matches / len(query_tokens)


def retrieve(
    query: str,
    all_chunks: List[DocumentChunk],
    top_k: int = 5,
    min_score: float = 0.0,
) -> List[RetrievedChunk]:
    """
    Recupera los fragmentos más relevantes para la consulta.

    Args:
        query: Consulta en lenguaje natural del usuario.
        all_chunks: Lista de todos los fragmentos disponibles en la sesión.
        top_k: Número máximo de fragmentos a devolver.
        min_score: Puntuación mínima para incluir un fragmento.

    Returns:
        Lista de RetrievedChunk ordenados por relevancia descendente.
    """
    if not all_chunks:
        return []

    query_tokens = _tokenize(query)

    scored = [
        RetrievedChunk(chunk=c, score=_score_chunk(query_tokens, c.text))
        for c in all_chunks
    ]
    scored.sort(key=lambda r: r.score, reverse=True)

    results = [r for r in scored if r.score > min_score]
    return results[:top_k]


def format_context_for_prompt(retrieved: List[RetrievedChunk]) -> str:
    """
    Formatea los fragmentos recuperados como contexto para el prompt del agente.
    Cada fragmento incluye la referencia de fuente.
    """
    if not retrieved:
        return "(No se encontraron fragmentos relevantes para esta consulta.)"

    parts = []
    for i, r in enumerate(retrieved, 1):
        parts.append(
            f"[Fuente {i}: {r.reference()}]\n{r.chunk.text.strip()}"
        )
    return "\n\n---\n\n".join(parts)
