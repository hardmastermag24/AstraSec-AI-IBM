"""Read local connection receipts; never confuse configuration with live checks."""
import json
from pathlib import Path

def connection_results(root=None):
    root=Path(root) if root else Path(__file__).resolve().parents[2]
    results={}
    def read(name):
        try:return json.loads((root/'data'/name).read_text(encoding='utf-8'))
        except (OSError,ValueError):return {}
    cos=read('cos_live_receipt.json')
    if cos.get('verified'):results['COS']='Escritura y lectura SHA-256 verificadas con datos sintéticos.'
    cloud=read('private/cloudant_live_receipt.json')
    if cloud.get('writer_verification',{}).get('verified'):
        results['Cloudant']='Base creada; documento sintético escrito y verificado con Writer.'
        if not cloud.get('temporary_credential_deleted'):results['Cloudant']+=' Revisar retirada de credencial temporal.'
    voice=read('private/service_live_checks.json').get('voice',{})
    if voice.get('transcript') and voice.get('audio_sha256'):
        results['Text to Speech']='Generación de audio sintético verificada.'
        results['Speech to Text']='Transcripción de audio sintético verificada.'
    runtime=read('private/runtime_connection_status.json')
    if runtime.get('status'):results['watsonx.ai Runtime']=runtime['status']
    return results
