"""Operational readiness panel. Configured never means connected or production approved."""
import json,os
import streamlit as st
from app.core.ibm_services import readiness,archive_synthetic_cloudant,analyze_synthetic_runtime,synthetic_voice_roundtrip
from app.core.evaluation import evaluation_bundle


def render_operations():
    lab_mode=os.environ.get("ASTRASEC_LAB_MODE","1").strip().lower() not in {"0","false","no"}
    st.subheader('Operación e integraciones del piloto')
    st.caption('Estado de configuración, pruebas sintéticas y resultados de conexión. No se envían evidencias reales desde estos controles.')
    from app.core.connection_receipts import connection_results
    verified=connection_results()
    states=readiness()
    for name,status in states.items():
        if lab_mode and name=='watsonx.ai Runtime':
            st.text('watsonx.ai Runtime: fuera del alcance del laboratorio; recibo de restricción conservado. No requiere ampliar IAM.')
        else:
            st.text(name+': '+verified.get(name,('Configurado; conexión no verificada' if status['configured'] else 'Pendiente: '+', '.join(status['missing']))))
    if st.button('Probar persistencia sintética Cloudant',disabled=not states['Cloudant']['configured']):
        try:st.session_state.cloudant_probe=archive_synthetic_cloudant()
        except (ValueError,RuntimeError):st.error('No se verificó Cloudant. Revisar base, endpoint y permisos.')
    if st.session_state.get('cloudant_probe'):st.json(st.session_state.cloudant_probe)
    if st.button('Segunda opinión PQC sintética con Runtime',disabled=lab_mode or not states['watsonx.ai Runtime']['configured']):
        st.session_state.pop('runtime_probe',None)
        try:st.session_state.runtime_probe=analyze_synthetic_runtime()
        except (ValueError,RuntimeError,ImportError):st.error('No se completó la prueba opcional. Revisa dependencias, acceso y configuración.')
    if st.session_state.get('runtime_probe'):
        st.caption('Segunda opinión sintética; no sustituye revisión técnica ni modifica los hallazgos del caso.')
        st.json(st.session_state.runtime_probe)
    if st.button('Probar voz sintética TTS → STT',disabled=not (states['Text to Speech']['configured'] and states['Speech to Text']['configured'])):
        try:st.session_state.voice_probe=synthetic_voice_roundtrip()
        except (ValueError,RuntimeError,ImportError):st.error('No se completó la prueba opcional. Revisa dependencias, acceso y configuración.')
    if st.session_state.get('voice_probe'):
        result=st.session_state.voice_probe;st.audio(result['audio'],format='audio/wav');st.text(result['transcript'])
    body,digest=evaluation_bundle()
    result=json.loads(body)
    st.text('Evaluación local reproducible: '+str(result['passed'])+'/'+str(result['total'])+' controles. No es evaluación remota de Governance.')
    st.download_button('Exportar paquete para revisión Governance / Studio',body,file_name='astrasec_evaluacion_local.json',mime='application/json')
    st.caption('Integraciones opcionales. En el laboratorio, Runtime, Studio y Governance no son requisitos. La prueba Runtime está deshabilitada en modo laboratorio. Los recibos previos son históricos; el flujo local permanece disponible.')
    st.text('Modo actual: '+os.environ.get('ASTRASEC_MODE','local'))
