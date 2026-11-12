"""
AstraSec AI — Generación de reportes Markdown.

Responsabilidades:
- Construir un reporte Markdown estructurado con las secciones requeridas.
- Distinguir hechos observados, hipótesis y recomendaciones.
- Incluir advertencias sobre el nivel de certeza.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from app.core.lab import Laboratory
from app.core.ingest import IngestedDocument


REPORT_HEADER = """\
<!--
  AVISO: Este reporte ha sido generado por AstraSec AI.
  Las secciones marcadas como "Hipótesis" son suposiciones no confirmadas.
  Las vulnerabilidades NO están confirmadas a menos que se indique explícitamente
  con evidencia directa. Revisar con un analista humano antes de tomar decisiones.
-->
"""


def generate_report(
    lab: Laboratory,
    documents: List[IngestedDocument],
    findings: List[str],
    hypotheses: List[str],
    recommendations: List[str],
    limitations: List[str],
    analyst_notes: str = "",
    ai_provider: str = "demo",
) -> str:
    """
    Genera un reporte Markdown completo.

    Args:
        lab: Laboratorio activo.
        documents: Documentos cargados en la sesión.
        findings: Hechos observados (lista de strings Markdown).
        hypotheses: Hipótesis no confirmadas.
        recommendations: Recomendaciones sustentadas.
        limitations: Limitaciones del análisis.
        analyst_notes: Notas libres del analista.
        ai_provider: Nombre del proveedor de IA utilizado.

    Returns:
        Reporte completo como string Markdown.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Sección: encabezado
    sections: List[str] = [
        REPORT_HEADER,
        f"# Reporte de Análisis de Seguridad",
        f"",
        f"| Campo | Valor |",
        f"|-------|-------|",
        f"| Laboratorio | {_escape_md(lab.name)} |",
        f"| Analista | {_escape_md(lab.analyst) or '(no especificado)'} |",
        f"| Fecha de generación | {now} |",
        f"| Proveedor de IA | {_escape_md(ai_provider)} |",
        f"",
    ]

    # Sección 1: Alcance
    sections += [
        "## 1. Alcance",
        "",
        lab.description,
        "",
    ]
    if lab.scope:
        sections += [
            "**Alcance técnico definido:**",
            "",
            lab.scope,
            "",
        ]

    # Sección 2: Documentos y evidencias analizadas
    sections += [
        "## 2. Documentos y Evidencias Analizadas",
        "",
    ]
    if documents:
        for doc in documents:
            status = "✅" if doc.ok else "❌"
            sections.append(
                f"- {status} **{_escape_md(doc.filename)}** "
                f"(tipo: {doc.file_type}, fragmentos: {len(doc.chunks)})"
                + (f" — ⚠️ {doc.error}" if doc.error else "")
            )
    else:
        sections.append("*(No se cargaron documentos en esta sesión.)*")
    sections.append("")

    # Sección 3: Hallazgos
    sections += [
        "## 3. Hallazgos",
        "",
        "> **Nota:** Los hechos observados están sustentados en las evidencias cargadas. "
        "Las hipótesis son inferencias no confirmadas que requieren validación adicional.",
        "",
    ]

    sections.append("### 3.1 Hechos Observados")
    sections.append("")
    if findings:
        for f in findings:
            sections.append(f"- {f}")
    else:
        sections.append("*(No se registraron hechos observados.)*")
    sections.append("")

    sections.append("### 3.2 Hipótesis (no confirmadas)")
    sections.append("")
    if hypotheses:
        for h in hypotheses:
            sections.append(f"- *Hipótesis:* {h}")
    else:
        sections.append("*(No se registraron hipótesis.)*")
    sections.append("")

    # Sección 4: Recomendaciones
    sections += [
        "## 4. Recomendaciones",
        "",
        "> Las recomendaciones se basan en las evidencias y el contexto del laboratorio. "
        "Deben ser revisadas por un analista antes de aplicarse.",
        "",
    ]
    if recommendations:
        for i, r in enumerate(recommendations, 1):
            sections.append(f"{i}. {r}")
    else:
        sections.append("*(No se generaron recomendaciones.)*")
    sections.append("")

    # Sección 5: Limitaciones
    sections += [
        "## 5. Limitaciones y Advertencias",
        "",
    ]
    default_limitations = [
        "Este análisis se basa únicamente en los documentos y logs cargados en la sesión.",
        "No se ejecutaron escaneos ni herramientas de verificación activa.",
        "Las vulnerabilidades no están confirmadas a menos que se indique explícitamente.",
        "El sistema no modifica ni remedia ningún sistema.",
    ]
    all_limitations = default_limitations + (limitations or [])
    for lim in all_limitations:
        sections.append(f"- {lim}")
    sections.append("")

    # Sección 6: Notas del analista
    if analyst_notes.strip():
        sections += [
            "## 6. Notas del Analista",
            "",
            analyst_notes.strip(),
            "",
        ]

    sections.append("---")
    sections.append(f"*Reporte generado por AstraSec AI · {now}*")

    return "\n".join(sections)


def _escape_md(text: str) -> str:
    """Escapa caracteres especiales de Markdown en valores de tabla."""
    return text.replace("|", "\\|")
