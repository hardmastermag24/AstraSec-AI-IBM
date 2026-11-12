"""
Página 3 — Consulta de documentos cargados con referencia de fuentes.
"""
from __future__ import annotations

import streamlit as st
from app.core.rag import retrieve
from app.utils.helpers import get_int_env
from app.core.mascots import agent_activity


def _all_chunks():
    chunks = []
    for doc in st.session_state.documents.values():
        chunks.extend(doc.chunks)
    return chunks


def render() -> None:
    st.header("🔍 Consultar documentos")
    st.markdown(
        "Consulta el contenido de los documentos cargados. "
        "Los resultados muestran la fuente exacta de cada fragmento."
    )

    if st.session_state.lab is None:
        st.warning("⚠️ Primero registra un laboratorio en **🏠 Laboratorio**.")
        return

    all_chunks = _all_chunks()
    if not all_chunks:
        st.info("ℹ️ No hay documentos cargados. Ve a **📂 Cargar archivos** primero.")
        return

    top_k = get_int_env("MAX_CONTEXT_CHUNKS", 5)

    st.markdown(
        f"**{len(all_chunks)} fragmentos disponibles** de {len(st.session_state.documents)} archivo(s)."
    )

    query = st.text_input(
        "Consulta",
        placeholder="Ej.: ¿Qué errores de autenticación aparecen en los logs?",
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        top_k_input = st.number_input(
            "Máx. fragmentos",
            min_value=1,
            max_value=20,
            value=top_k,
            help="Número máximo de fragmentos a mostrar",
        )

    if st.button("🔍 Buscar", type="primary", disabled=not query.strip()):
        with agent_activity("analyst", "Buscando en tus documentos", f"Consultando {len(all_chunks)} fragmentos locales.", completed="Búsqueda terminada"):
            results = retrieve(query, all_chunks, top_k=int(top_k_input))

        if not results:
            st.info("No se encontraron fragmentos relevantes para esta consulta.")
            return

        st.success(f"✅ {len(results)} fragmento(s) encontrado(s).")

        for i, r in enumerate(results, 1):
            with st.expander(
                f"Fragmento {i} — {r.reference()} (relevancia: {r.score:.0%})",
                expanded=(i <= 3),
            ):
                st.markdown(f"**Fuente:** `{r.chunk.source}` · fragmento {r.chunk.chunk_index + 1}")
                st.markdown(f"**Tipo de archivo:** {r.chunk.file_type}")
                st.text(r.chunk.text)
