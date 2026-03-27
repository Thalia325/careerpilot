from __future__ import annotations

from pathlib import Path

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def _ensure_font() -> str:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in candidates:
        font_path = Path(path)
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("CareerPilotFont", str(font_path)))
                return "CareerPilotFont"
            except Exception:
                continue
    return "Helvetica"


def export_markdown_to_pdf(markdown_content: str, output_path: Path) -> None:
    font_name = _ensure_font()
    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    pdf.setFont(font_name, 12)
    y = 800
    for line in markdown_content.splitlines():
        if y < 60:
            pdf.showPage()
            pdf.setFont(font_name, 12)
            y = 800
        pdf.drawString(40, y, line[:80])
        y -= 18
    pdf.save()


def export_markdown_to_docx(markdown_content: str, output_path: Path) -> None:
    doc = Document()
    for line in markdown_content.splitlines():
        doc.add_paragraph(line)
    doc.save(str(output_path))

