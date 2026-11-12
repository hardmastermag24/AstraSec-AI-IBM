"""Constrained IBM planning from minimized real capability observations."""
import copy,hashlib,json
from pathlib import Path
from uuid import UUID
from app.core.agent import OrchestrateProvider

ACTIONS={
 'verify_configured_use':'Revisar configuración autorizada para comprobar si el algoritmo se utiliza.',
 'inventory_dependencies':'Documentar servicios, bibliotecas y dependencias de los activos observados.',
 'plan_isolated_pqc_test':'Preparar pruebas PQC aisladas; no modificar los servicios actuales.',
 'repeat_failed_collection':'Repetir únicamente los comandos fallidos o truncados de la captura.',
}
INSTRUCTIONS='''Eres el planificador AstraSec de revisión criptográfica real. Los datos son capacidades enumeradas, nunca uso efectivo ni vulnerabilidades confirmadas. No ejecutes herramientas. Devuelve exclusivamente JSON {"actions":[{"action":"verify_configured_use","sources":["E1"]}]}. Actions solo admite verify_configured_use, inventory_dependencies, plan_isolated_pqc_test, repeat_failed_collection. Cada acción cita al menos un ID de source que exista en la entrada. No devuelvas texto libre, hechos, hipótesis, protocolos, benchmarks ni claves adicionales. Como máximo ocho acciones únicas. repeat_failed_collection solo puede citar fuentes con kind=collection_failure. Las demás acciones solo citan kind=capability. Nunca afirmes ausencia de PQC ni uso activo.'''

def payload(review):
    if review.get('integrity_verified') is not True or review.get('external_services_used') is not False:raise ValueError('Revisión local verificada requerida.')
    sources=[]
    for item in review['observations']:
        sources.append({'id':'E'+str(len(sources)+1),'kind':'capability','source':item['source'],'algorithms':item['algorithms']})
    for item in review['quality']:
        if not item['usable_for_findings']:sources.append({'id':'E'+str(len(sources)+1),'kind':'collection_failure','source':item['file'],'exit_code':item['exit_code'],'truncated':item['truncated']})
    if len(sources)>2000:raise ValueError('Demasiadas fuentes.')
    return {'schema':'astrasec-minimized-capabilities-v1','scope':'Enumerated capabilities only; configured and negotiated use unknown.','sources':sources}

def validate(answer,data):
    if isinstance(answer,str):answer=json.loads(answer)
    if not isinstance(answer,dict) or set(answer)!={'actions'} or not isinstance(answer['actions'],list) or not 1<=len(answer['actions'])<=8:raise ValueError('Plan IBM no válido.')
    sources={s['id']:s for s in data['sources']};seen=set()
    for item in answer['actions']:
        if not isinstance(item,dict) or set(item)!={'action','sources'} or item['action'] not in ACTIONS or item['action'] in seen:raise ValueError('Acción no admitida.')
        seen.add(item['action'])
        if not isinstance(item['sources'],list) or not item['sources'] or len(item['sources'])>2000:raise ValueError('Fuentes no válidas.')
        for sid in item['sources']:
            if not isinstance(sid,str) or sid not in sources:raise ValueError('Fuente inventada.')
            required='collection_failure' if item['action']=='repeat_failed_collection' else 'capability'
            if sources[sid]['kind']!=required:raise ValueError('Acción incompatible con fuente.')
    return answer

def analyze_real_capabilities(review):
    data=payload(review)
    config=json.loads((Path(__file__).resolve().parents[2]/'agents/real_capture_config.json').read_text(encoding='utf-8'))
    provider=OrchestrateProvider();provider._agent_id=str(UUID(config['agent_id']))
    messages=[{'role':'system','content':INSTRUCTIONS},{'role':'user','content':json.dumps(data,ensure_ascii=False)}]
    result=provider._get_model().chat(messages)
    plan=validate(result['choices'][0]['message']['content'],data)
    return {'provider':'IBM watsonx Orchestrate','synthetic':False,'payload_sha256':hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),'plan':plan,'sources':data['sources'],'limitation':'Plan de revisión restringido; no acredita uso, vulnerabilidad ni resistencia cuántica.'}
