"""Local animated line-art companions inspired by the user's robot references.

Illustrations show application activity, never a security verdict.
No remote assets, JavaScript, timers, or Streamlit reruns are needed.
"""
from html import escape
from contextlib import contextmanager
from base64 import b64encode

import streamlit as st


MASCOTS = (
    ("quantum", "Criptografía cuántica"),
    ("analyst", "Analista PQC"),
    ("worker", "Desarrollador de protocolos"),
    ("chat", "Soporte técnico PQC"),
    ("scanner", "Escáner cuántico"),
    ("admin", "Gestión de identidad"),
    ("data", "Analítica PQC"),
    ("repair", "Reparación cuántica"),
    ("reception", "Acceso seguro"),
    ("analyze", "Evaluación PQC"),
    ("advisor", "Asesor PQC"),
    ("network", "Redes PQC"),
    ("security", "Seguridad de enclave"),
    ("collab", "Colaboración PQC"),
    ("service", "Servicio de implementación PQC"),
    ("task", "Ejecución poscuántica"),
)

PAGE_MASCOTS = {
    "◉ Resumen": "data",
    "🏠 Laboratorio": "quantum",
    "📂 Cargar archivos": "scanner",
    "🔍 Consultar documentos": "analyst",
    "🤖 Agente": "advisor",
    "📄 Generar reporte": "admin",
    "⚙️ Configuración": "service",
    "Demo de un caso": "worker",
}

_CSS = """
<style>
.astra-mascots{color:#161616;font-family:'Segoe UI',sans-serif}
.astra-mascots .am-banner{display:flex;align-items:center;gap:18px;margin:0 0 16px;border-bottom:1px solid #e0e0e0;padding:4px 0 14px}
.astra-mascots svg,.astra-mascots img{display:block;flex-shrink:0;width:112px;height:112px;overflow:visible}
.astra-mascots .am-kicker{font-size:12px;color:#525252;margin-bottom:4px}
.astra-mascots .am-name{font-size:18px;font-weight:600;line-height:1.4}
.astra-mascots .am-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}
.astra-mascots .am-card{display:flex;flex-direction:column;align-items:center;text-align:center;border:1px solid #e0e0e0;padding:18px 10px;gap:10px;background:#fff}
.astra-mascots .am-card svg,.astra-mascots .am-card img{width:132px;height:132px;max-width:100%}
.astra-mascots .am-card span{font-size:14px;font-weight:600;line-height:1.4}
.astra-mascots.am-animated .am-float{animation:astra-bob 3.4s ease-in-out infinite}
.astra-mascots.am-animated .am-eyes{animation:astra-blink 5.2s infinite;transform-box:fill-box;transform-origin:center}
.astra-mascots.am-animated .am-spin{animation:astra-spin 7s linear infinite;transform-box:fill-box;transform-origin:center}
.astra-mascots.am-animated .am-wave{animation:astra-wave 2.6s ease-in-out infinite;transform-box:fill-box;transform-origin:bottom left}
.astra-mascots.am-animated .am-scan{animation:astra-scan 2.8s ease-in-out infinite}
.astra-mascots.am-animated .am-pulse{animation:astra-pulse 2.4s ease-in-out infinite}
.astra-mascots.am-animated .am-walk{animation:astra-walk 1.5s ease-in-out infinite;transform-box:fill-box;transform-origin:top center}
@keyframes astra-bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
@keyframes astra-blink{0%,43%,47%,100%{transform:scaleY(1)}45%{transform:scaleY(.12)}}
@keyframes astra-spin{to{transform:rotate(360deg)}}
@keyframes astra-wave{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(12deg)}}
@keyframes astra-scan{0%,100%{transform:translateY(0);opacity:.4}50%{transform:translateY(20px);opacity:1}}
@keyframes astra-pulse{0%,100%{opacity:.4}50%{opacity:1}}
@keyframes astra-walk{0%,100%{transform:rotate(-9deg)}50%{transform:rotate(9deg)}}
@media(max-width:700px){.astra-mascots .am-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(prefers-reduced-motion:reduce){.astra-mascots *{animation:none!important}}
</style>
"""


def _eyes(y=62, happy=False):
    if happy:
        return f'<g class="am-eyes"><path d="M43 {y+2}q6-10 12 0m18 0q6-10 12 0"/></g>'
    return f'<g class="am-eyes"><circle cx="49" cy="{y}" r="6"/><circle cx="79" cy="{y}" r="6"/></g>'


def _antenna():
    return '<path d="M64 31V20"/><circle cx="64" cy="14" r="5"/>'


def _face(happy=False):
    return ('<rect x="30" y="34" width="68" height="54" rx="12" fill="white"/>'
            '<path d="M30 49q-16 12 0 25m68-25q16 12 0 25"/>'
            + _eyes(happy=happy) + '<path d="M53 76q11 8 22 0"/>')


def _shield(x=64, y=92):
    return (f'<g transform="translate({x} {y})"><path fill="white" d="M0-17l17 6v13Q16 14 0 22Q-16 14-17 2v-13z"/>'
            '<rect x="-6" y="-1" width="12" height="10" rx="2"/><path d="M-4-1v-4a4 4 0 0 1 8 0v4"/></g>')


def _gear(x, y):
    return (f'<g transform="translate({x} {y})"><g class="am-spin"><circle r="9"/>'
            '<circle r="3"/><path d="M0-14v5m0 18v5m-14-14h5m18 0h5m-24-10l4 4m12 12l4 4m-20 0l4-4m12-12l4-4"/></g></g>')


def _drawing(kind):
    if kind == "repair":
        return ('<rect x="20" y="88" width="88" height="25" rx="12"/>'
                '<circle cx="38" cy="100" r="6"/><circle cx="64" cy="100" r="6"/><circle cx="90" cy="100" r="6"/>'
                '<path d="M39 87a25 25 0 0 1 50 0"/>'
                '<g class="am-wave"><path d="M65 61l26-28-38-9m37 14L49 32M48 23H31l-8-8m8 8l-8 8M48 32H31l-8 8"/>'
                '<circle cx="94" cy="31" r="7"/></g>')
    if kind == "scanner":
        pixels = ''.join(f'<rect x="{x}" y="{y}" width="3" height="3" fill="currentColor" stroke="none"/>'
                         for x in range(31, 98, 9) for y in range(84, 112, 9) if (x+y)%3)
        return ('<path d="M24 69a40 40 0 0 1 80 0M53 30l-6-8m28 8l6-8"/>' + _eyes(y=54)
                + '<rect x="18" y="69" width="92" height="9" rx="4"/>' + pixels
                + '<path class="am-scan" d="M29 85h70" stroke="#0f62fe" stroke-width="3"/>')
    if kind in {"admin", "analyze"}:
        dome = '<path d="M24 63a40 40 0 0 1 80 0Z" fill="white"/>' + _eyes(y=48)
        if kind == "admin":
            return dome + '<path d="M40 36l15 4m18 0l15-4"/><rect x="25" y="69" width="78" height="45" rx="4"/><path d="M38 83l3 3 6-7m-9 19l3 3 6-7m8-11h35m-35 15h35"/>'
        return dome + '<path d="M35 71l29 9 29-9-8 39H43z"/><g class="am-spin"><path d="M57 45h14m-7-7v14m-5-12l10 10m0-10l-10 10"/></g><path class="am-pulse" d="M48 91l10 9 22-19" stroke="#0f62fe"/>'
    if kind == "advisor":
        return (_antenna() + '<path d="M31 73a33 33 0 0 1 66 0"/>' + _eyes(y=59, happy=True)
                + '<path d="M48 72q16 8 32 0M24 91q-9-22 9-24m62 0q18 2 9 24"/>'
                '<path d="M64 84Q48 72 31 78v32q17-6 33 6 16-12 33-6V78q-17-6-33 6v32" fill="white"/>'
                '<path class="am-wave" d="M75 88l12 4-12 4m0 5h13"/>')
    if kind == "data":
        return ('<rect x="25" y="32" width="78" height="48" rx="10" fill="white"/>' + _eyes(y=53)
                + '<path d="M56 68h16M52 32l-7-8m31 8l7-8M50 80v8m28-8v8"/>'
                '<rect x="22" y="88" width="84" height="27" rx="13"/>'
                '<g class="am-spin"><circle cx="38" cy="101" r="7"/><path d="M38 94v14m-7-7h14"/></g>'
                '<circle cx="64" cy="101" r="7"/><circle cx="90" cy="101" r="7"/>'
                '<path class="am-pulse" d="M31 39h9m49 33h9" stroke="#0f62fe"/>')
    if kind == "service":
        return ('<path d="M27 31h73q9 0 9 9v43q0 9-9 9H66L47 109V92H27q-9 0-9-9V40q0-9 9-9Z" fill="white"/>'
                '<rect x="36" y="48" width="49" height="31" rx="6"/>' + _eyes(y=58, happy=True)
                + '<path d="M52 70q10 8 20 0"/>' + _gear(96, 38) + _gear(28, 85))
    if kind == "network":
        return (_antenna() + '<ellipse cx="64" cy="70" rx="32" ry="39"/>' + _eyes(y=51)
                + '<g class="am-pulse" stroke="#0f62fe"><path d="M24 43l80 48M24 91l80-48M24 43h80L64 112Z M24 91h80L64 25Z"/></g>'
                + ''.join(f'<circle cx="{x}" cy="{y}" r="5" fill="white"/>' for x,y in [(24,43),(104,43),(24,91),(104,91)])
                + '<circle cx="64" cy="79" r="11"/>')
    base = _antenna() + _face(happy=kind in {"reception", "collab", "worker"})
    if kind == "quantum":
        return base + '<g transform="translate(99 27)"><g class="am-spin"><ellipse rx="17" ry="6"/><ellipse rx="17" ry="6" transform="rotate(60)"/><ellipse rx="17" ry="6" transform="rotate(120)"/></g></g><path d="M46 103h36"/>'
    if kind == "analyst":
        return (base + '<path d="M25 57V48a39 39 0 0 1 78 0v20m-76 8q0 18 27 18"/>'
                '<g class="am-wave"><circle cx="90" cy="78" r="17" fill="white"/><path d="M102 91l14 18"/><path d="M81 77h18m-14 6h10" stroke-width="2"/></g>')
    if kind == "worker":
        return base + '<g class="am-wave"><path d="M93 25l14-12m-3-5l9 10m-84 8l-9-9m-5 4l11-11"/></g><path d="M46 103h36"/>'
    if kind == "chat":
        return base + '<path d="M40 88v20l22-20" fill="white"/><g class="am-pulse"><path d="M17 37q-12 18 0 36m94-36q12 18 0 36"/></g>'
    if kind == "reception":
        return base + '<path d="M40 89q-16 0-16 24h80q0-24-16-24"/>' + _shield(94, 97)
    if kind == "security":
        return base + '<path d="M35 91l-10 15m68-15l10 15"/>' + _shield()
    if kind == "collab":
        return base + '<path d="M38 89l-9 22m61-22l9 22M45 99l19 10 19-10"/>' + '<g class="am-wave"><circle cx="16" cy="25" r="10"/><circle cx="111" cy="25" r="10"/></g>'
    return base + '<path d="M45 88v15m38-15v15"/><g class="am-walk"><path d="M45 103l-10 13H23m60-13l10 13h12"/></g><path class="am-wave" d="M99 80l14 13 7-8"/>'


def mascot_svg(kind):
    label = dict(MASCOTS)[kind]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title><g fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">'
            f'<g class="am-float">{_drawing(kind)}</g></g></svg>')


_ACTIVITY_CSS = """<style>
.astra-mascots .am-banner{background:linear-gradient(110deg,#edf5ff,#fff 75%);border:1px solid #d0e2ff;border-left:4px solid #0f62fe;padding:16px 20px;gap:24px}
.astra-mascots .am-detail{font-size:13px;color:#525252;line-height:1.5;margin-top:7px;overflow-wrap:anywhere}
.astra-mascots .am-state{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#0043ce;margin-bottom:5px;font-weight:600}
.astra-mascots .am-track{height:4px;background:#d0e2ff;margin-top:12px;overflow:hidden;max-width:420px}
.astra-mascots .am-track i{display:block;height:100%;background:#0f62fe}
.astra-mascots.am-animated.am-busy .am-track i{width:32%;animation:astra-travel 1.4s ease-in-out infinite}
.astra-mascots.am-animated.am-busy .am-float{animation:astra-bob .9s ease-in-out infinite}
.astra-mascots.am-animated.am-busy .am-spin{animation-duration:1.2s}
.astra-mascots.am-animated.am-busy .am-scan{animation-duration:.85s}
.astra-mascots.am-done .am-banner{border-left-color:#198038;background:#defbe6}
.astra-mascots.am-error .am-banner{border-left-color:#da1e28;background:#fff1f1}
.astra-mascots.am-error .am-state{color:#a2191f}
@keyframes astra-travel{0%{transform:translateX(-110%)}100%{transform:translateX(420%)}}
@media(max-width:600px){.astra-mascots .am-banner{gap:12px;padding:12px}.astra-mascots .am-banner img{width:80px;height:80px}}
@media(prefers-reduced-motion:reduce){.astra-mascots *{animation:none!important}}
</style>"""


def mascot_image(kind, state="idle"):
    """Keep SVG animation self-contained in an image; st.html strips inline SVG."""
    animate = " am-animated" if st.session_state.get("animate_mascots", True) else ""
    svg = mascot_svg(kind).replace('<svg ', f'<svg class="astra-mascots{animate} am-{state}" style="color:#161616" ', 1)
    css = (_CSS + _ACTIVITY_CSS).replace('<style>', '').replace('</style>', '')
    end = svg.index('>') + 1
    svg = svg[:end] + '<style>' + css + '</style>' + svg[end:]
    encoded = b64encode(svg.encode('utf-8')).decode('ascii')
    return f'<img src="data:image/svg+xml;base64,{encoded}" alt="{escape(dict(MASCOTS)[kind])}" width="112" height="112">'


def _panel(kind, state="idle", title=None, detail="", progress=None):
    labels = {"idle": "Disponible", "busy": "En proceso", "done": "Completado", "error": "Revisar resultado"}
    animate = " am-animated" if st.session_state.get("animate_mascots", True) else ""
    track = ""
    if progress is not None:
        percent = max(0, min(100, round(progress * 100)))
        track = (f'<div class="am-track" role="progressbar" aria-label="Archivos procesados" '
                 f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{percent}"><i style="width:{percent}%"></i></div>')
    elif state == "busy":
        track = '<div class="am-track" aria-hidden="true"><i></i></div>'
    return (_CSS + _ACTIVITY_CSS + f'<div class="astra-mascots{animate} am-{state}"><div class="am-banner">'
            + mascot_image(kind, state) + '<div role="status" aria-live="polite">'
            + f'<div class="am-state">{labels[state]}</div><div class="am-name">{escape(title or dict(MASCOTS)[kind])}</div>'
            + f'<div class="am-detail">{escape(detail)}</div>{track}</div></div></div>')


def update_activity(kind, state, title, detail="", progress=None):
    """Replace this session's companion in place; no background reruns or delays."""
    if not st.session_state.get("show_mascots", True):
        return
    slot = st.session_state.get("_activity_slot")
    if slot is None:
        slot = st.empty()
        st.session_state["_activity_slot"] = slot
    with slot.container():
        st.html(_panel(kind, state, title, detail, progress))


@contextmanager
def agent_activity(kind, title, detail="", completed="Tarea completada"):
    """Busy for exactly the duration of the enclosed operation, including failures."""
    update_activity(kind, "busy", title, detail)
    try:
        yield lambda message, progress=None: update_activity(kind, "busy", title, message, progress)
    except Exception:
        update_activity(kind, "error", "La tarea no se completó", "Revisa el mensaje de la operación antes de continuar.")
        raise
    else:
        update_activity(kind, "done", completed, "La operación finalizó; revisa los resultados en esta pantalla.")


def render_companion(page):
    """Show a companion for the current section, using session display settings."""
    if not st.session_state.get("show_mascots", True):
        return
    kind = PAGE_MASCOTS.get(page, "chat")
    st.session_state["_activity_slot"] = st.empty()
    update_activity(kind, "idle", dict(MASCOTS)[kind], "Listo para acompañarte. El estado cambiará al procesar información.")


def render_gallery():
    with st.expander("Probar animaciones de los agentes", expanded=False):
        st.caption("Vista de muestra: estos estados no ejecutan tareas ni envían información.")
        options = {"Disponible": ("quantum", "idle"), "Cargando archivos": ("scanner", "busy"), "Analizando": ("advisor", "busy"), "Buscando": ("analyst", "busy"), "Completado": ("data", "done"), "Con incidencias": ("repair", "error")}
        selected = st.selectbox("Estado de muestra", list(options), key="agent_motion_preview")
        kind, state = options[selected]
        if st.session_state.get("show_mascots", True):
            st.html(_panel(kind, state, selected, "Vista previa de la animación · sin operación en curso."))
    with st.expander("Colección de mascotas PQC", expanded=False):
        st.caption("Los 16 robots de trabajo y soporte. Sus movimientos son ilustrativos.")
        animate = " am-animated" if st.session_state.get("animate_mascots", True) else ""
        cards = ''.join('<div class="am-card">' + mascot_image(kind) + f'<span>{escape(label)}</span></div>'
                        for kind, label in MASCOTS)
        st.html(_CSS + f'<div class="astra-mascots{animate}"><div class="am-grid">{cards}</div></div>')
