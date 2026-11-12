"""PQC inventory, IBM interpretation and synthetic COS archive UI."""
import json
import streamlit as st
from app.core.mascots import agent_activity
from app.core.pqc import synthetic_inventory, assess_inventory, pqc_messages, build_archive
from app.core.cos_archive import cos_status, archive_synthetic_pqc
from app.core.agent import OrchestrateProvider
from app.core.report_pdf import generate_pdf


def render_pqc():
    from app.core.real_capture_ui import render_real_capture
    render_real_capture()
    if st.session_state.get('pqc_policy_version') != 2:
        st.session_state.pop('pqc_ibm', None)
        st.session_state.pqc_policy_version = 2
    st.subheader('Preparación para criptografía poscuántica')
    st.caption('Inventario → clasificación local → interpretación IBM → reporte → archivo COS con SHA-256')
    st.info('Los logs generales de Ubuntu no bastan para evaluar criptografía. Este módulo analiza declaraciones de un inventario; no ejecuta algoritmos ni certifica resistencia cuántica.')
    raw=st.text_area('Inventario criptográfico JSON (evaluación local)',json.dumps(synthetic_inventory(),ensure_ascii=False,indent=2),height=220)
    if st.button('Evaluar inventario localmente'):
        st.session_state.pop('pqc_local',None)
        try:
            if len(raw)>500000: raise ValueError('Inventario demasiado grande.')
            st.session_state.pqc_local=assess_inventory(json.loads(raw))
        except (ValueError,TypeError):
            st.error('JSON no válido. Cada activo requiere id, algorithm, purpose, source y evidence. No incluyas claves privadas.')
    local=st.session_state.get('pqc_local')
    if local:
        st.write('Datos sintéticos' if local['synthetic'] else 'Declaraciones del inventario; uso efectivo no verificado')
        for asset in local['assets']:
            with st.expander(asset['id']+' · '+asset['status'],expanded=True):
                st.text('Algoritmo: '+asset['algorithm']+' | Uso: '+asset['purpose'])
                st.text(asset['assessment'])
                st.text('Fuente declarada: '+asset['source'])
                st.text('Referencia normativa: '+asset['reference'])
    st.subheader('Interpretación con IBM Orchestrate')
    st.caption('El botón siguiente siempre usa el caso sintético fijo, aunque edites el inventario de arriba. No envía archivos reales ni historial.')
    with st.expander('Vista previa del caso PQC enviado a IBM'):
        for msg in pqc_messages():st.text(msg['role']+': '+msg['content'])
    if st.button('Analizar caso PQC sintético con IBM',type='primary'):
        st.session_state.pop('pqc_ibm',None)
        try:
            with agent_activity("quantum", "Consultando IBM", "Esperando respuesta del proveedor autorizado.", completed="Consulta finalizada"):
                st.session_state.pqc_ibm=OrchestrateProvider().analyze_pqc_synthetic()
        except Exception:
            st.error('No se obtuvo un análisis válido de IBM; no se generó un reporte nuevo. Revisar configuración o disponibilidad.')
    result=st.session_state.get('pqc_ibm')
    if result:
        st.success('Respuesta IBM con secciones y fuentes válidas; requiere revisión técnica.')
        md='# AstraSec - Evaluación PQC sintética\n\nProveedor: IBM watsonx Orchestrate, agente astrasec_pqc.\n\n'
        refs={'S1':'inventario_sintetico.json','S2':'clasificacion_local_y_referencias_NIST'}
        for key,label in [('hechos','Hechos observados'),('hipotesis','Hipótesis no confirmadas'),('recomendaciones','Recomendaciones'),('limitaciones','Limitaciones')]:
            st.subheader(label);md+='## '+label+'\n\n'
            for item in result[key]:
                line=item['texto']+' [Fuentes: '+', '.join(refs[x] for x in item['fuentes'])+']'
                st.text('• '+line);md+='- '+line+'\n'
        md+='\n## Referencias\n\nhttps://csrc.nist.gov/pubs/fips/203/final\nhttps://csrc.nist.gov/pubs/fips/204/final\nhttps://csrc.nist.gov/pubs/fips/205/final\n\nDatos sintéticos. No es una certificación ni benchmark.\n'
        st.download_button('Descargar reporte PQC PDF',generate_pdf(md),file_name='astrasec_pqc_sintetico.pdf',mime='application/pdf')
        st.download_button('Descargar reporte PQC Markdown',md,file_name='astrasec_pqc_sintetico.md',mime='text/markdown')
        st.download_button('Descargar análisis PQC JSON',json.dumps(result,ensure_ascii=False,indent=2),file_name='astrasec_pqc_sintetico.json',mime='application/json')
    st.subheader('Archivo de evaluación en IBM Cloud Object Storage')
    body,digest=build_archive()
    st.caption('COS conserva el inventario sintético fijo y su evaluación local, con clave derivada del contenido y verificación de lectura. No se suben claves, logs, PDF ni inventarios editados.')
    st.text('SHA-256 del paquete: '+digest)
    st.download_button('Descargar paquete PQC para archivo',body,file_name='paquete_pqc_sintetico.json',mime='application/json')
    status=cos_status()
    if not all(status.values()):
        st.warning('COS pendiente de configuración: instancia, bucket, endpoint y credencial de servicio. No se ha realizado una subida real.')
        st.text('Variables pendientes: '+', '.join(k for k,v in status.items() if not v))
    if st.button('Archivar caso PQC sintético en COS y verificar',disabled=not all(status.values())):
        try:
            receipt=archive_synthetic_pqc();st.session_state.pqc_cos_receipt=receipt
            st.success('Objeto escrito y SHA-256 comprobado por lectura desde COS.')
        except (ValueError,RuntimeError) as exc:st.error(str(exc))
    if st.session_state.get('pqc_cos_receipt'):st.json(st.session_state.pqc_cos_receipt)
