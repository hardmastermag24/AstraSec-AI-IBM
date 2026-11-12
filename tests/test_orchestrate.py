import pytest
from app.core.agent import load_provider, OrchestrateProvider

@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'orchestrate')
    monkeypatch.setenv('ORCHESTRATE_API_KEY', 'test-secret')
    monkeypatch.setenv('ORCHESTRATE_URL', 'https://api.jp-tok.watson-orchestrate.cloud.ibm.com/instances/00000000-0000-4000-8000-000000000005')
    monkeypatch.setenv('ORCHESTRATE_AGENT_ID', '00000000-0000-4000-8000-000000000006')
    return load_provider()

def test_factory_and_authentication_payload(provider, monkeypatch):
    calls = []
    def post(url, payload, token=None):
        calls.append((url, payload, token))
        if len(calls) == 1:
            return {'access_token': 'test-token'}
        return {'choices': [{'message': {'content': 'OK'}}]}
    monkeypatch.setattr(provider, '_post', post)
    answer = provider.analyze('di solo: OK', [], [])
    assert isinstance(provider, OrchestrateProvider)
    assert answer.startswith('OK') and 'Fuentes consultadas (0)' in answer
    assert calls[0][0] == 'https://iam.cloud.ibm.com/identity/token'
    assert calls[0][1]['apikey'] == 'test-secret'
    assert calls[1][2] == 'test-token'
    assert calls[1][1]['stream'] is False

@pytest.mark.parametrize('chunks,history', [([object()], []), ([], [{'role': 'user', 'content': 'private'}])])
def test_evidence_and_history_blocked_before_network(provider, monkeypatch, chunks, history):
    monkeypatch.setattr(provider, '_post', lambda *a, **k: pytest.fail('Unexpected network'))
    with pytest.raises(ValueError, match='Fase 1'):
        provider.analyze('query', chunks, history)

def test_untrusted_endpoint_rejected(provider, monkeypatch):
    monkeypatch.setenv('ORCHESTRATE_URL', 'https://attacker.example/instances/00000000-0000-4000-8000-000000000005')
    with pytest.raises(ValueError, match='HTTPS oficial'):
        load_provider()

def test_malformed_response_does_not_expose_body(provider, monkeypatch):
    def post(url, payload, token=None):
        return {'access_token': 'test-token'} if token is None else {'sensitive': 'private-response'}
    monkeypatch.setattr(provider, '_post', post)
    with pytest.raises(RuntimeError) as error:
        provider.analyze('di solo: OK', [], [])
    assert 'private-response' not in str(error.value)

def test_http_error_does_not_expose_secret(provider, monkeypatch):
    from urllib.error import HTTPError
    import urllib.request
    class BrokenOpener:
        def open(self, *args, **kwargs):
            raise HTTPError('https://example.com', 401, 'test-secret', {}, None)
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *a: BrokenOpener())
    with pytest.raises(RuntimeError, match='HTTP 401') as error:
        provider._post('https://iam.cloud.ibm.com/identity/token', {'apikey': 'test-secret'})
    assert 'test-secret' not in str(error.value)
