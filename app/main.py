"""
AstraSec AI — Punto de entrada de la interfaz Streamlit.

Inicializa el estado de la sesión y muestra la navegación principal.
"""

import sys
import os
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils.helpers import load_env

load_env()

import streamlit as st

st.set_page_config(
    page_title="AstraSec AI",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.core.access_guard import require_access
require_access()
from app.core.console_design import apply_design,brand
apply_design()

# --------------------------------------------------------------------------
# Inicialización del estado de la sesión
# --------------------------------------------------------------------------
if "lab" not in st.session_state:
    st.session_state.lab = None

if "documents" not in st.session_state:
    st.session_state.documents = {}  # filename -> IngestedDocument

if "conversation" not in st.session_state:
    st.session_state.conversation = []  # [{"role": "user"|"agent", "content": str}]

if "findings" not in st.session_state:
    st.session_state.findings = []

if "hypotheses" not in st.session_state:
    st.session_state.hypotheses = []

if "recommendations" not in st.session_state:
    st.session_state.recommendations = []

if "limitations" not in st.session_state:
    st.session_state.limitations = []

if "analyst_notes" not in st.session_state:
    st.session_state.analyst_notes = ""

# --------------------------------------------------------------------------
# Barra lateral — navegación
# --------------------------------------------------------------------------
with st.sidebar:
    brand()

    ai_provider = os.environ.get("AI_PROVIDER", "demo").strip().lower()
    if ai_provider == "demo":
        st.warning("Conversación en modo demo.\nLa prueba real IBM tiene su propio estado y autorización.", icon="⚠️")
    else:
        st.caption(f"Proveedor configurado: {ai_provider} · ver estados en Resumen")

    st.divider()

    page = st.radio(
        "Navegación",
        options=[
            "◉ Resumen",
            "🏠 Laboratorio",
            "📂 Cargar archivos",
            "🔍 Consultar documentos",
            "🤖 Agente",
            "📄 Generar reporte",
            "⚙️ Configuración",
            "Demo de un caso",
        ],
        format_func=lambda value: {'◉ Resumen': 'Resumen', '🏠 Laboratorio': 'Laboratorio', '📂 Cargar archivos': 'Cargar evidencias', '🔍 Consultar documentos': 'Consultar documentos', '🤖 Agente': 'Agente', '📄 Generar reporte': 'Reportes', '⚙️ Configuración': 'Configuración'}.get(value,value),
        key="nav_page",
    )

    st.divider()
    if st.session_state.lab:
        st.markdown(f"**Lab activo:** {st.session_state.lab.name}")
        n_docs = len(st.session_state.documents)
        st.markdown(f"**Archivos cargados:** {n_docs}")
    else:
        st.markdown("*Sin laboratorio activo.*")

with st.sidebar:
    from app.core.case_ui import render_case_controls
    render_case_controls()

# --------------------------------------------------------------------------
# Enrutado de páginas
# --------------------------------------------------------------------------
from app.core.mascots import render_companion, render_gallery
with st.sidebar:
    with st.expander("Mascotas"):
        st.toggle("Mostrar mascotas", value=True, key="show_mascots")
        st.toggle("Animar mascotas", value=True, key="animate_mascots")

render_companion(page)
if page == "⚙️ Configuración":
    render_gallery()

if page == "◉ Resumen":
    from app.core.dashboard import render
    render()
elif page == "🏠 Laboratorio":
    from app.pages.page_lab import render
    render()
elif page == "📂 Cargar archivos":
    from app.pages.page_ingest import render
    render()
elif page == "🔍 Consultar documentos":
    from app.pages.page_query import render
    render()
elif page == "🤖 Agente":
    from app.pages.page_agent import render
    render()
elif page == "📄 Generar reporte":
    from app.pages.page_report import render
    render()
elif page == "⚙️ Configuración":
    from app.pages.page_config import render
    render()

elif page == "Demo de un caso":
    from app.pages.page_case_demo import render
    render()
