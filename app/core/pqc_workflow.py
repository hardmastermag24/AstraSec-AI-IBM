"""Capture-bound PQC dossier, review and local export. Never executes plan actions."""
import copy
import datetime
import hashlib
import io
import json
import re
import uuid
import zipfile
from app.core.real_ibm_advice import payload, validate, ACTIONS
from app.core.report_pdf import generate_pdf
from app.core.case_store import canonical

QUESTION = '¿Qué capacidades criptográficas declara la captura, qué no demuestra y qué debo revisar antes de proponer una migración?'
DECISIONS = ('Requiere más evidencia', 'Recomendaciones revisadas para seguimiento', 'No utilizar este plan')


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode('utf-8')


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def input_hash(data):
    # Preserve the hash format used by existing archived IBM plans.
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def capture_summary(review, folder):
    if not isinstance(folder, str) or not re.fullmatch(r'CRIPTO_[A-Za-z0-9_.-]+', folder):
        raise ValueError('Identificador de captura no válido.')
    data = payload(review)
    sha = review.get('manifest_sha256', '')
    if not re.fullmatch(r'[0-9a-f]{64}', sha):
        raise ValueError('Captura sin hash de manifiesto válido.')
    return {'folder': folder, 'vm': review['vm'], 'capture_utc': review.get('capture_utc'),
            'manifest_sha256': sha, 'quality': copy.deepcopy(review['quality']),
            'observations': len(review['observations']), 'limitations': list(review['limitations']),
            'payload': data, 'payload_sha256': input_hash(data)}


def checked_plan(plan, summary):
    if not isinstance(plan, dict) or plan.get('synthetic') is not False or plan.get('provider') != 'IBM watsonx Orchestrate':
        raise ValueError('Se requiere un plan real identificado de IBM.')
    if plan.get('payload_sha256') != summary['payload_sha256'] or plan.get('sources') != summary['payload']['sources']:
        raise ValueError('El plan no corresponde exactamente a esta captura.')
    validate(plan.get('plan'), summary['payload'])
    return copy.deepcopy(plan)


def event(record, kind):
    record['trace'].append({'event': kind, 'utc': utc(), 'capture_sha256': digest(record['capture']),
                            'plan_sha256': digest(record['ibm_plan']) if record['ibm_plan'] else None})


def create_record(review, folder, plan=None):
    summary = capture_summary(review, folder)
    record = {'schema': 'astrasec-pqc-case-v1', 'case_id': str(uuid.uuid4()),
              'lab': {'name': folder}, 'question': QUESTION, 'created_utc': utc(),
              'capture': summary, 'ibm_plan': None, 'review': None, 'trace': []}
    event(record, 'capture_verified')
    return attach_plan(record, plan) if plan else record


def attach_plan(record, plan):
    result = copy.deepcopy(record)
    plan = checked_plan(plan, result['capture'])
    if result['ibm_plan'] != plan:
        result['ibm_plan'] = plan
        result['review'] = None  # A decision never survives a different plan.
        event(result, 'archived_or_returned_ibm_plan_linked')
    return result


def register_review(record, reviewer, decision, notes, human=True):
    if not record.get('ibm_plan'):
        raise ValueError('Falta un plan válido para revisar.')
    if decision not in DECISIONS or not isinstance(reviewer, str) or not reviewer.strip() or not isinstance(notes, str) or not notes.strip():
        raise ValueError('Completa responsable, decisión y justificación.')
    if len(reviewer) > 120 or len(notes) > 4000 or type(human) is not bool:
        raise ValueError('Revisión fuera de límites.')
    result = copy.deepcopy(record)
    result['review'] = {'reviewer': reviewer.strip(), 'decision': decision, 'notes': notes.strip(),
                        'kind': 'human' if human else 'technical_rehearsal', 'utc': utc(),
                        'capture_sha256': digest(result['capture']), 'plan_sha256': digest(result['ibm_plan'])}
    event(result, 'human_review_registered' if human else 'technical_rehearsal_registered')
    return result


def validate_record(record, current_review=None, folder=None):
    if not isinstance(record, dict) or record.get('schema') != 'astrasec-pqc-case-v1':
        raise ValueError('Expediente incompatible.')
    uuid.UUID(record['case_id'])
    summary = record['capture']
    if record['lab']['name'] != summary['folder'] or summary['payload_sha256'] != input_hash(summary['payload']):
        raise ValueError('Vinculación de captura no válida.')
    if current_review is not None and summary != capture_summary(current_review, folder):
        raise ValueError('La captura cambió; verifica y crea un expediente nuevo.')
    if record['ibm_plan']:
        checked_plan(record['ibm_plan'], summary)
    review = record['review']
    if review:
        if not record['ibm_plan'] or review['capture_sha256'] != digest(summary) or review['plan_sha256'] != digest(record['ibm_plan']):
            raise ValueError('Revisión perteneciente a otra versión.')
        if review['kind'] not in ('human', 'technical_rehearsal') or review['decision'] not in DECISIONS or not review['reviewer'].strip() or not review['notes'].strip():
            raise ValueError('Revisión incompleta.')
    if not isinstance(record['trace'], list) or not record['trace']:
        raise ValueError('Falta la traza local.')
    return record


def status(record):
    if not record['ibm_plan']:
        return 'Borrador: falta plan IBM vinculado'
    if not record['review'] or record['review']['kind'] != 'human':
        return 'Borrador: revisión humana pendiente'
    if record['review']['decision'] == 'No utilizar este plan':
        return 'Plan descartado por revisión humana'
    return 'Revisión humana registrada; acciones no ejecutadas'


def report(record):
    validate_record(record)
    c = record['capture']
    lines = ['# AstraSec IA - Expediente PQC integrado', '', 'Expediente: '+record['case_id'],
             'Estado: '+status(record), 'Pregunta: '+record['question'],
             'Captura: '+c['folder'], 'Equipo: '+c['vm'], 'UTC de captura: '+str(c['capture_utc']),
             'SHA-256 del manifiesto: '+c['manifest_sha256'], 'SHA-256 del resumen IBM: '+c['payload_sha256'],
             '', '## 1. Hechos comprobados localmente',
             'Integridad verificada respecto al manifiesto. Observaciones de capacidad: '+str(c['observations'])+'.',
             'Fuentes del resumen minimizado: '+str(len(c['payload']['sources']))+'.',
             'No se ejecutan herramientas remotas ni acciones del plan. No es certificación PQC ni validación FIPS.',
             '', '## 2. Calidad y errores de captura']
    for q in c['quality']:
        lines.append('- '+q['file']+': exit_code='+str(q['exit_code'])+', truncado='+str(q['truncated'])+'. '+('Utilizable.' if q['usable_for_findings'] else 'Excluido de hallazgos; no implica ausencia.'))
    lines += ['', '## 3. Plan IBM vinculado']
    if record['ibm_plan']:
        refs = {s['id']: s['source'] for s in c['payload']['sources']}
        lines += ['Proveedor del plan archivado: IBM watsonx Orchestrate.', 'El hash y las fuentes del plan coinciden con el resumen. Reutilizarlo no realiza otra consulta.']
        for action in record['ibm_plan']['plan']['actions']:
            lines.append('- '+ACTIONS[action['action']]+' Fuentes: '+', '.join(s+' ('+refs[s]+')' for s in action['sources']))
    else:
        lines.append('Plan no disponible. No se atribuyen recomendaciones al modelo.')
    lines += ['', '## 4. Revisión y decisión']
    r = record['review']
    if r:
        lines += ['Tipo: '+('Revisión humana declarada' if r['kind']=='human' else 'Ensayo técnico; no aprobación humana'),
                  'Responsable declarado: '+r['reviewer'], 'UTC: '+r['utc'], 'Decisión: '+r['decision'], 'Justificación: '+r['notes']]
    else:
        lines.append('Pendiente. Este reporte es un borrador.')
    lines += ['', '## 5. Trazabilidad observable']
    lines += ['- '+e['utc']+' - '+e['event'] for e in record['trace']]
    lines += ['', '## 6. Limitaciones']+['- '+x for x in c['limitations']]
    lines += ['- La revisión humana es declarada por el operador local; no autentica identidad ni firma digital.',
              '- La traza documenta pasos de la aplicación, no razonamiento interno, delegación multiagente ni ejecución de herramientas IBM.',
              '- El paquete minimizado omite logs brutos y credenciales. Los originales permanecen en el laboratorio.',
              '- Las comprobaciones de estructura y referencias no prueban exactitud semántica completa del modelo.']
    return '\n'.join(lines)+'\n'


def export_bundle(record, receipt=None):
    if receipt:
        if receipt['case_id'] != record['case_id'] or receipt['sha256'] != hashlib.sha256(canonical(record)).hexdigest():
            raise ValueError('El recibo no corresponde a esta versión guardada.')
    markdown = report(record)
    if receipt:
        markdown = markdown.replace('Estado: ', 'Revisión guardada: '+str(receipt['revision'])+'\nEstado: ', 1)
    files = {'expediente.json': encoded(record), 'reporte.md': markdown.encode('utf-8'),
             'reporte.pdf': generate_pdf(markdown), 'traza.json': encoded(record['trace'])}
    if receipt:
        files['recibo_guardado.json'] = encoded(receipt)
    files['LEER_PRIMERO.txt'] = ('Expediente PQC local minimizado. '+status(record)+'.\nLos hashes permiten comprobar consistencia; no son firma externa ni certificación.\nLas acciones del plan no se ejecutan.\n').encode('utf-8')
    files['SHA256.json'] = encoded({n: hashlib.sha256(b).hexdigest() for n, b in files.items()})
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, body in files.items():z.writestr(name, body)
    return output.getvalue(), files['reporte.pdf'], markdown
