"""Reproducible local quality checks and export bundle for governance review."""
import datetime,hashlib,json
from app.core.pqc import assess_inventory,synthetic_inventory,validate_pqc_analysis


def evaluation_bundle():
    assets=assess_inventory(synthetic_inventory())['assets']
    checks=[{'id':'rsa_requires_review','passed':assets[0]['status']=='Revisar migración PQC'}, {'id':'kem_not_certification','passed':'no verificada' in assets[1]['status']}, {'id':'signature_not_certification','passed':'no verificada' in assets[2]['status']}]
    sample={'hechos':[{'texto':'RSA declarado','fuentes':['S1']}],'hipotesis':[],'recomendaciones':[],'limitaciones':[{'texto':'Datos sintéticos','fuentes':['S1']}]}
    for name,mutate in [('unknown_source',lambda d:d['hechos'][0].update(fuentes=['S9'])),('unsupported_protocol',lambda d:d['recomendaciones'].append({'texto':'Configurar TLS híbrido','fuentes':['S2']}))]:
        data=json.loads(json.dumps(sample));mutate(data)
        try:validate_pqc_analysis(json.dumps(data));passed=False
        except ValueError:passed=True
        checks.append({'id':'reject_'+name,'passed':passed})
    body={'schema':'astrasec-local-evaluation-v1','generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'synthetic':True,'checks':checks,'passed':sum(x['passed'] for x in checks),'total':len(checks),'scope':'Deterministic local checks only. Not a watsonx.governance evaluation, semantic certification, cryptographic benchmark or production approval.','intended_review':'Import or review these artifacts in the assigned watsonx.ai Studio / Governance project after configuring its authorized workspace.'}
    encoded=json.dumps(body,ensure_ascii=False,sort_keys=True,indent=2).encode()
    return encoded,hashlib.sha256(encoded).hexdigest()
