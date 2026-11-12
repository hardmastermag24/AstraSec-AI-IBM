"""Explicit PQC save/recovery, review and download controls for the local pilot."""
import hashlib
import json
from pathlib import Path
import streamlit as st
from app.core.mascots import agent_activity
from app.core.case_store import CaseStore, canonical
from app.core.pqc_workflow import (QUESTION, DECISIONS, capture_summary, create_record,
    attach_plan, checked_plan, digest, register_review, validate_record, status, export_bundle)
from app.core.real_ibm_advice import analyze_real_capabilities, ACTIONS

PRIVATE = Path(__file__).resolve().parents[2]/'data/private'


def render_integrated_report():
    """Reports navigation can recover a saved dossier without a general lab session."""
    from app.core.real_capture import review_capture
    store = CaseStore(PRIVATE/'pqc_cases.sqlite3')
    cases = store.list()
    st.subheader('Reporte del expediente PQC')
    if cases:
        labels = {c['id']:c['name']+' · revisión '+str(c['revision']) for c in cases}
        chosen = st.selectbox('Expediente PQC guardado para reportar', list(labels), format_func=labels.get)
        if st.button('Abrir reporte PQC guardado'):
            try:
                record, revision = store.load(chosen)
                folder = record['capture']['folder']
                review = review_capture(PRIVATE.parent/'evidencias'/folder)
                validate_record(record, review, folder)
                st.session_state.pqc_workflow = record
                st.session_state.pqc_workflow_revision = revision
                st.session_state.pqc_workflow_receipt = {'case_id':chosen, 'revision':revision, 'sha256':hashlib.sha256(canonical(record)).hexdigest()}
            except (OSError, ValueError, KeyError, TypeError):
                st.error('No se abrió el reporte: captura ausente, alterada o expediente incompatible.')
    record = st.session_state.get('pqc_workflow')
    receipt = st.session_state.get('pqc_workflow_receipt')
    if not record or not receipt:
        st.info('En Agente > Criptografía poscuántica verifica la captura y guarda el expediente, o recupera uno guardado aquí.')
        return False
    try:
        folder = record['capture']['folder']
        validate_record(record, review_capture(PRIVATE.parent/'evidencias'/folder), folder)
        bundle, pdf, markdown = export_bundle(record, receipt)
    except (OSError, ValueError, KeyError, TypeError):
        st.warning('La versión actual no coincide con el expediente guardado o la captura. Verifica y guarda antes de exportar.')
        return False
    st.info(status(record))
    st.caption('Expediente '+record['case_id']+' · revisión '+str(receipt['revision'])+' · '+folder)
    stem = 'AstraSec_PQC_'+record['case_id']+'_r'+str(receipt['revision'])
    st.download_button('Descargar expediente PQC ZIP', bundle, file_name=stem+'.zip', mime='application/zip')
    st.download_button('Descargar reporte PQC integrado PDF', pdf, file_name=stem+'.pdf', mime='application/pdf')
    st.download_button('Descargar reporte PQC integrado Markdown', markdown, file_name=stem+'.md', mime='text/markdown')
    with st.expander('Vista previa del reporte integrado'):st.text(markdown)
    return True


def render_workflow(review, folder, archived_plan=None):
    summary = capture_summary(review, folder)
    st.subheader('Expediente PQC · de la evidencia a la decisión')
    st.caption('Captura verificada → plan vinculado → revisión → guardado → reporte y evidencias. Las flechas representan pasos de la aplicación; el agente no ejecuta acciones en las VM.')
    st.write(QUESTION)
    record = st.session_state.get('pqc_workflow')
    if not record or record['capture'] != summary:
        record = create_record(review, folder)
        st.session_state.pqc_workflow = record
        st.session_state.pqc_workflow_receipt = None
        st.session_state.pqc_workflow_revision = 0
    # Only validated artifacts for this precise capture can enter the dossier.
    candidates = [st.session_state.get('pqc_real_ibm'), archived_plan]
    for candidate in candidates:
        if not candidate:continue
        try:
            checked_plan(candidate, summary)
            if not record['ibm_plan']:
                record = attach_plan(record, candidate)
                st.session_state.pqc_workflow = record
            break
        except (ValueError, KeyError, TypeError):
            st.caption('Se omitió un plan incompatible con esta captura o con sus fuentes.')
    try:validate_record(record, review, folder)
    except (ValueError, KeyError, TypeError):
        st.error('Expediente incompatible. Vuelve a verificar la captura antes de continuar.')
        return
    st.info(status(record))
    st.code('Caso: '+record['case_id']+'\nCaptura: '+folder+'\nResumen SHA-256: '+summary['payload_sha256'], language=None)
    with st.expander('Plan IBM y fuentes del mismo caso', expanded=True):
        if record['ibm_plan']:
            st.success('Plan archivado validado: hash, fuentes y acciones coinciden. No se ha repetido la consulta IBM.')
            refs = {s['id']:s['source'] for s in summary['payload']['sources']}
            for action in record['ibm_plan']['plan']['actions']:
                st.write(ACTIONS[action['action']])
                st.caption('Fuentes: '+', '.join(s+' · '+refs[s] for s in action['sources']))
        else:st.warning('No hay un plan IBM válido para esta captura. Puedes guardar un borrador local.')
    with st.expander('Consulta nueva opcional a IBM · revisar contenido antes de autorizar'):
        st.caption('Solo se enviará el resumen minimizado que se muestra. Sin logs brutos, archivos de sesión ni historial. Reutilizar el plan archivado evita consumo adicional.')
        st.json(summary['payload'])
        consent = st.checkbox('Autorizar únicamente este resumen a IBM Orchestrate', key='pqc_consent_'+summary['payload_sha256'])
        if st.button('Solicitar un plan IBM nuevo', disabled=not consent):
            try:
                with agent_activity("quantum", "Consultando IBM", "Esperando respuesta del proveedor autorizado.", completed="Consulta finalizada"):
                    result = analyze_real_capabilities(review)
                    next_record = attach_plan(record, result)
                    # Preserve older plans; never silently replace the historical artifact.
                    history = PRIVATE/'pqc_plans'
                    history.mkdir(parents=True, exist_ok=True)
                    (history/(digest(result)+'.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
                    record = next_record
                    st.session_state.pqc_workflow = record
                    st.session_state.pqc_real_ibm = result
                st.success('Plan nuevo validado y conservado. Revisa de nuevo y guarda una revisión del expediente.')
            except Exception:
                st.error('No se obtuvo un plan válido. Se conserva el expediente previo; no se inventó un resultado alternativo.')
    key = record['case_id']+'_'+(digest(record['ibm_plan']) if record['ibm_plan'] else 'sin_plan')
    with st.expander('Revisión y decisión · obligatoria antes de declarar revisión humana'):
        current = record.get('review') or {}
        if current:
            st.write('Revisión registrada: '+current['reviewer']+' · '+current['decision'])
            st.caption('Revisión humana declarada' if current['kind']=='human' else 'Ensayo técnico; revisión humana pendiente')
        with st.form('pqc_review_'+key):
            kind = st.selectbox('Tipo de revisión', ['Revisión humana', 'Ensayo técnico (no aprobación humana)'])
            reviewer = st.text_input('Responsable de esta revisión', max_chars=120)
            decision = st.selectbox('Decisión sobre el plan', DECISIONS)
            notes = st.text_area('Justificación, faltantes y siguiente paso', max_chars=4000)
            confirmed = st.checkbox('He contrastado las fuentes y entiendo que el plan no ejecuta cambios ni certifica seguridad PQC')
            submitted = st.form_submit_button('Registrar revisión del expediente', disabled=not record['ibm_plan'])
        if submitted:
            try:
                if not confirmed:raise ValueError('Confirma la revisión de fuentes antes de registrarla.')
                record = register_review(record, reviewer, decision, notes, human=kind=='Revisión humana')
                st.session_state.pqc_workflow = record
                st.success('Revisión registrada. Guarda el expediente para conservarla.')
            except ValueError as exc:st.error(str(exc))
    store = CaseStore(PRIVATE/'pqc_cases.sqlite3')
    with st.expander('Guardar o recuperar expediente PQC', expanded=True):
        st.caption('Repositorio PQC local con revisiones. No modifica los casos generales del laboratorio ni envía datos a la nube.')
        if st.button('Guardar expediente PQC en este equipo'):
            try:
                validate_record(record, review, folder)
                if not store.verify_audit():raise ValueError('Auditoría local no válida.')
                receipt = store.save(record, record['case_id'], st.session_state.get('pqc_workflow_revision', 0))
                st.session_state.pqc_workflow_receipt = receipt
                st.session_state.pqc_workflow_revision = receipt['revision']
                st.success('Expediente PQC guardado · revisión '+str(receipt['revision']))
            except (ValueError, KeyError, TypeError):st.error('No se guardó: revisar integridad o conflicto de revisión. Recupera la versión actual antes de sobrescribir.')
        cases = store.list()
        if cases:
            labels = {c['id']:c['name']+' · revisión '+str(c['revision']) for c in cases}
            selected = st.selectbox('Expediente PQC a recuperar', list(labels), format_func=labels.get)
            if st.button('Recuperar expediente PQC'):
                try:
                    recovered, revision = store.load(selected)
                    validate_record(recovered, review, folder)
                    st.session_state.pqc_workflow = recovered
                    st.session_state.pqc_workflow_revision = revision
                    st.session_state.pqc_workflow_receipt = {'case_id':selected, 'revision':revision, 'sha256':hashlib.sha256(canonical(recovered)).hexdigest()}
                    st.rerun()
                except (ValueError, KeyError, TypeError):st.error('No se recuperó: verifica primero la misma captura; revisa integridad y versión.')
    receipt = st.session_state.get('pqc_workflow_receipt')
    if receipt and receipt['sha256'] == hashlib.sha256(canonical(record)).hexdigest():
        bundle, pdf, markdown = export_bundle(record, receipt)
        stem = 'AstraSec_PQC_'+record['case_id']+'_r'+str(receipt['revision'])
        st.subheader('Descargar expediente guardado · revisión '+str(receipt['revision']))
        st.caption(status(record)+'. El ZIP contiene PDF, Markdown, JSON, traza y manifiesto SHA-256; omite logs brutos y credenciales.')
        st.download_button('Descargar expediente PQC ZIP', bundle, file_name=stem+'.zip', mime='application/zip')
        st.download_button('Descargar reporte PQC integrado PDF', pdf, file_name=stem+'.pdf', mime='application/pdf')
        st.download_button('Descargar reporte PQC integrado Markdown', markdown, file_name=stem+'.md', mime='text/markdown')
        with st.expander('Traza observable del expediente'):st.json(record['trace'])
    else:st.caption('Guarda la versión actual del expediente para habilitar sus descargas integradas.')
