"""
Pruebas unitarias del módulo agent.py
Cubre DemoProvider, WatsonxProvider y la factory load_provider.
"""
import pytest
import warnings
from app.core.agent import DemoProvider, WatsonxProvider, load_provider, DEMO_LABEL
from app.core.rag import RetrievedChunk
from app.core.ingest import DocumentChunk


def _make_retrieved(text: str, source: str = "test.txt") -> RetrievedChunk:
    chunk = DocumentChunk(source=source, chunk_index=0, text=text, file_type="txt")
    return RetrievedChunk(chunk=chunk, score=0.5)


# ============================================================
# DemoProvider
# ============================================================

def test_demo_provider_name():
    provider = DemoProvider()
    assert "demo" in provider.provider_name.lower()


def test_demo_provider_response_contains_label():
    provider = DemoProvider()
    response = provider.analyze("¿Qué ocurrió?", [], [])
    assert DEMO_LABEL in response


def test_demo_provider_response_is_string():
    provider = DemoProvider()
    response = provider.analyze("consulta de prueba", [], [])
    assert isinstance(response, str)
    assert len(response) > 0


def test_demo_provider_with_context():
    provider = DemoProvider()
    chunks = [_make_retrieved("login failed admin", "logs.json")]
    response = provider.analyze("¿Hay intentos fallidos?", chunks, [])
    assert DEMO_LABEL in response
    assert "1" in response  # menciona que usó 1 fragmento


def test_demo_provider_with_history():
    provider = DemoProvider()
    history = [
        {"role": "user", "content": "primera pregunta"},
        {"role": "agent", "content": "primera respuesta demo"},
    ]
    response = provider.analyze("segunda pregunta", [], history)
    assert isinstance(response, str)


# ============================================================
# WatsonxProvider — validación de credenciales
# ============================================================

def test_watsonx_provider_raises_on_missing_env(monkeypatch):
    """Sin variables de entorno debe lanzar EnvironmentError."""
    for k in ["WATSONX_API_KEY", "WATSONX_URL", "WATSONX_PROJECT_ID", "WATSONX_MODEL"]:
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(EnvironmentError, match="Faltan variables"):
        WatsonxProvider()


def test_watsonx_provider_raises_on_partial_env(monkeypatch):
    """Con solo API key debe fallar por URL y PROJECT_ID faltantes."""
    monkeypatch.setenv("WATSONX_API_KEY", "fake-key")
    monkeypatch.delenv("WATSONX_URL", raising=False)
    monkeypatch.delenv("WATSONX_PROJECT_ID", raising=False)
    with pytest.raises(EnvironmentError, match="WATSONX_URL"):
        WatsonxProvider()


def test_watsonx_provider_name(monkeypatch):
    """Con todas las variables configuradas, el provider_name incluye el model_id."""
    monkeypatch.setenv("WATSONX_API_KEY", "fake-key")
    monkeypatch.setenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "fake-project-id")
    monkeypatch.setenv("WATSONX_MODEL", "ibm/granite-3-3-8b-instruct")
    provider = WatsonxProvider()
    assert "watsonx" in provider.provider_name.lower()
    assert "granite" in provider.provider_name.lower()


def test_watsonx_provider_uses_default_model(monkeypatch):
    """Si WATSONX_MODEL no está definido, usa el modelo por defecto."""
    monkeypatch.setenv("WATSONX_API_KEY", "fake-key")
    monkeypatch.setenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "fake-project-id")
    monkeypatch.delenv("WATSONX_MODEL", raising=False)
    provider = WatsonxProvider()
    assert WatsonxProvider._DEFAULT_MODEL in provider.provider_name


def test_watsonx_analyze_mocked(monkeypatch):
    """
    Verifica que analyze() llama a model.chat() y procesa la respuesta correctamente.
    No realiza llamadas de red reales.
    """
    monkeypatch.setenv("WATSONX_API_KEY", "fake-key")
    monkeypatch.setenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "fake-project-id")
    monkeypatch.setenv("WATSONX_MODEL", "ibm/granite-3-3-8b-instruct")

    # Mock de ModelInference y Credentials
    class FakeModel:
        def chat(self, messages):
            return {
                "choices": [{"message": {"role": "assistant", "content": "Respuesta de prueba."}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }

    class FakeCredentials:
        def __init__(self, url, api_key): pass

    import app.core.agent as agent_module

    def fake_get_model(self):
        return FakeModel()

    monkeypatch.setattr(agent_module.WatsonxProvider, "_get_model", fake_get_model)

    provider = WatsonxProvider()
    chunks = [_make_retrieved("login failed admin", "logs.json")]
    response = provider.analyze("¿Hubo intentos fallidos?", chunks, [])

    assert "Respuesta de prueba." in response
    assert "logs.json" in response  # debe incluir fuentes
    assert "15" in response          # tokens totales


def test_watsonx_analyze_bad_response_raises(monkeypatch):
    """Si la respuesta del modelo tiene estructura inesperada, lanza RuntimeError."""
    monkeypatch.setenv("WATSONX_API_KEY", "fake-key")
    monkeypatch.setenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "fake-project-id")

    class BrokenModel:
        def chat(self, messages):
            return {"unexpected": "structure"}

    import app.core.agent as agent_module
    monkeypatch.setattr(agent_module.WatsonxProvider, "_get_model", lambda self: BrokenModel())

    provider = WatsonxProvider()
    with pytest.raises(RuntimeError, match="inesperada"):
        provider.analyze("consulta", [], [])


# ============================================================
# load_provider — factory
# ============================================================

def test_load_provider_default_is_demo(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    provider = load_provider()
    assert isinstance(provider, DemoProvider)


def test_load_provider_demo_explicit(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "demo")
    provider = load_provider()
    assert isinstance(provider, DemoProvider)


def test_load_provider_watsonx_ok(monkeypatch):
    """Con todas las variables watsonx configuradas devuelve WatsonxProvider."""
    monkeypatch.setenv("AI_PROVIDER", "watsonx")
    monkeypatch.setenv("WATSONX_API_KEY", "fake-key")
    monkeypatch.setenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "fake-project")
    provider = load_provider()
    assert isinstance(provider, WatsonxProvider)


def test_load_provider_watsonx_missing_env_falls_back(monkeypatch):
    """Si faltan variables watsonx, cae a demo con advertencia."""
    monkeypatch.setenv("AI_PROVIDER", "watsonx")
    for k in ["WATSONX_API_KEY", "WATSONX_URL", "WATSONX_PROJECT_ID"]:
        monkeypatch.delenv(k, raising=False)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        provider = load_provider()
        assert isinstance(provider, DemoProvider)
        assert len(w) == 1
        assert "WatsonxProvider" in str(w[0].message)


def test_load_provider_unknown_falls_back_to_demo(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "proveedor_inexistente_xyz")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        provider = load_provider()
        assert isinstance(provider, DemoProvider)
        assert len(w) == 1
        assert "no reconocido" in str(w[0].message).lower()
