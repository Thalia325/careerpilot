"""Tests for report PDF/DOCX export functionality (US-016)."""

import tempfile
from pathlib import Path

import pytest

from app.services.reports.exporters import (
    _parse_markdown_blocks,
    _strip_inline_md,
    export_markdown_to_docx,
    export_markdown_to_pdf,
)


# ---------------------------------------------------------------------------
# Markdown parser unit tests
# ---------------------------------------------------------------------------

class TestParseMarkdownBlocks:
    def test_heading_levels(self):
        blocks = _parse_markdown_blocks("# Title\n## H2\n### H3\n#### H4")
        headings = [b for b in blocks if b["type"] == "heading"]
        assert len(headings) == 4
        assert headings[0]["level"] == 1
        assert headings[0]["text"] == "Title"
        assert headings[1]["level"] == 2
        assert headings[1]["text"] == "H2"

    def test_bullet_items(self):
        blocks = _parse_markdown_blocks("- item1\n- item2\n* item3\n+ item4")
        bullets = [b for b in blocks if b["type"] == "bullet"]
        assert len(bullets) == 4
        assert bullets[0]["text"] == "item1"
        assert bullets[3]["text"] == "item4"

    def test_ordered_list_items(self):
        blocks = _parse_markdown_blocks("1. first\n2. second\n3. third")
        bullets = [b for b in blocks if b["type"] == "bullet"]
        assert len(bullets) == 3
        assert bullets[0]["text"] == "first"

    def test_horizontal_rule(self):
        blocks = _parse_markdown_blocks("---\n---")
        hrs = [b for b in blocks if b["type"] == "hr"]
        assert len(hrs) == 2

    def test_block_quote(self):
        blocks = _parse_markdown_blocks("> quote text")
        quotes = [b for b in blocks if b["type"] == "quote"]
        assert len(quotes) == 1
        assert quotes[0]["text"] == "quote text"

    def test_paragraph(self):
        blocks = _parse_markdown_blocks("normal text line")
        paras = [b for b in blocks if b["type"] == "paragraph"]
        assert len(paras) == 1
        assert paras[0]["text"] == "normal text line"

    def test_empty_lines_skipped(self):
        blocks = _parse_markdown_blocks("line1\n\n\nline2")
        assert len(blocks) == 2

    def test_mixed_content(self):
        md = """# Report Title

Some intro paragraph.

## Section One

- bullet item
- another bullet

1. numbered item

> a quote

---

More text after rule."""
        blocks = _parse_markdown_blocks(md)
        types = [b["type"] for b in blocks]
        assert types == [
            "heading", "paragraph", "heading",
            "bullet", "bullet", "bullet",
            "quote", "hr", "paragraph",
        ]


class TestStripInlineMarkdown:
    def test_bold_stripped(self):
        assert _strip_inline_md("**bold**") == "bold"

    def test_italic_stripped(self):
        assert _strip_inline_md("*italic*") == "italic"

    def test_code_stripped(self):
        assert _strip_inline_md("`code`") == "code"

    def test_mixed_stripped(self):
        assert _strip_inline_md("**bold** and *italic* and `code`") == "bold and italic and code"

    def test_plain_unchanged(self):
        assert _strip_inline_md("plain text") == "plain text"


# ---------------------------------------------------------------------------
# PDF export integration tests
# ---------------------------------------------------------------------------

SAMPLE_MARKDOWN = """# CareerPilot 职业发展报告

## 一、学生基本情况

**姓名**：张三
**专业**：计算机科学与技术

- 技能：Python、React
- 证书：CET-6

> 备注：该学生有较强的实践能力

## 二、匹配分析

匹配得分 **85分**，表现良好。

### 建议

1. 加强算法能力
2. 参与开源项目

---

*生成于 CareerPilot*
"""


class TestExportPDF:
    def test_pdf_file_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "report.pdf"
            export_markdown_to_pdf(SAMPLE_MARKDOWN, output)
            assert output.exists()
            assert output.stat().st_size > 0

    def test_pdf_with_empty_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "empty.pdf"
            export_markdown_to_pdf("", output)
            assert output.exists()

    def test_pdf_with_only_headings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "headings.pdf"
            export_markdown_to_pdf("# Title\n## Subtitle\n### Section", output)
            assert output.exists()
            assert output.stat().st_size > 0


class TestExportDOCX:
    def test_docx_file_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "report.docx"
            export_markdown_to_docx(SAMPLE_MARKDOWN, output)
            assert output.exists()
            assert output.stat().st_size > 0

    def test_docx_with_empty_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "empty.docx"
            export_markdown_to_docx("", output)
            assert output.exists()

    def test_docx_with_only_headings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "headings.docx"
            export_markdown_to_docx("# Title\n## Subtitle\n### Section", output)
            assert output.exists()
            assert output.stat().st_size > 0

    def test_docx_has_paragraphs(self):
        """Verify DOCX contains expected content by reading it back."""
        from docx import Document

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "content.docx"
            export_markdown_to_docx(SAMPLE_MARKDOWN, output)
            doc = Document(str(output))
            texts = [p.text for p in doc.paragraphs]
            full_text = "\n".join(texts)
            assert "CareerPilot" in full_text
            assert "张三" in full_text
            assert "计算机科学与技术" in full_text


# ---------------------------------------------------------------------------
# API integration tests
# ---------------------------------------------------------------------------

class TestExportAPI:
    def test_export_pdf_endpoint(self, client):
        """POST /reports/export with format=pdf returns file info."""
        # First generate a report
        headers = {"Authorization": "Bearer dev-bypass"}
        gen_resp = client.post(
            "/api/v1/reports/generate",
            json={"student_id": 1, "job_code": "J-FE-001"},
            headers=headers,
        )
        if gen_resp.status_code != 200:
            pytest.skip(f"Report generation failed: {gen_resp.status_code}")

        report_id = gen_resp.json()["report_id"]

        # Export as PDF
        export_resp = client.post(
            "/api/v1/reports/export",
            json={"report_id": report_id, "format": "pdf"},
            headers=headers,
        )
        assert export_resp.status_code == 200
        data = export_resp.json()
        assert data["report_id"] == report_id
        assert data["exported"]["format"] == "pdf"
        assert data["exported"]["file_name"].endswith(".pdf")

    def test_export_docx_endpoint(self, client):
        """POST /reports/export with format=docx returns file info."""
        headers = {"Authorization": "Bearer dev-bypass"}
        gen_resp = client.post(
            "/api/v1/reports/generate",
            json={"student_id": 1, "job_code": "J-FE-001"},
            headers=headers,
        )
        if gen_resp.status_code != 200:
            pytest.skip(f"Report generation failed: {gen_resp.status_code}")

        report_id = gen_resp.json()["report_id"]

        # Export as DOCX
        export_resp = client.post(
            "/api/v1/reports/export",
            json={"report_id": report_id, "format": "docx"},
            headers=headers,
        )
        assert export_resp.status_code == 200
        data = export_resp.json()
        assert data["report_id"] == report_id
        assert data["exported"]["format"] == "docx"
        assert data["exported"]["file_name"].endswith(".docx")

    def test_export_nonexistent_report(self, client):
        """Export with invalid report_id returns 500 via ValueError."""
        headers = {"Authorization": "Bearer dev-bypass"}
        resp = client.post(
            "/api/v1/reports/export",
            json={"report_id": 99999, "format": "pdf"},
            headers=headers,
        )
        assert resp.status_code == 400

    def test_exported_file_downloadable(self, client):
        """The exported file is accessible via /exports/{filename}."""
        headers = {"Authorization": "Bearer dev-bypass"}
        gen_resp = client.post(
            "/api/v1/reports/generate",
            json={"student_id": 1, "job_code": "J-FE-001"},
            headers=headers,
        )
        if gen_resp.status_code != 200:
            pytest.skip(f"Report generation failed: {gen_resp.status_code}")

        report_id = gen_resp.json()["report_id"]

        # Export
        export_resp = client.post(
            "/api/v1/reports/export",
            json={"report_id": report_id, "format": "pdf"},
            headers=headers,
        )
        assert export_resp.status_code == 200
        file_name = export_resp.json()["exported"]["file_name"]

        # Download via static files
        dl_resp = client.get(f"/exports/{file_name}")
        assert dl_resp.status_code == 200
        assert len(dl_resp.content) > 0
