from io import BytesIO
from html import escape
import re
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def generate_pdf(markdown: str) -> bytes:
    """Render the generated report locally; never interpret embedded HTML or fetch URLs."""
    output = BytesIO()
    styles = getSampleStyleSheet()
    for name in ('Normal', 'BodyText'):
        styles[name].fontSize = 10
        styles[name].leading = 15
        styles[name].spaceAfter = 7
        styles[name].splitLongWords = True
    styles['Title'].textColor = colors.HexColor('#15344b')
    styles['Heading2'].textColor = colors.HexColor('#15344b')
    styles['Heading2'].keepWithNext = True
    styles['Heading3'].keepWithNext = True
    story = []
    text = re.sub(r'<!--.*?-->', '', markdown, flags=re.S)
    replacements = {'✅': '[OK]', '❌': '[ERROR]', '⚠️': '[AVISO]', '—': '-', '–': '-'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    for line in text.splitlines():
        line = line.strip()
        if not line or line == '---' or re.fullmatch(r'[| :\-]+', line):
            continue
        style = 'BodyText'
        if line.startswith('# '):
            style, line = 'Title', line[2:]
        elif line.startswith('### '):
            style, line = 'Heading3', line[4:]
        elif line.startswith('## '):
            style, line = 'Heading2', line[3:]
        elif line.startswith('|'):
            cells = re.split(r'(?<!\\)\|', line.strip('|'))
            line = ': '.join(c.strip().replace('\\|', '|') for c in cells)
        elif line.startswith('> '):
            line = line[2:]
        line = line.replace('**', '').replace('*', '').replace('`', '')
        story.append(Paragraph(escape(line), styles[style]))
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#526372'))
        canvas.drawString(42, 25, 'AstraSec AI - Reporte local')
        canvas.drawRightString(A4[0] - 42, 25, f'Página {doc.page}')
        canvas.restoreState()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=42, leftMargin=42,
                            topMargin=42, bottomMargin=45, title='Reporte AstraSec AI')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
