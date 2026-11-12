import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from app.core import ibm_demo


def test_archived_result_matches_exact_sources_and_response(monkeypatch, tmp_path):
    monkeypatch.setattr(ibm_demo, 'PRIVATE', tmp_path)
    receipt = ibm_demo.load_saved()
    assert receipt['structure_valid'] is True
    assert receipt['input_sha256'] == ibm_demo.input_hash()
    assert len(receipt['sources']) == 2
    assert receipt['elapsed_seconds'] == 8.48


def test_no_authorization_means_no_network(monkeypatch):
    client = Mock(side_effect=AssertionError('Unexpected network client'))
    monkeypatch.setattr('app.core.agent.OrchestrateProvider', client)
    with pytest.raises(ValueError, match='Autoriza'):
        ibm_demo.analyze()
    client.assert_not_called()


def test_tampered_fixture_blocks_client_creation(monkeypatch, tmp_path):
    for path in ibm_demo.ASSETS.iterdir():
        if path.is_file():
            (tmp_path/path.name).write_bytes(path.read_bytes())
    (tmp_path/'eventos_acceso_FICTICIOS.txt').write_text('modified', encoding='utf-8')
    monkeypatch.setattr(ibm_demo, 'ASSETS', tmp_path)
    client = Mock(side_effect=AssertionError('Unexpected network client'))
    monkeypatch.setattr('app.core.agent.OrchestrateProvider', client)
    with pytest.raises(ValueError, match='cambió'):
        ibm_demo.analyze(authorized=True)
    client.assert_not_called()


@pytest.mark.parametrize('change', ['sources', 'analysis', 'input_sha256'])
def test_modified_receipts_are_rejected(change):
    receipt = copy.deepcopy(ibm_demo.load_saved())
    if change == 'sources':
        receipt['sources'][0]['contenido'] += 'altered'
    elif change == 'analysis':
        receipt['analysis']['hechos'][0]['texto'] = 'invented'
    else:
        receipt['input_sha256'] = 'wrong'
    with pytest.raises(ValueError):
        ibm_demo.validate_receipt(receipt)


def test_authorized_call_sends_only_fixtures_and_saves_version(monkeypatch, tmp_path):
    archived = ibm_demo.load_saved()
    chat = Mock(return_value={'choices': [{'message': {'content': archived['raw_response']}}]})
    provider = SimpleNamespace(_get_model=lambda: SimpleNamespace(chat=chat))
    monkeypatch.setattr('app.core.agent.OrchestrateProvider', lambda: provider)
    monkeypatch.setattr(ibm_demo, 'PRIVATE', tmp_path)
    result = ibm_demo.analyze(authorized=True)
    outgoing = chat.call_args.args[0]
    payload = json.loads(outgoing[1]['content'])
    assert set(payload) == {'caso', 'fuentes'}
    assert payload['fuentes'] == ibm_demo.sources()
    assert len(outgoing) == 2
    assert ibm_demo.load_saved() == result
    assert len(list(tmp_path.glob('*.json'))) == 1


def test_main_ui_reuses_result_without_network_and_gates_new_calls(monkeypatch):
    from streamlit.testing.v1 import AppTest
    network = Mock(side_effect=AssertionError('Unexpected IBM request'))
    monkeypatch.setattr(ibm_demo, 'analyze', network)
    entry = Path(__file__).resolve().parents[1]/'app/main.py'
    app = AppTest.from_file(str(entry)).run(timeout=20)
    app.sidebar.radio(key='nav_page').set_value('🤖 Agente').run()
    app.radio(key='agent_mode').set_value('Prueba real IBM · datos ficticios').run()
    assert not app.exception
    assert app.button(key='ibm_demo_run').disabled
    app.run()
    network.assert_not_called()
    assert any('Resultado real de IBM recuperado' in item.value for item in app.success)


def test_failed_new_call_keeps_archived_real_result(monkeypatch):
    from streamlit.testing.v1 import AppTest
    network = Mock(side_effect=RuntimeError('IBM unavailable'))
    monkeypatch.setattr(ibm_demo, 'analyze', network)
    entry = Path(__file__).resolve().parents[1]/'app/main.py'
    app = AppTest.from_file(str(entry)).run(timeout=20)
    app.sidebar.radio(key='nav_page').set_value('🤖 Agente').run()
    app.radio(key='agent_mode').set_value('Prueba real IBM · datos ficticios').run()
    app.checkbox(key='ibm_demo_consent').set_value(True).run()
    assert not app.button(key='ibm_demo_run').disabled
    app.button(key='ibm_demo_run').click().run()
    network.assert_called_once_with(authorized=True)
    assert not app.exception
    assert any('Se conserva el resultado anterior' in item.value for item in app.error)
    assert any('Resultado real de IBM recuperado' in item.value for item in app.success)


def test_latest_local_receipt_takes_precedence(monkeypatch, tmp_path):
    monkeypatch.setattr(ibm_demo, 'PRIVATE', tmp_path)
    archived = ibm_demo.load_saved()
    newer = copy.deepcopy(archived)
    newer['elapsed_seconds'] = 12.45
    newer['timestamp_utc'] = '2026-11-04T12:00:00+00:00'
    (tmp_path / '20261101.json').write_text(json.dumps(archived), encoding='utf-8')
    (tmp_path / '20261104.json').write_text(json.dumps(newer), encoding='utf-8')
    assert ibm_demo.load_saved() == newer
