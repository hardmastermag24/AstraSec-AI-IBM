"""
Pruebas unitarias del módulo rag.py
"""
from app.core.rag import retrieve, format_context_for_prompt, _tokenize, _score_chunk
from app.core.ingest import DocumentChunk


# ---- helpers ----

def _make_chunk(text: str, source: str = "test.txt", idx: int = 0) -> DocumentChunk:
    return DocumentChunk(source=source, chunk_index=idx, text=text, file_type="txt")


# ---- tokenización ----

def test_tokenize_basic():
    tokens = _tokenize("Hola mundo")
    assert "hola" in tokens
    assert "mundo" in tokens


def test_tokenize_empty():
    assert _tokenize("") == []


def test_tokenize_ignores_punctuation():
    tokens = _tokenize("error: 404 not found!")
    assert "error" in tokens
    assert "404" in tokens
    assert "!" not in tokens


# ---- puntuación ----

def test_score_chunk_exact_match():
    score = _score_chunk(["login", "failed"], "login failed event detected")
    assert score == 1.0


def test_score_chunk_no_match():
    score = _score_chunk(["xyz123"], "absolutely unrelated content")
    assert score == 0.0


def test_score_chunk_partial_match():
    score = _score_chunk(["login", "success"], "login event detected")
    assert 0.0 < score < 1.0


def test_score_chunk_empty_query():
    score = _score_chunk([], "cualquier texto")
    assert score == 0.0


# ---- retrieve ----

def test_retrieve_empty_chunks():
    results = retrieve("cualquier consulta", [])
    assert results == []


def test_retrieve_returns_top_k():
    chunks = [
        _make_chunk("login failed admin ip 192.168.1.1", idx=0),
        _make_chunk("login failed root ip 192.168.1.1", idx=1),
        _make_chunk("firewall blocked outbound", idx=2),
        _make_chunk("authentication success user jlopez", idx=3),
        _make_chunk("web server request GET /admin/", idx=4),
        _make_chunk("error path traversal blocked", idx=5),
    ]
    results = retrieve("login failed", chunks, top_k=2)
    assert len(results) <= 2


def test_retrieve_relevance_order():
    chunks = [
        _make_chunk("este texto no tiene nada relevante", idx=0),
        _make_chunk("autenticación fallida usuario admin ip", idx=1),
        _make_chunk("autenticación exitosa usuario jlopez", idx=2),
    ]
    results = retrieve("autenticación fallida", chunks, top_k=3)
    assert len(results) >= 1
    # El fragmento con "autenticación fallida" debe tener mayor puntuación
    assert results[0].score >= results[-1].score


def test_retrieve_includes_source_reference():
    chunk = _make_chunk("evento de seguridad crítico", source="logs.json", idx=0)
    results = retrieve("seguridad crítico", [chunk], top_k=1)
    assert len(results) == 1
    assert "logs.json" in results[0].reference()


# ---- formato de contexto ----

def test_format_context_empty():
    text = format_context_for_prompt([])
    assert "no se encontraron" in text.lower()


def test_format_context_includes_sources():
    from app.core.rag import RetrievedChunk
    chunk = _make_chunk("evidencia importante", source="evidencia.txt", idx=2)
    retrieved = [RetrievedChunk(chunk=chunk, score=0.8)]
    text = format_context_for_prompt(retrieved)
    assert "evidencia.txt" in text
    assert "evidencia importante" in text
    assert "Fuente 1" in text
