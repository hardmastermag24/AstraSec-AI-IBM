"""Main-platform view of the authorized fixed-file IBM test."""
import json
import streamlit as st
from app.core import ibm_demo
from app.core.mascots import agent_activity, update_activity


def render():
    st.subheader('Prueba real de IBM con datos ficticios')
    st.info('Esta prueba usa el agente IBM existente y dos archivos ficticios fijos. Los archivos cargados en tu sesión y el historial no se envían.')
    try:
        sources = ibm_demo.sources()
        saved = ibm_demo.load_saved()
    except (OSError, ValueError, KeyError, TypeError):
        st.error('No se pudo verificar la prueba guardada o sus fuentes. Revisa la integridad antes de continuar.')
        return
    with st.expander('Ver los dos archivos que se enviarían a IBM'):
        for source in sources:
            st.write(source['id'] + ' · ' + source['archivo'])
            st.code(source['contenido'], language=None)
    failed = False
    with st.expander('Solicitar un nuevo análisis a IBM', expanded=False):
        st.caption('El resultado anterior ya está disponible abajo. Solo este botón inicia una nueva consulta y consumo del servicio.')
        consent = st.checkbox('Autorizar el envío de S1 y S2 a IBM Orchestrate', key='ibm_demo_consent')
        if st.button('Consultar de nuevo a IBM', disabled=not consent, key='ibm_demo_run', type='primary'):
            try:
                with agent_activity('advisor', 'IBM está analizando los dos archivos', 'Esperando la respuesta real de IBM Orchestrate.', completed='Respuesta real de IBM recibida'):
                    saved = ibm_demo.analyze(authorized=consent)
            except Exception:
                failed = True
                st.error('IBM no devolvió un análisis válido o no se pudo guardar. Se conserva el resultado anterior; no se sustituye por una respuesta demo.')
    if not saved:
        st.info('Todavía no hay resultado. Revisa los archivos y autoriza una consulta para ejecutar esta prueba.')
        return
    st.success('Resultado real de IBM recuperado. Abrir esta página o cambiar de sección no repite la consulta.')
    if failed:
        update_activity('advisor', 'error', 'No se completó la consulta nueva', 'Se muestra el resultado IBM anterior; no se ha sustituido por una respuesta demo.')
    else:
        update_activity('advisor', 'done', 'Análisis IBM disponible', 'Dos fuentes ficticias · consulta real archivada · revisión humana pendiente.')
    st.caption('Proveedor utilizado: ' + saved['provider'] + ' · Agente: ' + saved['agent'])
    st.caption('Consulta del ' + saved['timestamp_utc'] + ' · ' + str(saved['elapsed_seconds']) + ' segundos')
    labels = {'hechos': 'Hechos en las fuentes ficticias', 'hipotesis': 'Hipótesis no confirmadas', 'recomendaciones': 'Recomendaciones de IBM', 'limitaciones': 'Limitaciones'}
    refs = {source['id']: source['archivo'] for source in sources}
    for key, label in labels.items():
        st.subheader(label)
        for item in saved['analysis'][key]:
            st.write('• ' + item['texto'])
            if item['fuentes']:
                st.caption('Fuentes: ' + ' · '.join(refs[sid] for sid in item['fuentes']))
    st.caption('Formato y referencias validados; esto no certifica exactitud, seguridad ni revisión humana. Este resultado no se incorpora al expediente real.')
    st.download_button('Descargar análisis IBM y trazabilidad JSON', json.dumps(saved, ensure_ascii=False, indent=2).encode('utf-8'), file_name='AstraSec_AI_Prueba_IBM_Ficticia.json', mime='application/json')
