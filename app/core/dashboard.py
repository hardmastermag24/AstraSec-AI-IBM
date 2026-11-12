"""Live local operations dashboard. Receipts are historical, never uptime claims."""
import datetime,json,os
from pathlib import Path
import streamlit as st
from app.core.case_store import CaseStore
from app.core.connection_receipts import connection_results

ROOT=Path(__file__).resolve().parents[2]

def read(name):
    try:return json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))
    except (OSError,ValueError):return {}

def go(page):st.session_state.nav_page=page

@st.fragment(run_every='15s')
def live_overview():
    now=datetime.datetime.now().astimezone()
    st.caption('ACTUALIZACIÓN LOCAL · '+now.strftime('%H:%M:%S %Z')+' · intervalo 15 s · sin consultas de red ni consumo IBM automático')
    store=CaseStore(ROOT/'data/private/cases.sqlite3');cases=store.list()
    captures=sorted((ROOT/'data/evidencias').glob('CRIPTO_*/manifest.json'),reverse=True)
    connections=connection_results();plan=read('private/real_ibm_plan.json');kex=read('private/ssh_kex_completed_observation.json')
    verified=sum(1 for name in ('COS','Cloudant','Text to Speech','Speech to Text') if name in connections)
    cols=st.columns(4)
    cols[0].metric('Casos conservados',len(cases))
    cols[1].metric('Capturas disponibles',len(captures))
    cols[2].metric('Pruebas IBM registradas',verified,help='COS, Cloudant y voz. Éxitos anteriores; no verifica disponibilidad actual.')
    cols[3].metric('Acciones del plan real',len(plan.get('plan',{}).get('actions',[])))
    st.write('')
    left,right=st.columns([1.6,1],gap='large')
    with left:
        with st.container(border=True):
            st.subheader('Entorno observado')
            st.caption('Inventario derivado de capturas. Estado de encendido de las VM no monitorizado.')
            rows=[]
            for path in captures:
                try:
                    m=json.loads(path.read_text(encoding='utf-8'))
                    failed=sum(x.get('exit_code')!=0 or x.get('truncated') is True for x in m.get('files',[]))
                    rows.append({'Activo':m.get('vm','Desconocido'),'Captura UTC':m.get('capture_utc','Sin fecha'),'Archivos':len(m.get('files',[])),'Revisar':failed,'Origen':'Captura histórica'})
                except (OSError,ValueError,TypeError):continue
            if rows:st.dataframe(rows,hide_index=True,width='stretch')
            else:st.info('Recibe una captura para incorporar un activo al entorno.')
        with st.container(border=True):
            st.subheader('Validación criptográfica')
            if kex.get('newkeys_received') and kex.get('host_identity_matches_known_hosts'):
                st.success('Intercambio SSH completado · identidad del servidor comprobada')
                st.code(kex.get('kex',''),language=None)
                st.caption('Ubuntu → Kali · evidencia de captura transcrita · autenticación del usuario no realizada. No acredita ML-KEM ni seguridad integral.')
            else:st.info('Aún no hay una prueba de intercambio completado registrada.')
            st.caption('Capacidad disponible → política configurada → intercambio observado. Cada nivel requiere su propia evidencia.')
        with st.container(border=True):
            st.subheader('Actividad del caso')
            if cases:
                st.dataframe([{'Laboratorio':x['name'],'Revisión':x['revision'],'Guardado UTC':x['updated']} for x in cases[:8]],hide_index=True,width='stretch')
            else:st.caption('Sin casos guardados todavía.')
            if store.verify_audit():st.caption('● Cadena local de auditoría consistente')
            else:st.error('La auditoría presenta inconsistencias. Revisar antes de continuar.')
    with right:
        with st.container(border=True):
            st.subheader('Servicios IBM')
            for name in ('COS','Cloudant','Text to Speech','Speech to Text','watsonx.ai Runtime'):
                st.markdown('**'+name+'**')
                message=connections.get(name,'Sin prueba registrada')
                if name=='watsonx.ai Runtime' and os.environ.get('ASTRASEC_LAB_MODE','1').strip().lower() not in {'0','false','no'}:st.caption('Fuera del alcance del laboratorio; no requiere ampliación IAM. Recibo de restricción conservado.')
                elif 'Bloqueado' in message:st.warning(message)
                else:st.caption(('● ' if name in connections else '○ ')+message)
            st.markdown('**Orchestrate · plan real**')
            st.caption('● Respuesta validada y archivada' if plan.get('plan') else '○ Sin plan real archivado')
            st.markdown('**Studio / Governance**')
            st.caption('○ Integraciones opcionales fuera del alcance obligatorio del laboratorio')
            st.caption('Estos estados proceden de recibos locales. No representan disponibilidad en vivo de IBM.')
        with st.container(border=True):
            st.subheader('Siguiente acción')
            actions={'verify_configured_use':'Comprobar el uso configurado','inventory_dependencies':'Inventariar dependencias','repeat_failed_collection':'Repetir la consulta fallida','plan_isolated_pqc_test':'Preparar pruebas aisladas'}
            for index,item in enumerate(plan.get('plan',{}).get('actions',[]),1):
                st.write(str(index)+'. '+actions.get(item.get('action'),'Revisar plan'))
                st.caption('Fuentes vinculadas: '+str(len(item.get('sources',[]))))
            st.caption('El plan IBM no ejecuta comandos ni cambia los sistemas.')

def render():
    st.markdown('<div class="console-eyebrow">AstraSec / Operaciones</div>',unsafe_allow_html=True)
    title,control=st.columns([4,1])
    with title:
        st.title('Resumen de operaciones')
        st.caption('Evidencias, integraciones y seguimiento de revisiones criptográficas.')
    with control:st.markdown('<span class="console-status">● Consola local activa</span>',unsafe_allow_html=True)
    st.markdown('<div class="console-rule"></div>',unsafe_allow_html=True)
    live_overview()
    pqc_store=CaseStore(ROOT/'data/private/pqc_cases.sqlite3')
    pqc_cases=pqc_store.list()
    if pqc_cases:
        st.subheader('Expedientes PQC conservados')
        st.caption(str(len(pqc_cases))+' expediente(s) PQC local(es). Su revisión y reporte integrado se recuperan en Reportes.')
    st.subheader('Continuar el trabajo')
    cols=st.columns(3)
    cols[0].button('01  Incorporar evidencias',on_click=go,args=('📂 Cargar archivos',),width='stretch')
    cols[1].button('02  Abrir agente PQC',on_click=go,args=('🤖 Agente',),type='primary',width='stretch')
    cols[2].button('03  Generar reporte',on_click=go,args=('📄 Generar reporte',),width='stretch')
