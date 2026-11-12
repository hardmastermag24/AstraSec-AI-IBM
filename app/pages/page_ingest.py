"""
Página 2 — Carga de archivos (PDF, TXT, JSON).
"""
from __future__ import annotations

import streamlit as st
from app.core.ingest import ingest_file, ALLOWED_EXTENSIONS
from app.utils.helpers import get_int_env
from app.core.mascots import agent_activity, update_activity


def render() -> None:
    st.header("📂 Cargar archivos")
    st.markdown(
        "Carga documentos PDF o TXT y logs TXT o JSON. "
        "El contenido se trata como **datos**, nunca como instrucciones ejecutables."
    )

    if st.session_state.lab is None:
        st.warning("⚠️ Primero registra un laboratorio en la pestaña **🏠 Laboratorio**.")
        return

    chunk_size = get_int_env("CHUNK_SIZE", 1500)
    overlap = get_int_env("CHUNK_OVERLAP", 200)

    uploaded_files = st.file_uploader(
        "Selecciona uno o varios archivos",
        type=["pdf", "txt", "json"],
        accept_multiple_files=True,
        help=f"Tipos permitidos: {', '.join(sorted(ALLOWED_EXTENSIONS))} · Máximo 20 MB por archivo",
    )

    if uploaded_files:
        for uf in uploaded_files:
            if uf.name in st.session_state.documents:
                st.info(f"ℹ️ **{uf.name}** ya está cargado. Se reemplazará.")

        if st.button("⬆️ Procesar archivos seleccionados", type="primary"):
            total = len(uploaded_files)
            failed = 0
            with agent_activity("scanner", "Leyendo tus evidencias", "Extracción local de texto y fragmentos.", completed="Procesamiento terminado") as status:
                for i, uf in enumerate(uploaded_files):
                    status(f"Archivo {i + 1} de {total} · {uf.name}", i / total)
                    data = uf.getvalue()
                    doc = ingest_file(uf.name, data, chunk_size=chunk_size, overlap=overlap)
                    st.session_state.documents[uf.name] = doc
                    status(f"{i + 1} de {total} procesados · {uf.name}", (i + 1) / total)
                    if doc.ok:
                        st.success(
                            f"✅ **{uf.name}** — {len(doc.chunks)} fragmentos extraídos "
                            f"({len(doc.full_text):,} caracteres)"
                        )
                    else:
                        failed += 1
                        st.error(f"❌ **{uf.name}** — {doc.error}")
            update_activity("scanner", "error" if failed else "done", "Carga terminada con incidencias" if failed else "Evidencias listas para consultar", f"{total - failed} de {total} archivos procesados correctamente.", 1)

    # Mostrar documentos cargados
    st.divider()
    st.subheader("Archivos cargados en esta sesión")

    if not st.session_state.documents:
        st.info("No hay archivos cargados todavía.")
        return

    for filename, doc in list(st.session_state.documents.items()):
        with st.expander(f"{'✅' if doc.ok else '❌'} {filename} ({doc.file_type})"):
            if doc.ok:
                st.markdown(f"- **Fragmentos:** {len(doc.chunks)}")
                st.markdown(f"- **Caracteres totales:** {len(doc.full_text):,}")
                st.markdown("**Primer fragmento (vista previa):**")
                if doc.chunks:
                    st.text(doc.chunks[0].text[:500] + ("…" if len(doc.chunks[0].text) > 500 else ""))
            else:
                st.error(f"Error: {doc.error}")

            if st.button(f"🗑️ Eliminar {filename}", key=f"del_{filename}"):
                del st.session_state.documents[filename]
                st.rerun()
