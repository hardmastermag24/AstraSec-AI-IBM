import hashlib,json,sqlite3
import pytest
from app.core.case_store import CaseStore,ConflictError,canonical

def test_persist_and_conflicting_writer(tmp_path):
    path=tmp_path/'cases.sqlite3';store=CaseStore(path)
    first=store.save({'lab':{'name':'Piloto'},'notes':'evidencia'})
    reopened=CaseStore(path)
    assert reopened.load(first['case_id'])[0]['notes']=='evidencia'
    second=reopened.save({'lab':{'name':'Piloto'},'notes':'revisión'},first['case_id'],1)
    with pytest.raises(ConflictError):store.save({'lab':{'name':'Piloto'}},first['case_id'],1)
    assert store.load(first['case_id'])[1]==second['revision']==2
    assert store.verify_audit()

def test_recomputed_payload_hash_still_rejected(tmp_path):
    path=tmp_path/'cases.sqlite3';store=CaseStore(path)
    saved=store.save({'lab':{'name':'Piloto'}})
    altered=canonical({'lab':{'name':'alterado'}})
    with sqlite3.connect(path) as db:db.execute('UPDATE cases SET snapshot=?,sha256=?',(altered.decode(),hashlib.sha256(altered).hexdigest()))
    with pytest.raises(ValueError,match='auditoría'):store.load(saved['case_id'])

def test_audit_corruption_blocks_recovery(tmp_path):
    path=tmp_path/'cases.sqlite3';store=CaseStore(path)
    saved=store.save({'lab':{'name':'Piloto'}})
    with sqlite3.connect(path) as db:db.execute("UPDATE audit SET timestamp='alterado'")
    assert not store.verify_audit()
    with pytest.raises(ValueError):store.load(saved['case_id'])
