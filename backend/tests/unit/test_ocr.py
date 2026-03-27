import pytest

from app.integrations.ocr.providers import MockOCRProvider


@pytest.mark.asyncio
async def test_mock_ocr_structured_output():
    provider = MockOCRProvider()
    result = await provider.parse_document(
        "resume.txt",
        "姓名：陈同学\n专业：软件工程\n技能：Python React SQL\n证书：英语四级".encode("utf-8"),
        document_type="resume",
    )
    assert "raw_text" in result
    assert "layout_blocks" in result
    assert result["structured_json"]["skills"] == ["Python", "React", "SQL"]
    assert "英语四级" in result["structured_json"]["certificates"]
