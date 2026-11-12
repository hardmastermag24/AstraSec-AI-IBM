"""Local capability review with file integrity and exact source lines. No cloud calls."""
import hashlib,json,re
from pathlib import Path

_KEX_OBS_PATH=Path(__file__).resolve().parents[2]/'data/private/ssh_kex_completed_observation.json'

def load_kex_observation():
    """Load the manually-recorded SSH kex observation if it exists and is well-formed."""
    try:
        data=json.loads(_KEX_OBS_PATH.read_text(encoding='utf-8'))
        if not isinstance(data,dict):return None
        required={'kex','server_host_key_algorithm','host_identity_matches_known_hosts','newkeys_received','user_authentication_succeeded','assessment','source_type','external_services_used'}
        if not required.issubset(data):return None
        if data.get('external_services_used') is not False:return None
        return data
    except (OSError,ValueError,KeyError):return None

NAMES={'openssl_version.txt','openssl_providers.txt','openssl_kem.txt','openssl_signatures.txt','openssl_ciphers.txt','paquetes_cripto.txt','ssh_kex.txt','ssh_keys.txt','ssh_ciphers.txt','ssh_macs.txt','gnupg_version.txt','python_ssl.txt'}

def review_capture(folder):
    folder=Path(folder)
    path=folder/'manifest.json'
    if path.is_symlink() or path.stat().st_size>100000:raise ValueError('Manifest no válido.')
    manifest=json.loads(path.read_text(encoding='utf-8'))
    records=manifest.get('files',[])
    if manifest.get('kind')!='crypto_capabilities_v1' or manifest.get('schema_version')!=1 or manifest.get('vm') not in ('ASTRA-UBUNTU','ASTRA-KALI'):raise ValueError('Tipo de captura no admitido.')
    if len(records)!=len(NAMES) or {r.get('name') for r in records}!=NAMES:raise ValueError('Lista de archivos no válida.')
    observations=[];quality=[];pqc=[]
    for record in records:
        name=record['name'];file=folder/name
        if file.is_symlink() or file.stat().st_size>5*1024*1024:raise ValueError('Archivo no válido.')
        body=file.read_bytes()
        if len(body)!=record.get('size') or hashlib.sha256(body).hexdigest()!=record.get('sha256'):raise ValueError('Integridad no válida: '+name)
        usable=record.get('exit_code')==0 and record.get('truncated') is False
        quality.append({'file':name,'exit_code':record.get('exit_code'),'truncated':record.get('truncated'),'usable_for_findings':usable,'sha256':record['sha256']})
        if not usable:continue
        for number,line in enumerate(body.decode('utf-8',errors='replace').splitlines(),1):
            algorithms=[]
            for pattern,label in [(r'\bRSA\b','RSA'),(r'\bECDSA\b','ECDSA'),(r'\bED25519\b','Ed25519'),(r'\bX25519\b|\bcurve25519','X25519 / Curve25519'),(r'\bML[-_]?KEM(?:[-_]?\d+)?\b','ML-KEM'),(r'\bML[-_]?DSA(?:[-_]?\d+)?\b','ML-DSA'),(r'\bSLH[-_]?DSA\b','SLH-DSA')]:
                if re.search(pattern,line,re.I):algorithms.append(label)
            if algorithms:
                item={'source':name+':'+str(number),'evidence':line,'algorithms':algorithms,'meaning':'Capacidad enumerada; configuración y uso efectivo no verificados.'}
                observations.append(item)
                if any(a in ('ML-KEM','ML-DSA','SLH-DSA') for a in algorithms):pqc.append(item['source'])
    return {'schema_version':1,'vm':manifest['vm'],'capture_utc':manifest.get('capture_utc'),'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'integrity_verified':True,'external_services_used':False,'quality':quality,'observations':observations,'pqc_sources':pqc,'limitations':['Los hashes verifican consistencia con el manifiesto, no autenticidad del equipo origen.','Los listados muestran capacidades, no servicios configurados ni negociaciones reales.','Un comando fallido o truncado no demuestra ausencia de algoritmos.','No detectar ML-KEM, ML-DSA o SLH-DSA en estos archivos no demuestra su ausencia en todo el sistema.','Esta revisión no ejecuta primitivas PQC ni certifica resistencia cuántica.']}

def report_markdown(review,kex_obs=None):
    lines=['# AstraSec — Revisión criptográfica de captura real','','Equipo: '+review['vm'],'Fecha UTC de captura: '+str(review['capture_utc']),'Generación: análisis local determinista; sin envío a IBM.','SHA-256 del manifiesto: '+review['manifest_sha256'],'','## Resultado','Integridad de los archivos verificada respecto al manifiesto.','Observaciones de capacidad con fuente: '+str(len(review['observations'])),('Declaraciones PQC encontradas: '+', '.join(review['pqc_sources'])) if review['pqc_sources'] else 'No se identificaron declaraciones ML-KEM, ML-DSA o SLH-DSA en las salidas utilizables. Esto no demuestra ausencia en el sistema.','','## Calidad de la captura']
    for item in review['quality']:lines.append('- '+item['file']+': código '+str(item['exit_code'])+', truncado '+str(item['truncated'])+'. '+('Utilizable.' if item['usable_for_findings'] else 'Excluido de hallazgos; revisar o repetir el comando.'))
    lines+=['','## Observaciones con evidencia']
    for item in review['observations']:lines+=['','### '+item['source'],'Algoritmos: '+', '.join(item['algorithms']),item['evidence'],item['meaning']]
    if kex_obs is None:kex_obs=load_kex_observation()
    if kex_obs:
        lines+=['','## Prueba de intercambio SSH observada','','> Procedencia: '+kex_obs.get('source_type','manual')+' · '+kex_obs.get('source',''),'> Hash del archivo original verificado: '+str(kex_obs.get('original_file_hash_verified',False)),'> Servicio externo utilizado: '+str(kex_obs.get('external_services_used',False)),'']
        lines.append('Dirección: '+str(kex_obs.get('direction','')))
        lines.append('KEX seleccionado: `'+str(kex_obs.get('kex','')+'`'))
        lines.append('Clave de host del servidor: `'+str(kex_obs.get('server_host_key_algorithm','')+'`'))
        lines.append('Identidad del servidor coincide con known_hosts: '+str(kex_obs.get('host_identity_matches_known_hosts','')))
        lines.append('SSH2_MSG_NEWKEYS recibido: '+str(kex_obs.get('newkeys_received','')))
        lines.append('Autenticación del usuario completada: '+str(kex_obs.get('user_authentication_succeeded','')))
        if kex_obs.get('visible_lines'):
            lines+=['','Líneas visibles en la captura:']
            for vl in kex_obs['visible_lines']:lines.append('    '+vl)
        lines+=['','**Interpretación:** '+kex_obs.get('assessment',''),'','> Esta observación proviene de una captura de pantalla transcrita manualmente. No tiene hash de archivo original verificado. No acredita ML-KEM (FIPS 203), firmas poscuánticas ni seguridad integral.']
    lines+=['','## Recomendaciones','- Revisar servicios y configuraciones autorizados para determinar uso real de los algoritmos clásicos observados.','- Priorizar el inventario de firmas e intercambio de claves y confirmar criticidad y tiempo de confidencialidad.','- Ejecutar pruebas PQC en un entorno separado antes de proponer una migración.','','## Limitaciones']
    lines+=['- '+text for text in review['limitations']]
    return '\n'.join(lines)+'\n'
