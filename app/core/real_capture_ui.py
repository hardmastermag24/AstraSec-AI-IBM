"""Local verified capture review controls."""
import hashlib
import json
from pathlib import Path
import streamlit as st
from app.core.real_capture import review_capture,report_markdown,load_kex_observation
from app.core.report_pdf import generate_pdf

_SAVED_PLAN=Path(__file__).resolve().parents[2]/'data/private/real_ibm_plan.json'


def _load_saved_plan():
    try:
        data=json.loads(_SAVED_PLAN.read_text(encoding='utf-8'))
        if isinstance(data,dict) and 'plan' in data and 'sources' in data:return data
    except (OSError,ValueError):pass
    return None


def render_real_capture():
    st.subheader('Capturas criptográficas reales · revisión local')
    base=Path(__file__).resolve().parents[2]/'data/evidencias'
    folders=sorted((p for p in base.glob('CRIPTO_*') if p.is_dir() and not p.is_symlink()),reverse=True)
    if not folders:
        st.info('No hay capturas criptográficas locales recibidas.');return
    selected=st.selectbox('Captura a revisar',[p.name for p in folders])
    if st.button('Verificar captura y generar revisión local'):
        st.session_state.pop('pqc_real_capture',None)
        st.session_state.pop('pqc_capture_folder',None)
        try:
            st.session_state.pqc_real_capture=review_capture(base/selected)
            st.session_state.pqc_capture_folder=selected
        except (OSError,ValueError,KeyError,TypeError):st.error('Captura incompleta, incompatible o con integridad no válida. No se generaron hallazgos.')
    review=st.session_state.get('pqc_real_capture')
    if not review:return
    if st.session_state.get('pqc_capture_folder')!=selected:
        st.info('Verifica la captura seleccionada antes de continuar; la revisión anterior pertenece a otra selección.')
        return
    st.caption('Resultado guardado para '+review['vm']+' · '+str(review['capture_utc'])+'. No se envió evidencia a IBM.')
    st.success('Hashes verificados respecto al manifiesto. Uso real de los algoritmos pendiente de comprobar.')
    st.dataframe(review['quality'],hide_index=True)

    from app.core.pqc_workflow_ui import render_workflow
    render_workflow(review, selected, archived_plan=_load_saved_plan())

    # ---- Observación SSH ----
    kex=load_kex_observation()
    if kex:
        st.subheader('Archivo histórico · observación SSH independiente')
        st.caption('Esta observación no forma parte de la captura seleccionada ni de su informe local.')
        src_type=kex.get('source_type','desconocido')
        hash_ok=kex.get('original_file_hash_verified',False)
        if hash_ok:
            st.success('Intercambio '+kex['kex']+' completado · identidad del servidor verificada.')
        else:
            st.info('Intercambio '+kex['kex']+' observado · evidencia por transcripción manual, sin hash de archivo original.')
        col1,col2=st.columns(2)
        col1.metric('KEX seleccionado',kex.get('kex','—'))
        col2.metric('Clave host servidor',kex.get('server_host_key_algorithm','—'))
        col1.metric('known_hosts coincide',str(kex.get('host_identity_matches_known_hosts','')))
        col2.metric('NEWKEYS recibido',str(kex.get('newkeys_received','')))
        col1.metric('Autenticación usuario',str(kex.get('user_authentication_succeeded','')))
        with st.expander('Líneas visibles en la captura'):
            for vl in kex.get('visible_lines',[]):st.code(vl,language=None)
        st.caption(kex.get('assessment',''))
        st.caption('Procedencia: '+src_type+' · '+kex.get('source','')+'  |  Hash archivo verificado: '+str(hash_ok)+'  |  Servicio externo: '+str(kex.get('external_services_used',False)))
        st.caption('sntrup761 + X25519 es intercambio híbrido poscuántico; no es ML-KEM (FIPS 203). No acredita firmas PQC ni seguridad integral.')

    # ---- Observaciones de capacidad ----
    st.write('Observaciones de capacidad: '+str(len(review['observations'])))
    failed=[q for q in review['quality'] if not q['usable_for_findings']]
    if failed:
        with st.expander('⚠️ Archivos excluidos de hallazgos (comando fallido o truncado) — '+str(len(failed))):
            for q in failed:
                st.text(q['file']+' · exit_code '+str(q['exit_code'])+' · truncado '+str(q['truncated']))
            st.caption('Un comando fallido no demuestra ausencia del algoritmo. Repetir el comando corregido.')
    if st.checkbox('Mostrar detalle de observaciones de capacidad'):
        for item in review['observations']:
            with st.expander(item['source']+' · '+', '.join(item['algorithms'])):
                st.code(item['evidence'],language=None);st.caption(item['meaning'])
    for item in review['limitations']:st.caption(item)
    md=report_markdown(review,kex_obs={})
    st.download_button('Descargar revisión real PDF',generate_pdf(md),file_name='astrasec_captura_real.pdf',mime='application/pdf')
    st.download_button('Descargar revisión real JSON',json.dumps(review,ensure_ascii=False,indent=2),file_name='astrasec_captura_real.json',mime='application/json')
    st.download_button('Descargar revisión real Markdown',md,file_name='astrasec_captura_real.md',mime='text/markdown')
