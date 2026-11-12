"""Isolated UI for validating IBM using fixed synthetic data."""
import json
import streamlit as st
from app.core.mascots import agent_activity
from app.core.agent import OrchestrateProvider
from app.core.synthetic_agent import synthetic_chunks, synthetic_messages, report_lines, CASE_NAME
from app.core.lab import Laboratory
from app.core.ingest import IngestedDocument
from app.core.report import generate_report
from app.core.report_pdf import generate_pdf


def render_synthetic():
    st.subheader('AstraSec · validación con IBM')
    st.caption('Fuentes sintéticas → IBM Orchestrate → validación de estructura y fuentes → reporte PDF / Markdown')
    st.info('Esta prueba usa exclusivamente dos fuentes ficticias incluidas en la aplicación. Los archivos reales cargados y el historial no se envían a IBM.')
    with st.expander('Ver exactamente qué se enviará a IBM'):
        for msg in synthetic_messages():
            st.text(msg['role'] + ': ' + msg['content'])
    if st.button('🤖 Analizar caso sintético con IBM', type='primary'):
        st.session_state.pop('synthetic_analysis', None)
        try:
            with agent_activity("advisor", "Consultando IBM", "Esperando respuesta del proveedor autorizado.", completed="Consulta finalizada"):
                result = OrchestrateProvider().analyze_synthetic()
                st.session_state.synthetic_analysis = result
        except Exception as exc:
            st.error(str(exc) if isinstance(exc, (RuntimeError, ValueError, EnvironmentError)) else 'No se pudo completar el análisis. Revisar la conexión y configuración de IBM.')
    result = st.session_state.get('synthetic_analysis')
    if not result:
        return
    st.success('IBM devolvió un análisis con estructura y referencias válidas. El contenido requiere revisión del analista.')
    for key, label in [('hechos','Hechos observados'), ('hipotesis','Hipótesis no confirmadas'), ('recomendaciones','Recomendaciones'), ('limitaciones','Limitaciones')]:
        st.subheader(label)
        for line in report_lines(result[key]):
            st.text('• ' + line)
    chunks = synthetic_chunks()
    lab = Laboratory(name=CASE_NAME, description='Validación de integración con datos completamente sintéticos.', analyst='Validación técnica', scope='Solo los dos documentos ficticios incluidos; no representa el laboratorio real.')
    docs = [IngestedDocument(r.chunk.source, 'txt', r.chunk.text, [r.chunk]) for r in chunks]
    md = generate_report(lab, docs, report_lines(result['hechos']), report_lines(result['hipotesis']), report_lines(result['recomendaciones']), report_lines(result['limitaciones']), analyst_notes='DATOS SINTÉTICOS. Respuesta de IBM con validación estructural y referencias; esa validación no certifica la veracidad de cada afirmación.', ai_provider='IBM watsonx Orchestrate (consulta real, datos sintéticos)')
    st.download_button('⬇️ Descargar validación PDF', generate_pdf(md), file_name='validacion_agente_sintetico.pdf', mime='application/pdf')
    st.download_button('⬇️ Descargar validación Markdown', md, file_name='validacion_agente_sintetico.md', mime='text/markdown')
    st.download_button('⬇️ Descargar análisis JSON', json.dumps(result, ensure_ascii=False, indent=2), file_name='validacion_agente_sintetico.json', mime='application/json')
    st.caption('La prueba no modifica los hallazgos ni el reporte de ASTRA-UBUNTU. El envío de evidencias reales sigue bloqueado.')
