"""
Pruebas unitarias del módulo report.py
"""
from app.core.lab import create_laboratory
from app.core.ingest import ingest_file
from app.core.report import generate_report


def _make_lab():
    return create_laboratory("Lab-Test-Reporte", "Laboratorio ficticio para pruebas de reporte.")


def _make_docs():
    doc = ingest_file("evidencia.txt", b"Log de autenticacion fallida para usuario admin.")
    return [doc]


# ---- estructura del reporte ----

def test_report_contains_required_sections():
    lab = _make_lab()
    report = generate_report(
        lab=lab,
        documents=_make_docs(),
        findings=["Se detectaron 5 intentos fallidos"],
        hypotheses=["Podría ser un ataque de fuerza bruta"],
        recommendations=["Habilitar bloqueo de cuenta"],
        limitations=[],
    )
    assert "# Reporte de Análisis de Seguridad" in report
    assert "## 1. Alcance" in report
    assert "## 2. Documentos y Evidencias" in report
    assert "## 3. Hallazgos" in report
    assert "## 4. Recomendaciones" in report
    assert "## 5. Limitaciones" in report


def test_report_contains_lab_name():
    lab = _make_lab()
    report = generate_report(lab=lab, documents=[], findings=[], hypotheses=[], recommendations=[], limitations=[])
    assert "Lab-Test-Reporte" in report


def test_report_contains_findings():
    lab = _make_lab()
    report = generate_report(
        lab=lab, documents=[], findings=["Hecho observado número uno"], hypotheses=[], recommendations=[], limitations=[]
    )
    assert "Hecho observado número uno" in report


def test_report_contains_hypotheses():
    lab = _make_lab()
    report = generate_report(
        lab=lab, documents=[], findings=[], hypotheses=["Hipótesis de prueba"], recommendations=[], limitations=[]
    )
    assert "Hipótesis de prueba" in report
    assert "Hipótesis" in report  # sección de hipótesis


def test_report_contains_recommendations():
    lab = _make_lab()
    report = generate_report(
        lab=lab, documents=[], findings=[], hypotheses=[], recommendations=["Recomendación de prueba"], limitations=[]
    )
    assert "Recomendación de prueba" in report


def test_report_contains_default_limitations():
    lab = _make_lab()
    report = generate_report(lab=lab, documents=[], findings=[], hypotheses=[], recommendations=[], limitations=[])
    assert "No se ejecutaron escaneos" in report


def test_report_contains_analyst_notes():
    lab = _make_lab()
    report = generate_report(
        lab=lab, documents=[], findings=[], hypotheses=[], recommendations=[], limitations=[],
        analyst_notes="Nota adicional del analista."
    )
    assert "Nota adicional del analista." in report
    assert "## 6. Notas del Analista" in report


def test_report_no_analyst_notes_no_section():
    lab = _make_lab()
    report = generate_report(lab=lab, documents=[], findings=[], hypotheses=[], recommendations=[], limitations=[])
    assert "## 6. Notas del Analista" not in report


def test_report_contains_disclaimer_comment():
    lab = _make_lab()
    report = generate_report(lab=lab, documents=[], findings=[], hypotheses=[], recommendations=[], limitations=[])
    assert "AVISO" in report


def test_report_contains_document_list():
    lab = _make_lab()
    docs = _make_docs()
    report = generate_report(lab=lab, documents=docs, findings=[], hypotheses=[], recommendations=[], limitations=[])
    assert "evidencia.txt" in report


def test_report_marks_empty_documents():
    lab = _make_lab()
    report = generate_report(lab=lab, documents=[], findings=[], hypotheses=[], recommendations=[], limitations=[])
    assert "No se cargaron documentos" in report
