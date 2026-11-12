"""Optional IBM services. Only fixed synthetic payloads are sent by these probes."""
import hashlib,io,json,os,re
from urllib.parse import urlparse
from app.core.pqc import build_archive,pqc_messages,validate_pqc_analysis

SERVICE_VARS={
 'COS':('COS_API_KEY','COS_SERVICE_INSTANCE_ID','COS_ENDPOINT','COS_BUCKET'),
 'Cloudant':('CLOUDANT_API_KEY','CLOUDANT_URL','CLOUDANT_DATABASE'),
 'watsonx.ai Runtime':('WATSONX_API_KEY','WATSONX_URL','WATSONX_PROJECT_ID'),
 'Speech to Text':('STT_API_KEY','STT_URL'),
 'Text to Speech':('TTS_API_KEY','TTS_URL'),
}


def readiness():
    return {name:{'configured':all(os.environ.get(k,'').strip() for k in keys),'missing':[k for k in keys if not os.environ.get(k,'').strip()],'live_verified':False} for name,keys in SERVICE_VARS.items()}


def endpoint(value,service):
    u=urlparse(value)
    patterns={'cloudant':r'[a-z0-9-]+[.]cloudantnosqldb[.]appdomain[.]cloud','speech-to-text':r'api[.][a-z0-9-]+[.]speech-to-text[.]watson[.]cloud[.]ibm[.]com','text-to-speech':r'api[.][a-z0-9-]+[.]text-to-speech[.]watson[.]cloud[.]ibm[.]com'}
    if u.scheme!='https' or not re.fullmatch(patterns[service],u.hostname or '') or u.port or u.username or u.password or u.query or u.fragment:
        raise ValueError('Endpoint IBM no válido.')
    if service=='cloudant' and u.path not in ('','/'):raise ValueError('URL Cloudant debe identificar el servicio, sin base de datos.')
    if service!='cloudant' and not re.fullmatch(r'/instances/[a-fA-F0-9-]{36}/?',u.path):raise ValueError('Endpoint de voz sin instancia válida.')
    return value.rstrip('/')


def required(name):
    missing=readiness()[name]['missing']
    if missing:raise ValueError('Servicio pendiente de configuración: '+', '.join(missing))


def archive_synthetic_cloudant(client=None):
    required('Cloudant')
    url=endpoint(os.environ['CLOUDANT_URL'],'cloudant')
    database=os.environ['CLOUDANT_DATABASE']
    if not re.fullmatch(r'[a-z][a-z0-9_$()+/-]{0,99}',database) or '/' in database:raise ValueError('Base Cloudant no válida.')
    if client is None:
        from ibmcloudant.cloudant_v1 import CloudantV1
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
        client=CloudantV1(authenticator=IAMAuthenticator(os.environ['CLOUDANT_API_KEY']))
        client.set_service_url(url)
        client.set_http_config({'timeout':30})
    body,digest=build_archive();doc_id='astrasec-pqc-synthetic-'+digest
    doc={'_id':doc_id,'schema':'astrasec-evaluation-v1','synthetic':True,'payload_sha256':digest,'payload_json':body.decode()}
    try:
        try:client.post_document(db=database,document=doc).get_result()
        except Exception as exc:
            if getattr(exc,'code',None)!=409:raise
        actual=client.get_document(db=database,doc_id=doc_id).get_result()
        if actual.get('payload_sha256')!=digest or hashlib.sha256(actual.get('payload_json','').encode()).hexdigest()!=digest:raise ValueError('Cloudant: contenido no coincide con el hash esperado.')
    except ValueError:raise
    except Exception:raise RuntimeError('Cloudant: no se completó escritura y verificación; revisar base y permisos.') from None
    return {'id':doc_id,'sha256':digest,'verified':True,'synthetic':True}


def analyze_synthetic_runtime():
    required('watsonx.ai Runtime')
    from app.core.agent import WatsonxProvider
    try:
        response=WatsonxProvider()._get_model().chat(messages=pqc_messages())
        return validate_pqc_analysis(response['choices'][0]['message']['content'])
    except Exception:raise RuntimeError('Runtime: no se obtuvo un análisis PQC válido. Revisar credencial, proyecto, modelo y permisos.') from None


def synthetic_voice_roundtrip(tts=None,stt=None):
    required('Speech to Text');required('Text to Speech')
    tts_url=endpoint(os.environ['TTS_URL'],'text-to-speech');stt_url=endpoint(os.environ['STT_URL'],'speech-to-text')
    text='Prueba sintética de AstraSec. La evidencia debe revisarse antes de confirmar una conclusión.'
    if tts is None or stt is None:
        from ibm_watson import SpeechToTextV1,TextToSpeechV1
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
        tts=TextToSpeechV1(authenticator=IAMAuthenticator(os.environ['TTS_API_KEY']));tts.set_service_url(tts_url);tts.set_http_config({'timeout':30})
        stt=SpeechToTextV1(authenticator=IAMAuthenticator(os.environ['STT_API_KEY']));stt.set_service_url(stt_url);stt.set_http_config({'timeout':30})
    try:
        voices=tts.list_voices().get_result()['voices']
        voice=next(v['name'] for v in voices if v.get('language','').startswith('es-'))
        audio=tts.synthesize(text,accept='audio/wav',voice=voice).get_result().content
        if not audio.startswith(b'RIFF') or len(audio)>5*1024*1024:raise ValueError()
        models=stt.list_models().get_result()['models']
        model=next(m['name'] for m in models if m.get('language','').startswith('es-'))
        result=stt.recognize(audio=io.BytesIO(audio),content_type='audio/wav',model=model).get_result()
        transcript=' '.join(r['alternatives'][0]['transcript'] for r in result.get('results',[]) if r.get('alternatives'))
        if not transcript.strip():raise ValueError()
    except Exception:raise RuntimeError('Voz: no se completó la prueba sintética; revisar modelos disponibles, claves y permisos.') from None
    return {'synthetic':True,'input':text,'transcript':transcript,'audio':audio,'audio_sha256':hashlib.sha256(audio).hexdigest()}
