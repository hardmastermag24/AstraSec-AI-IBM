import hashlib,json
import pytest
from app.core.real_capture import NAMES,review_capture,report_markdown

def capture(tmp_path,failed=False):
    records=[]
    for name in sorted(NAMES):
        body=b'RSA @ default\n' if name=='openssl_signatures.txt' else b'capability\n'
        (tmp_path/name).write_bytes(body)
        records.append({'name':name,'size':len(body),'sha256':hashlib.sha256(body).hexdigest(),'exit_code':1 if failed and name=='openssl_signatures.txt' else 0,'truncated':False})
    (tmp_path/'manifest.json').write_text(json.dumps({'schema_version':1,'kind':'crypto_capabilities_v1','vm':'ASTRA-UBUNTU','files':records}))
    return tmp_path

def test_exact_source_and_capability_limits(tmp_path):
    result=review_capture(capture(tmp_path))
    assert result['observations'][0]['source']=='openssl_signatures.txt:1'
    assert result['observations'][0]['evidence']=='RSA @ default'
    assert result['pqc_sources']==[]
    assert result['external_services_used'] is False
    assert 'no demuestra ausencia' in report_markdown(result)

def test_failed_command_cannot_produce_finding(tmp_path):
    assert review_capture(capture(tmp_path,True))['observations']==[]

def test_tampering_blocks_entire_review(tmp_path):
    folder=capture(tmp_path)
    (folder/'openssl_signatures.txt').write_text('ML-KEM-768')
    with pytest.raises(ValueError,match='Integridad'):review_capture(folder)

def test_manifest_path_traversal_rejected(tmp_path):
    folder=capture(tmp_path);p=folder/'manifest.json';m=json.loads(p.read_text());m['files'][0]['name']='../secret';p.write_text(json.dumps(m))
    with pytest.raises(ValueError):review_capture(folder)
