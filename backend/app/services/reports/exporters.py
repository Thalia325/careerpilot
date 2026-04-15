"""Export career reports from Markdown to PDF and DOCX with proper formatting."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ---------------------------------------------------------------------------
# Shared Markdown → structured-blocks parser
# ---------------------------------------------------------------------------

def _parse_markdown_blocks(md: str) -> list[dict]:
    """Split markdown into structured blocks: headings, bullets, paragraphs, rules."""
    blocks: list[dict] = []
    for line in md.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Horizontal rule
        if re.match(r"^-{3,}$", stripped):
            blocks.append({"type": "hr"})
            continue

        # Heading (## Title or ### Title)
        h_match = re.match(r"^(#{1,6})\s+(.*)", stripped)
        if h_match:
            level = len(h_match.group(1))
            text = h_match.group(2).strip()
            blocks.append({"type": "heading", "level": level, "text": text})
            continue

        # Unordered list item
        if re.match(r"^[-*+]\s+", stripped):
            text = re.sub(r"^[-*+]\s+", "", stripped)
            blocks.append({"type": "bullet", "text": text})
            continue

        # Ordered list item
        o_match = re.match(r"^\d+\.\s+(.*)", stripped)
        if o_match:
            blocks.append({"type": "bullet", "text": o_match.group(1)})
            continue

        # Block quote
        if stripped.startswith(">"):
            text = stripped.lstrip(">").strip()
            blocks.append({"type": "quote", "text": text})
            continue

        # Regular paragraph
        blocks.append({"type": "paragraph", "text": stripped})
    return blocks


def _strip_inline_md(text: str) -> str:
    """Remove inline markdown markers (bold, italic, code) for plain text."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------

_font_cache: str | None = None


def _ensure_font() -> str:
    global _font_cache
    if _font_cache:
        return _font_cache

    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in candidates:
        font_path = Path(path)
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("CareerPilotFont", str(font_path)))
                _font_cache = "CareerPilotFont"
                return _font_cache
            except Exception:
                continue
    _font_cache = "Helvetica"
    return _font_cache


def _md_to_reportlab_inline(text: str) -> str:
    """Convert inline markdown bold/italic to reportlab XML tags."""
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    # Code
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    return text


def export_markdown_to_pdf(markdown_content: str, output_path: Path) -> None:
    font_name = _ensure_font()

    styles = {
        "title": ParagraphStyle(
            "Title", fontName=font_name, fontSize=18, leading=26,
            spaceAfter=8 * mm, alignment=1,
        ),
        "h1": ParagraphStyle(
            "H1", fontName=font_name, fontSize=16, leading=22,
            spaceBefore=6 * mm, spaceAfter=4 * mm,
        ),
        "h2": ParagraphStyle(
            "H2", fontName=font_name, fontSize=14, leading=20,
            spaceBefore=5 * mm, spaceAfter=3 * mm,
        ),
        "h3": ParagraphStyle(
            "H3", fontName=font_name, fontSize=12, leading=18,
            spaceBefore=4 * mm, spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "Body", fontName=font_name, fontSize=10, leading=16,
            spaceAfter=2 * mm,
        ),
        "bullet": ParagraphStyle(
            "Bullet", fontName=font_name, fontSize=10, leading=16,
            leftIndent=12 * mm, spaceAfter=1 * mm,
        ),
        "quote": ParagraphStyle(
            "Quote", fontName=font_name, fontSize=10, leading=16,
            leftIndent=8 * mm, textColor="grey",
        ),
    }

    blocks = _parse_markdown_blocks(markdown_content)
    story: list = []

    for block in blocks:
        btype = block["type"]

        if btype == "hr":
            story.append(Spacer(1, 3 * mm))
            continue

        text = block["text"]
        if btype == "heading":
            level = block["level"]
            if level == 1:
                style = styles["title"] if len(story) == 0 else styles["h1"]
            elif level == 2:
                style = styles["h2"]
            else:
                style = styles["h3"]
            story.append(Paragraph(_md_to_reportlab_inline(text), style))
            continue

        if btype == "bullet":
            safe = _md_to_reportlab_inline(f"- {text}")
            story.append(Paragraph(safe, styles["bullet"]))
            continue

        if btype == "quote":
            story.append(Paragraph(_md_to_reportlab_inline(text), styles["quote"]))
            continue

        # paragraph
        story.append(Paragraph(_md_to_reportlab_inline(text), styles["body"]))

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )
    doc.build(story)


# ---------------------------------------------------------------------------
# DOCX export
# ---------------------------------------------------------------------------

def export_markdown_to_docx(markdown_content: str, output_path: Path) -> None:
    doc = Document()

    # Set default font size
    style = doc.styles["Normal"]
    font = style.font
    font.size = Pt(10.5)
    font.name = "Microsoft YaHei"

    blocks = _parse_markdown_blocks(markdown_content)

    for block in blocks:
        btype = block["type"]

        if btype == "hr":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run("—")
            continue

        text = block["text"]
        if btype == "heading":
            level = block["level"]
            heading_level = min(level, 4)  # docx supports 1-4 practically
            p = doc.add_heading(level=heading_level)
            _add_inline_runs(p, text)
            continue

        if btype == "bullet":
            p = doc.add_paragraph(style="List Bullet")
            _add_inline_runs(p, text)
            continue

        if btype == "quote":
            p = doc.add_paragraph()
            p.style = doc.styles["Normal"]
            run = p.add_run(text)
            run.italic = True
            continue

        # paragraph
        p = doc.add_paragraph()
        _add_inline_runs(p, text)

    doc.save(str(output_path))


def _add_inline_runs(paragraph, text: str) -> None:
    """Parse bold/italic/code markers in *text* and add corresponding runs."""
    # Split on **bold**, *italic*, `code` patterns
    parts = re.split(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)", text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("*") and part.endswith("*"):
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Courier New"
        else:
            paragraph.add_run(part)
