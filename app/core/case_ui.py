"""Explicit case save/restore for the private local pilot; no cloud transmission."""
from dataclasses import asdict
from pathlib import Path
import streamlit as st
from app.core.case_store import CaseStore, ConflictError
from app.core.lab import Laboratory
from app.core.ingest import IngestedDocument,DocumentChunk

FIELDS=('conversation','findings','hypotheses','recommendations','limitations','analyst_notes')


def snapshot(state):
    return {'schema_version':1,'lab':asdict(state.lab),'documents':{name:asdict(doc) for name,doc in state.documents.items()},**{key:state[key] for key in FIELDS},'pqc_local':state.get('pqc_local'),'pqc_ibm':state.get('pqc_ibm'),'pqc_real_capture':state.get('pqc_real_capture'),'pqc_real_ibm':state.get('pqc_real_ibm')}


def restore(data):
    if data.get('schema_version')!=1:raise ValueError('Versión de caso no admitida.')
    lab=Laboratory.from_dict(data['lab'])
    documents={}
    for name,item in data['documents'].items():
        chunks=[DocumentChunk(**chunk) for chunk in item['chunks']]
        documents[name]=IngestedDocument(item['filename'],item['file_type'],item['full_text'],chunks,item['error'])
    return {'lab':lab,'documents':documents,**{key:data[key] for key in FIELDS},'pqc_local':data.get('pqc_local'),'pqc_ibm':data.get('pqc_ibm'),'pqc_real_capture':data.get('pqc_real_capture'),'pqc_real_ibm':data.get('pqc_real_ibm')}


def render_case_controls():
    store=CaseStore(Path(__file__).resolve().parents[2]/'data/private/cases.sqlite3')
    with st.expander('Casos guardados · piloto local'):
        st.caption('Guardado explícito en este equipo. No se envía a IBM. Para cambiar de caso, guarda primero el actual.')
        if st.button('Guardar caso en este equipo',disabled=st.session_state.lab is None):
            try:
                if not store.verify_audit():raise ValueError('Registro de auditoría alterado; revisar antes de guardar.')
                receipt=store.save(snapshot(st.session_state),st.session_state.get('case_id'),st.session_state.get('case_revision',0))
                st.session_state.case_id=receipt['case_id'];st.session_state.case_revision=receipt['revision']
                st.success('Caso guardado. Revisión '+str(receipt['revision']))
            except (ValueError,TypeError):st.error('No se pudo guardar: revisar integridad, tamaño y conflictos de revisión.')
        cases=store.list()
        if cases:
            labels={case['id']:case['name']+' · revisión '+str(case['revision']) for case in cases}
            selected=st.selectbox('Caso a recuperar',list(labels),format_func=labels.get)
            if st.button('Recuperar caso guardado'):
                try:
                    if not store.verify_audit():raise ValueError('Auditoría alterada')
                    data,revision=store.load(selected)
                    values=restore(data)
                    for key,value in values.items():st.session_state[key]=value
                    st.session_state.case_id=selected;st.session_state.case_revision=revision
                    st.session_state.pqc_policy_version=2
                    st.rerun()
                except (ValueError,KeyError,TypeError):st.error('No se recuperó el caso: estructura o integridad no válida.')
        st.caption('Auditoría íntegra' if store.verify_audit() else 'Auditoría: revisar integridad')
