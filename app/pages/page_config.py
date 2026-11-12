"""
Configuración del piloto y diagnóstico de proveedores opcionales.
Muestra el estado de las variables de entorno y permite verificar la conexión.
"""
from __future__ import annotations

import os
import streamlit as st


def _env(key: str) -> str:
    """Devuelve el valor enmascarado de una variable de entorno."""
    v = os.environ.get(key, "")
    if not v:
        return "❌ No configurada"
    if "KEY" in key or "TOKEN" in key:
        return "✅ Configurada"
    return f"✅ {v}"


def render() -> None:
    st.header("⚙️ Configuración del agente")
    from app.core.operations_ui import render_operations
    st.info("Laboratorio IBM SkillsBuild: Bob IDE es obligatorio para el desarrollo; watsonx es opcional. El piloto local no requiere crear instancias ni ampliar permisos IAM. Guía, páginas 2, 5, 29 y 31.")
    from app.core.tools_evidence_ui import render_tools_evidence
    render_tools_evidence()
    render_operations()
    st.markdown(
        "Aquí puedes consultar la configuración del proveedor opcional ya disponible. "
        "Una configuración guardada o un recibo histórico no garantizan conexión actual."
    )

    provider = os.environ.get("AI_PROVIDER", "demo").strip().lower()

    # ---- Estado actual ----
    st.subheader("Estado actual")

    if provider == "demo":
        st.warning(
            "**Modo demostración activo** (`AI_PROVIDER=demo`).  \n"
            "Las respuestas del agente son ficticias. Para usar IA real, "
            "utiliza únicamente un proveedor habilitado para tu cuenta. Orchestrate es opcional; Runtime no es requisito del laboratorio.",
            icon="⚠️",
        )
    elif provider == "orchestrate":
        st.success("Proveedor configurado: IBM watsonx Orchestrate")
        for key in ("ORCHESTRATE_URL", "ORCHESTRATE_AGENT_ID", "ORCHESTRATE_API_KEY"):
            st.write(key + ": " + ("Configurada" if os.environ.get(key, "").strip() else "No configurada"))
        st.info("Proveedor configurado; pulsa la prueba para comprobar conexión actual. La consulta de prueba solo envía el texto sintético indicado.")
        if st.button("Probar conexion con Orchestrate", type="primary"):
            try:
                from app.core.agent import load_provider
                with st.spinner("Conectando con IBM..."):
                    result = load_provider()._get_model().chat(messages=[{"role": "user", "content": "di solo: OK"}])
                if result["choices"][0]["message"]["content"].strip() == "OK":
                    st.success("Conexion verificada: OK")
                else:
                    st.warning("Conexion establecida; respuesta distinta de OK.")
            except Exception:
                st.error("No se pudo verificar la conexion. Revisa credenciales, permisos y conectividad.")
        return
    elif provider == "watsonx":
        st.success("**Proveedor configurado:** IBM watsonx.ai", icon="✅")
        # Diagnóstico de bloqueo WML si el recibo indica 403
        try:
            import json
            from pathlib import Path
            status_path = Path(__file__).resolve().parents[2] / "data/private/runtime_connection_status.json"
            status_data = json.loads(status_path.read_text(encoding="utf-8"))
            status_msg = status_data.get("status", "")
            if "403" in status_msg or "Bloqueado" in status_msg:
                st.warning(
                    "**watsonx.ai Runtime — Acceso bloqueado (HTTP 403)**\n\n"
                    "El acceso registrado a Runtime está restringido. La guía del laboratorio indica que los servicios restringidos no son necesarios ni están disponibles para esta experiencia. "
                    "Conserva el flujo local y usa Orchestrate solo con el acceso existente; no necesitas solicitar roles Writer/Editor ni crear identidades de servicio.",
                    icon="⚠️",
                )
                st.caption("Estado registrado: " + status_msg)
        except (OSError, ValueError, KeyError):
            pass
    else:
        st.error(f"Proveedor desconocido: `{provider}`. Valores válidos: `demo`, `orchestrate`, `watsonx`.")

    # ---- Variables de entorno watsonx ----
    st.subheader("Variables de entorno (IBM watsonx.ai)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**AI_PROVIDER:** `{provider}`")
        st.markdown(f"**WATSONX_API_KEY:** {_env('WATSONX_API_KEY')}")
        st.markdown(f"**WATSONX_URL:** {_env('WATSONX_URL')}")
    with col2:
        st.markdown(f"**WATSONX_PROJECT_ID:** {_env('WATSONX_PROJECT_ID')}")
        model = os.environ.get("WATSONX_MODEL", "ibm/granite-3-3-8b-instruct")
        st.markdown(f"**WATSONX_MODEL:** `{model}`")

    # ---- Verificar conexión ----
    if provider == "watsonx":
        st.subheader("Verificar conexión")
        st.markdown(
            "Esto enviará una solicitud de prueba a la API de watsonx.ai. "
            "**No se enviarán documentos de tu sesión.**"
        )
        if st.button("🔌 Probar conexión con watsonx.ai", type="primary"):
            missing = [k for k in ["WATSONX_API_KEY", "WATSONX_URL", "WATSONX_PROJECT_ID"]
                       if not os.environ.get(k, "").strip()]
            if missing:
                st.error(f"Faltan variables: {', '.join(missing)}")
            else:
                with st.spinner("Conectando con watsonx.ai…"):
                    try:
                        from ibm_watsonx_ai.foundation_models import ModelInference
                        from ibm_watsonx_ai import Credentials

                        credentials = Credentials(
                            url=os.environ["WATSONX_URL"],
                            api_key=os.environ["WATSONX_API_KEY"],
                        )
                        model_id = os.environ.get("WATSONX_MODEL", "ibm/granite-3-3-8b-instruct")
                        model = ModelInference(
                            model_id=model_id,
                            credentials=credentials,
                            project_id=os.environ["WATSONX_PROJECT_ID"],
                        )
                        resp = model.chat(messages=[
                            {"role": "user", "content": "Di solo 'OK' en una palabra."}
                        ])
                        answer = resp["choices"][0]["message"]["content"]
                        st.success(f"✅ Conexión exitosa. Respuesta del modelo: **{answer.strip()[:80]}**")
                    except ImportError:
                        st.error(
                            "❌ El paquete `ibm-watsonx-ai` no está instalado en este entorno.  \n"
                            "Instálalo con:  \n`pip install ibm-watsonx-ai`  \n\n"
                            "**Nota:** Requiere Python ≥ 3.11 y < 3.15. "
                            "Usa el entorno `.venv314` (Python 3.14)."
                        )
                    except Exception as exc:
                        st.error(f"❌ Error de conexión: {exc}")

    # La cuenta educativa no requiere aprovisionamiento ni cambios IAM.
    if os.environ.get("ASTRASEC_LAB_MODE", "1").strip().lower() not in {"0", "false", "no"}:
        st.caption("Entrega del programa: conservar los resúmenes reales de tareas de Bob en bob_sessions. Runtime y Studio no son dependencias obligatorias. No crear claves ni instancias para resolver un acceso restringido.")
        return

    # ---- Instrucciones paso a paso ----
    st.divider()
    st.subheader("Cómo configurar watsonx.ai en 4 pasos")

    with st.expander("Ver instrucciones completas", expanded=(provider == "demo")):
        st.markdown("""
**Paso 1 — Obtener tu API Key de IBM Cloud**

1. Ve a [IBM Cloud → Gestionar → Acceso (IAM)](https://cloud.ibm.com/iam/apikeys)
2. Haz clic en **Crear una clave de API**
3. Dale un nombre (ej. `astrasec-key`) y copia el valor — solo se muestra una vez

---

**Paso 2 — Encontrar tu Project ID**

1. Abre [watsonx.ai](https://dataplatform.cloud.ibm.com/wx/home)
2. Abre el proyecto donde tienes el servicio watsonx.ai Runtime
3. Ve a la pestaña **Manage** → **General**
4. Copia el valor de **Project ID**

---

**Paso 3 — Identificar tu URL de región**

Según dónde provisionaste tu instancia de watsonx.ai Runtime:

| Región | URL |
|--------|-----|
| Dallas (us-south) | `https://us-south.ml.cloud.ibm.com` |
| Frankfurt (eu-de) | `https://eu-de.ml.cloud.ibm.com` |
| London (eu-gb) | `https://eu-gb.ml.cloud.ibm.com` |
| Tokyo (jp-tok) | `https://jp-tok.ml.cloud.ibm.com` |

---

**Paso 4 — Crear el archivo `.env`**

En la carpeta raíz del proyecto (`la carpeta del proyecto`), crea un archivo `.env`:

```
AI_PROVIDER=watsonx
WATSONX_API_KEY=<tu api key>
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_PROJECT_ID=<tu project id>
WATSONX_MODEL=ibm/granite-3-3-8b-instruct
```

Luego **reinicia la aplicación** con el entorno Python 3.14:

```powershell
# Desde la carpeta del proyecto
.venv314\\Scripts\\Activate.ps1
streamlit run app/main.py
```

---

> ⚠️ El archivo `.env` está excluido de git. Nunca lo compartas ni lo subas a repositorios.
""")
