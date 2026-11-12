"""IBM COS archive for the fixed synthetic PQC assessment only."""
import hashlib
import os
import re
from urllib.parse import urlparse
from app.core.pqc import build_archive

NAMES=('COS_API_KEY','COS_SERVICE_INSTANCE_ID','COS_ENDPOINT','COS_BUCKET')

def cos_status():
    return {key: bool(os.environ.get(key,'').strip()) for key in NAMES}


def archive_synthetic_pqc(client=None):
    values={key:os.environ.get(key,'').strip() for key in NAMES}
    if not all(values.values()):
        raise ValueError('COS no configurado: faltan credenciales, endpoint o bucket. No se intentó ninguna transferencia.')
    endpoint=urlparse(values['COS_ENDPOINT'])
    if endpoint.scheme!='https' or not re.fullmatch(r's3[.][a-z0-9.-]+[.]cloud-object-storage[.]appdomain[.]cloud',endpoint.hostname or '') or endpoint.port or endpoint.username or endpoint.password or endpoint.path not in ('','/') or endpoint.query or endpoint.fragment:
        raise ValueError('COS_ENDPOINT debe ser un endpoint HTTPS oficial de IBM COS.')
    bucket=values['COS_BUCKET']
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]',bucket):
        raise ValueError('Nombre de bucket COS no válido.')
    if client is None:
        import ibm_boto3
        from ibm_botocore.client import Config
        client=ibm_boto3.client('s3',ibm_api_key_id=values['COS_API_KEY'],ibm_service_instance_id=values['COS_SERVICE_INSTANCE_ID'],config=Config(signature_version='oauth',connect_timeout=15,read_timeout=30,retries={'max_attempts':1}),endpoint_url=values['COS_ENDPOINT'])
    body,digest=build_archive()
    key='astrasec/pqc/synthetic/'+digest+'.json'
    try:
        client.put_object(Bucket=bucket,Key=key,Body=body,ContentType='application/json',Metadata={'sha256':digest,'dataset':'synthetic'})
        received=client.get_object(Bucket=bucket,Key=key)['Body'].read(len(body)+1)
        if hashlib.sha256(received).hexdigest()!=digest:
            raise RuntimeError('COS: el objeto fue enviado, pero la lectura no coincidió con el SHA-256 esperado.')
    except RuntimeError:
        raise
    except Exception:
        raise RuntimeError('No se pudo completar escritura y verificación COS. Revisar acceso al bucket; no se muestran credenciales ni respuestas internas.') from None
    return {'bucket':bucket,'key':key,'sha256':digest,'verified':True,'synthetic':True}
