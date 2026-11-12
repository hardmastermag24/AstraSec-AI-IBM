import copy,hashlib,io,json,zipfile
import pytest
from app.core.case_store import CaseStore,ConflictError
from app.core.pqc_workflow import (create_record,capture_summary,attach_plan,register_review,
    checked_plan,validate_record,status,export_bundle,input_hash,DECISIONS)


def fixture():
    review={'vm':'ASTRA-UBUNTU','capture_utc':'2026-10-21T00:00:00Z','manifest_sha256':'a'*64,
        'integrity_verified':True,'external_services_used':False,
        'observations':[{'source':'openssl_signatures.txt:1','algorithms':['RSA'],'evidence':'RAW_PRIVATE_SENTINEL'}],
        'quality':[{'file':'paquetes_cripto.txt','exit_code':1,'truncated':False,'usable_for_findings':False,'sha256':'b'*64}],
        'limitations':['Capacidad no demuestra uso.']}
    summary=capture_summary(review,'CRIPTO_ASTRA-UBUNTU_TEST')
    data=summary['payload']
    plan={'provider':'IBM watsonx Orchestrate','synthetic':False,'payload_sha256':input_hash(data),
        'sources':data['sources'],'plan':{'actions':[{'action':'verify_configured_use','sources':['E1']},{'action':'repeat_failed_collection','sources':['E2']}]}}
    return review,plan


def record():
    r,p=fixture();return create_record(r,'CRIPTO_ASTRA-UBUNTU_TEST',p)


def test_end_to_end_bound_plan_review_persist_export(tmp_path):
    r=register_review(record(),'Analista de prueba',DECISIONS[0],'Falta verificar uso configurado.',human=True)
    store=CaseStore(tmp_path/'pqc.sqlite3');receipt=store.save(r,r['case_id'])
    restored,revision=store.load(r['case_id'])
    validate_record(restored,*[fixture()[0],'CRIPTO_ASTRA-UBUNTU_TEST'])
    bundle,pdf,md=export_bundle(restored,receipt)
    with zipfile.ZipFile(io.BytesIO(bundle)) as z:
        manifest=json.loads(z.read('SHA256.json'))
        assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in manifest.items())
        assert set(z.namelist())==set(manifest)|{'SHA256.json'}
        assert 'RAW_PRIVATE_SENTINEL' not in z.read('expediente.json').decode()
    assert pdf.startswith(b'%PDF') and revision==1 and store.verify_audit()
    assert 'Revisión humana registrada' in md and r['case_id'] in md and 'Revisión guardada: 1' in md


@pytest.mark.parametrize('field,value',[('synthetic',True),('payload_sha256','c'*64),('sources',[]),('provider','demo')])
def test_incompatible_plan_rejected(field,value):
    review,plan=fixture();plan[field]=value
    with pytest.raises(ValueError):create_record(review,'CRIPTO_ASTRA-UBUNTU_TEST',plan)


def test_source_tampering_rejected_even_with_original_hash():
    review,plan=fixture();plan=copy.deepcopy(plan);plan['sources'][0]['source']='invented.txt:1'
    with pytest.raises(ValueError):create_record(review,'CRIPTO_ASTRA-UBUNTU_TEST',plan)


def test_changed_capture_cannot_restore_old_decision():
    r=record();changed=fixture()[0];changed['manifest_sha256']='c'*64
    with pytest.raises(ValueError,match='cambió'):validate_record(r,changed,'CRIPTO_ASTRA-UBUNTU_TEST')


def test_new_plan_invalidates_review():
    r=register_review(record(),'Test',DECISIONS[0],'Necesita datos.',True)
    plan=copy.deepcopy(r['ibm_plan']);plan['plan']['actions']=plan['plan']['actions'][:1]
    changed=attach_plan(r,plan)
    assert changed['review'] is None and 'pendiente' in status(changed)
    assert r['review'] is not None


def test_technical_rehearsal_never_means_human_approval():
    r=register_review(record(),'Ensayo',DECISIONS[1],'Solo prueba funcional.',False)
    assert status(r)=='Borrador: revisión humana pendiente'
    assert 'technical_rehearsal_registered'==r['trace'][-1]['event']
    assert 'no aprobación humana' in export_bundle(r)[2]


@pytest.mark.parametrize('name,decision,notes',[('',DECISIONS[0],'nota'),('Test','ejecutar_shell','nota'),('Test',DECISIONS[0],'')])
def test_incomplete_or_unsupported_decision_rejected(name,decision,notes):
    with pytest.raises(ValueError):register_review(record(),name,decision,notes)


def test_missing_plan_is_explicit_draft_and_not_reviewable():
    r=create_record(fixture()[0],'CRIPTO_ASTRA-UBUNTU_TEST')
    assert 'falta plan' in status(r)
    assert 'Plan no disponible' in export_bundle(r)[2]
    with pytest.raises(ValueError):register_review(r,'Test',DECISIONS[0],'nota')


def test_receipt_from_other_content_cannot_be_exported(tmp_path):
    r=record();store=CaseStore(tmp_path/'x.sqlite');receipt=store.save(r,r['case_id'])
    changed=register_review(r,'Test',DECISIONS[0],'nota',False)
    with pytest.raises(ValueError,match='recibo'):export_bundle(changed,receipt)
    store.save(changed,r['case_id'],1)
    with pytest.raises(ConflictError):store.save(r,r['case_id'],1)


def test_fake_review_on_other_plan_rejected():
    r=register_review(record(),'Test',DECISIONS[0],'nota')
    r['review']['plan_sha256']='c'*64
    with pytest.raises(ValueError):export_bundle(r)


def test_plan_actions_remain_bounded():
    review,plan=fixture();plan['plan']['actions'][0]['action']='run_shell'
    with pytest.raises(ValueError):create_record(review,'CRIPTO_ASTRA-UBUNTU_TEST',plan)


@pytest.mark.parametrize('folder',['../secret','C:/secret','CRIPTO_test/../../x'])
def test_capture_identity_never_allows_arbitrary_path(folder):
    with pytest.raises(ValueError):create_record(fixture()[0],folder)
