"""
Página 1 — Registro del laboratorio.
"""
from __future__ import annotations

import streamlit as st
from app.core.lab import create_laboratory


def render() -> None:
    st.header("🏠 Laboratorio")
    st.markdown(
        "Registra el nombre, descripción y alcance del laboratorio activo. "
        "Esta información se incluirá en los reportes generados."
    )

    lab = st.session_state.lab

    with st.form("form_lab"):
        name = st.text_input(
            "Nombre del laboratorio *",
            value=lab.name if lab else "",
            placeholder="Ej.: Lab-Pentest-RedTeam-2024",
        )
        description = st.text_area(
            "Descripción *",
            value=lab.description if lab else "",
            placeholder="Breve descripción del propósito y contexto del laboratorio.",
            height=100,
        )
        analyst = st.text_input(
            "Analista responsable",
            value=lab.analyst if lab else "",
            placeholder="Nombre o identificador del analista",
        )
        scope = st.text_area(
            "Alcance técnico",
            value=lab.scope if lab else "",
            placeholder="Ej.: Red interna 192.168.10.0/24, servidor web app01.",
            height=80,
        )

        submitted = st.form_submit_button("💾 Guardar laboratorio", type="primary")

    if submitted:
        try:
            new_lab = create_laboratory(
                name=name,
                description=description,
                analyst=analyst,
                scope=scope,
            )
            st.session_state.lab = new_lab
            st.success(f"✅ Laboratorio **{new_lab.name}** registrado correctamente.")
        except ValueError as exc:
            st.error(f"❌ {exc}")

    if st.session_state.lab:
        st.divider()
        st.subheader("Laboratorio activo")
        lab = st.session_state.lab
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Nombre:** {lab.name}")
            st.markdown(f"**Analista:** {lab.analyst or '(no especificado)'}")
            st.markdown(f"**Creado:** {lab.created_at}")
        with col2:
            st.markdown(f"**Descripción:** {lab.description}")
            if lab.scope:
                st.markdown(f"**Alcance:** {lab.scope}")

        with st.expander("Ver JSON del laboratorio"):
            st.code(lab.to_json(), language="json")
