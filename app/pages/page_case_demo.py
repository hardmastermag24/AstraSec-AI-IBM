"""Guided replay of documented evidence; no execution or external calls."""
from pathlib import Path
import json
import streamlit as st

def render():
    base=Path(__file__).resolve().parents[2]/"docs/demo_caso_ubuntu"
    steps=json.loads((base/"pasos.json").read_text(encoding="utf-8"))
    st.header("Demostración de un caso · ASTRA-UBUNTU")
    st.info("Recorrido guiado de evidencia ya documentada. Cambiar de paso no ejecuta comandos, modifica expedientes ni realiza consultas a IBM.")
    st.caption("Caso de demostración · revisión 1 · ensayo técnico · revisión humana pendiente")
    st.markdown("Captura → plan IBM → revisión → control de errores → guardado → reporte")
    selected=st.select_slider("Paso del flujo",options=list(range(1,7)),format_func=lambda n:f"{n}. {steps[n-1]['title']}",key="case_demo_step")
    row=st.columns([1,4,1])
    def move(delta):
        st.session_state.case_demo_step=max(1,min(6,st.session_state.case_demo_step+delta))
    row[0].button("Anterior",disabled=selected==1,on_click=move,args=(-1,))
    row[2].button("Siguiente",disabled=selected==6,on_click=move,args=(1,))
    s=steps[selected-1]
    st.subheader(s["title"])
    st.caption(s["tool"])
    cols=st.columns(3)
    for col,label,key in zip(cols,["Entrada","Qué hace","Resultado"],["input","action","result"]):
        with col:
            st.markdown("**"+label+"**")
            st.write(s[key])
    st.success("Qué decir: "+s["say"])
    with st.expander("Finalidad y límites del caso"):
        st.write("Organizar evidencia y apoyar una decisión revisable para preparar la transición PQC. No certifica seguridad poscuántica ni ejecuta remediación. Usuario y utilidad pendientes de validación.")
        st.write("IBM Bob: asistencia de desarrollo documentada en Configuración. Este incremento fue realizado con Codex. Miro conserva el diseño; las propuestas no equivalen a funciones implementadas.")
