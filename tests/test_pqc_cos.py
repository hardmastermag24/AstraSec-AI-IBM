import io,json
import pytest
from app.core.pqc import assess_inventory,synthetic_inventory,pqc_messages,build_archive
from app.core.cos_archive import archive_synthetic_pqc,NAMES


def item(algorithm,purpose='firma'):
    return {'synthetic':True,'assets':[{'id':'demo','algorithm':algorithm,'purpose':purpose,'source':'test:1','evidence':'Declaración sintética.'}]}

@pytest.mark.parametrize('algorithm,purpose,status',[
    ('RSA','firma','Revisar migración PQC'),('ECDSA','firma','Revisar migración PQC'),
    ('ML-KEM-768','establecimiento','PQC declarado; implementación no verificada'),
    ('ML-KEM-768','firma','Uso inconsistente'),('ML-DSA-65','firma','PQC declarado; implementación no verificada'),
    ('SLH-DSA-SHA2-128s','firma','PQC declarado; implementación no verificada'),
    ('ML-KEM-999','establecimiento','Parámetros por verificar'),('AES-256','cifrado','Primitiva simétrica o hash'),
    ('unknown','firma','Desconocido')])
def test_pqc_classifies_roles_and_unknowns(algorithm,purpose,status):
    assert assess_inventory(item(algorithm,purpose))['assets'][0]['status']==status


def test_private_key_and_duplicate_id_rejected():
    data=item('RSA');data['assets'][0]['evidence']='-----BEGIN PRIVATE KEY-----'
    with pytest.raises(ValueError):assess_inventory(data)
    data=item('RSA');data['assets']*=2
    with pytest.raises(ValueError):assess_inventory(data)


def test_messages_are_fixed_and_archive_reproducible():
    a=synthetic_inventory();a['assets'][0]['algorithm']='PRIVATE-DATA'
    assert 'PRIVATE-DATA' not in str(pqc_messages())
    assert build_archive()==build_archive()
    assert json.loads(build_archive()[0])['inventory']['synthetic'] is True


def configure(monkeypatch):
    for name,value in zip(NAMES,['test-secret','test-instance','https://s3.us-south.cloud-object-storage.appdomain.cloud','test-pqc-bucket']):monkeypatch.setenv(name,value)


def test_cos_missing_config_does_not_call_client(monkeypatch):
    for name in NAMES:monkeypatch.delenv(name,raising=False)
    with pytest.raises(ValueError,match='no configurado'):archive_synthetic_pqc(object())


def test_cos_untrusted_endpoint_rejected(monkeypatch):
    configure(monkeypatch);monkeypatch.setenv('COS_ENDPOINT','https://attacker.example')
    with pytest.raises(ValueError,match='oficial'):archive_synthetic_pqc(object())


def test_cos_upload_and_readback_hash(monkeypatch):
    configure(monkeypatch)
    class Fake:
        def put_object(self,**kwargs):self.kwargs=kwargs
        def get_object(self,**kwargs):return {'Body':io.BytesIO(self.kwargs['Body'])}
    client=Fake();receipt=archive_synthetic_pqc(client)
    assert receipt['verified'] and receipt['synthetic']
    assert receipt['sha256'] in client.kwargs['Key']
    assert 'ACL' not in client.kwargs
    assert b'test-secret' not in client.kwargs['Body']


def test_cos_corrupt_readback_not_success(monkeypatch):
    configure(monkeypatch)
    class Fake:
        def put_object(self,**kwargs):pass
        def get_object(self,**kwargs):return {'Body':io.BytesIO(b'corrupt')}
    with pytest.raises(RuntimeError,match='no coincidió'):archive_synthetic_pqc(Fake())


def test_pqc_model_rejects_unsupported_protocol_and_hypothesis():
    from app.core.pqc import validate_pqc_analysis
    data={'hechos':[{'texto':'RSA declarado en tls-demo','fuentes':['S1']}], 'hipotesis':[], 'recomendaciones':[], 'limitaciones':[{'texto':'Datos sintéticos','fuentes':['S2']}]}
    assert validate_pqc_analysis(json.dumps(data))
    data['recomendaciones']=[{'texto':'Configurar TLS híbrido','fuentes':['S2']}]
    with pytest.raises(ValueError):validate_pqc_analysis(json.dumps(data))
    data['recomendaciones']=[];data['hipotesis']=[{'texto':'Podría no usarse','fuentes':['S2']}]
    with pytest.raises(ValueError):validate_pqc_analysis(json.dumps(data))
