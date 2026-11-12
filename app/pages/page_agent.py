"""
Página 4 — Conversación con el agente de IA.
"""
from __future__ import annotations

import os
import streamlit as st
from app.core.rag import retrieve, format_context_for_prompt
from app.core.agent import load_provider, DEMO_LABEL
from app.utils.helpers import get_int_env
from app.core.mascots import agent_activity


def _all_chunks():
    chunks = []
    for doc in st.session_state.documents.values():
        chunks.extend(doc.chunks)
    return chunks


def render() -> None:
    st.header("🤖 Agente de análisis")

    mode = st.radio("Modo del agente", ["Captura real Ubuntu / Kali", "Conversación", "Prueba real IBM · datos ficticios"], key="agent_mode")
    if mode == "Captura real Ubuntu / Kali":
        st.caption("Revisa las evidencias recopiladas en tus máquinas virtuales. Disponible sin conexión a IBM.")
        from app.core.real_capture_ui import render_real_capture
        render_real_capture()
        return

    if mode == "Prueba real IBM · datos ficticios":
        from app.core.ibm_demo_ui import render as render_ibm_demo
        render_ibm_demo()
        return

    ai_provider_name = os.environ.get("AI_PROVIDER", "demo").strip().lower()
    if ai_provider_name == "orchestrate":
        mode = st.radio("Área de análisis", ["Criptografía poscuántica", "Validación general"], horizontal=True)
        if mode == "Criptografía poscuántica":
            from app.core.pqc_ui import render_pqc
            render_pqc()
            return
        from app.core.synthetic_ui import render_synthetic
        render_synthetic()
        return

    if ai_provider_name == "demo":
        st.warning(
            "**Modo demostración activo.** Las respuestas del agente son ficticias "
            "y no representan análisis real de IA. Configure `AI_PROVIDER` en `.env` "
            "para usar un modelo real.",
            icon="⚠️",
        )

    if st.session_state.lab is None:
        st.warning("⚠️ Primero registra un laboratorio en **🏠 Laboratorio**.")
        return

    all_chunks = _all_chunks()
    top_k = get_int_env("MAX_CONTEXT_CHUNKS", 5)

    if not all_chunks:
        st.info(
            "ℹ️ No hay documentos cargados. El agente puede responder sin contexto, "
            "pero el análisis será muy limitado. Ve a **📂 Cargar archivos** primero."
        )

    # Mostrar historial de conversación
    for turn in st.session_state.conversation:
        if turn["role"] == "user":
            with st.chat_message("user"):
                st.markdown(turn["content"])
        else:
            with st.chat_message("assistant", avatar="🔐"):
                st.markdown(turn["content"])

    # Entrada del usuario
    user_input = st.chat_input("Escribe tu consulta o pregunta sobre las evidencias…")

    if user_input:
        # Recuperar contexto
        results = retrieve(user_input, all_chunks, top_k=top_k)

        # Mostrar aviso de contexto que se enviará (transparencia)
        if results and ai_provider_name != "demo":
            with st.expander(
                f"ℹ️ Contexto que se enviará al modelo ({len(results)} fragmento(s)) — revisar antes de continuar",
                expanded=True,
            ):
                st.markdown("**Fragmentos seleccionados:**")
                for r in results:
                    st.markdown(f"- `{r.reference()}`")
                context_preview = format_context_for_prompt(results)
                st.text_area("Contenido del contexto", context_preview, height=200, disabled=True)
                st.info("Al enviar la consulta, este contenido será transmitido al proveedor de IA.")

        # Agregar turno del usuario
        st.session_state.conversation.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generar respuesta del agente
        with st.chat_message("assistant", avatar="🔐"):
            try:
                with agent_activity("advisor", "Analizando la consulta", "Preparando respuesta de demostración." if ai_provider_name == "demo" else "Esperando respuesta del proveedor configurado.", completed="Respuesta preparada"):
                    agent = load_provider()
                    response = agent.analyze(
                        query=user_input,
                        context_chunks=results,
                        conversation_history=st.session_state.conversation[:-1],
                    )
            except Exception as exc:  # noqa: BLE001
                response = f"❌ Error al consultar el agente: {exc}"

            st.markdown(response)
            st.session_state.conversation.append({"role": "agent", "content": response})

    # Controles
    st.divider()
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state.conversation = []
            st.rerun()

    # Extraer hallazgos de la conversación
    with col2:
        if st.button("📥 Extraer último análisis como hallazgo"):
            agent_turns = [t for t in st.session_state.conversation if t["role"] == "agent"]
            if agent_turns:
                last = agent_turns[-1]["content"]
                # Agregar a hallazgos para el reporte
                snippet = last[:300].replace("\n", " ").strip()
                st.session_state.findings.append(f"[Agente]: {snippet}…")
                st.success("✅ Último análisis agregado a los hallazgos del reporte.")
            else:
                st.warning("No hay respuestas del agente todavía.")

