"""
Página 5 — Generación del reporte Markdown.
"""
from __future__ import annotations

import os
from datetime import datetime

import streamlit as st
from app.core.report import generate_report
from app.core.report_pdf import generate_pdf
from app.core.mascots import agent_activity


def render() -> None:
    st.header("📄 Generar reporte")
    st.markdown(
        "Genera un reporte PDF o Markdown estructurado con alcance, evidencias, hallazgos, "
        "recomendaciones y limitaciones."
    )

    from app.core.pqc_workflow_ui import render_integrated_report
    has_pqc_report = render_integrated_report()
    st.divider()
    if st.session_state.lab is None and has_pqc_report:
        st.caption('El reporte PQC usa su propio expediente verificado. El reporte general requiere un laboratorio registrado.')
        return

    if st.session_state.lab is None:
        st.warning("⚠️ Primero registra un laboratorio en **🏠 Laboratorio**.")
        return

    lab = st.session_state.lab
    documents = list(st.session_state.documents.values())

    st.subheader("Contenido del reporte")

    # Hallazgos
    st.markdown("### Hechos observados")
    st.caption("Lista de hechos constatados en las evidencias. Uno por línea.")
    findings_text = st.text_area(
        "Hechos observados",
        value="\n".join(st.session_state.findings),
        height=120,
        placeholder="Ej.: Se detectaron 47 intentos de autenticación fallida en 5 minutos.",
        label_visibility="collapsed",
    )

    st.markdown("### Hipótesis (no confirmadas)")
    st.caption("Inferencias basadas en las evidencias, sin confirmación directa.")
    hypotheses_text = st.text_area(
        "Hipótesis",
        value="\n".join(st.session_state.hypotheses),
        height=100,
        placeholder="Ej.: El patrón podría indicar un ataque de fuerza bruta.",
        label_visibility="collapsed",
    )

    st.markdown("### Recomendaciones")
    st.caption("Acciones sugeridas sustentadas en las evidencias.")
    recommendations_text = st.text_area(
        "Recomendaciones",
        value="\n".join(st.session_state.recommendations),
        height=100,
        placeholder="Ej.: Habilitar bloqueo de cuenta tras 5 intentos fallidos.",
        label_visibility="collapsed",
    )

    st.markdown("### Limitaciones adicionales")
    st.caption("Restricciones específicas de este análisis (opcionales).")
    limitations_text = st.text_area(
        "Limitaciones",
        value="\n".join(st.session_state.limitations),
        height=80,
        placeholder="Ej.: No se analizaron logs del servidor de base de datos.",
        label_visibility="collapsed",
    )

    st.markdown("### Notas del analista")
    analyst_notes = st.text_area(
        "Notas",
        value=st.session_state.analyst_notes,
        height=80,
        placeholder="Observaciones adicionales libres.",
        label_visibility="collapsed",
    )

    st.divider()

    if st.button("📄 Generar reporte", type="primary"):
        # Parsear listas (línea por línea, ignorar vacías)
        findings = [l.strip() for l in findings_text.splitlines() if l.strip()]
        hypotheses = [l.strip() for l in hypotheses_text.splitlines() if l.strip()]
        recommendations = [l.strip() for l in recommendations_text.splitlines() if l.strip()]
        limitations = [l.strip() for l in limitations_text.splitlines() if l.strip()]

        # Guardar en sesión
        st.session_state.findings = findings
        st.session_state.hypotheses = hypotheses
        st.session_state.recommendations = recommendations
        st.session_state.limitations = limitations
        st.session_state.analyst_notes = analyst_notes

        ai_provider = os.environ.get("AI_PROVIDER", "demo").strip()

        with agent_activity("admin", "Preparando tu reporte", "Generando Markdown y PDF localmente.", completed="Reporte listo para descargar"):
            report_md = generate_report(
                lab=lab,
                documents=documents,
                findings=findings,
                hypotheses=hypotheses,
                recommendations=recommendations,
                limitations=limitations,
                analyst_notes=analyst_notes,
                ai_provider="Generación local; proveedor configurado: " + ai_provider,
            )
            report_pdf = generate_pdf(report_md)

        st.success("✅ Reporte generado.")

        # Vista previa
        with st.expander("Vista previa del reporte", expanded=True):
            st.markdown(report_md)

        # Descarga
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in lab.name)
        filename = f"reporte_{safe_name}_{timestamp}.md"

        st.download_button(
            label="⬇️ Descargar reporte .md",
            data=report_md.encode("utf-8"),
            file_name=filename,
            mime="text/markdown",
        )

        st.download_button(
            label="⬇️ Descargar reporte PDF",
            data=report_pdf,
            file_name=filename.removesuffix(".md") + ".pdf",
            mime="application/pdf",
        )

        if ai_provider == "demo":
            st.warning(
                "⚠️ Este reporte fue generado en **modo demostración**. "
                "Los hallazgos y recomendaciones son ficticios si provienen del agente demo.",
                icon="⚠️",
            )
