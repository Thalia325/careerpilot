import io

import pytest
from docx import Document

from app.integrations.ocr.providers import (
    MockOCRProvider,
    OCRParseError,
    OCRServiceError,
    OCRNetworkError,
)


def _build_docx(text: str) -> bytes:
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


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


# --- OCR Error Classification Tests ---


@pytest.mark.asyncio
async def test_mock_ocr_raises_parse_error_for_empty_pdf():
    """MockOCRProvider should raise OCRParseError when PDF text extraction yields nothing."""
    provider = MockOCRProvider()
    with pytest.raises(OCRParseError) as exc_info:
        await provider.parse_document(
            "resume.pdf",
            b"%PDF-1.4\n%empty content",
            document_type="resume",
        )
    assert exc_info.value.error_code == "parse_error"
    assert exc_info.value.retryable is False


@pytest.mark.asyncio
async def test_mock_ocr_raises_parse_error_for_empty_docx():
    """MockOCRProvider should raise OCRParseError for empty DOCX files."""
    provider = MockOCRProvider()
    with pytest.raises(OCRParseError) as exc_info:
        await provider.parse_document(
            "resume.docx",
            b"PK\x03\x04",  # ZIP header but no content
            document_type="resume",
        )
    assert exc_info.value.error_code == "parse_error"
    assert exc_info.value.retryable is False


@pytest.mark.asyncio
async def test_mock_ocr_raises_parse_error_for_empty_bytes():
    """MockOCRProvider should raise OCRParseError when raw bytes are empty."""
    provider = MockOCRProvider()
    with pytest.raises(OCRParseError) as exc_info:
        await provider.parse_document(
            "unknown.bin",
            b"",
            document_type="resume",
        )
    assert exc_info.value.error_code == "parse_error"


@pytest.mark.asyncio
async def test_mock_ocr_succeeds_with_raw_text():
    """MockOCRProvider should succeed when raw_text is provided."""
    provider = MockOCRProvider()
    result = await provider.parse_document(
        "manual_input.txt",
        b"",
        document_type="resume",
        raw_text="姓名：张三\n技能：Python",
    )
    assert result["structured_json"]["name"] == "张三"
    assert "Python" in result["structured_json"]["skills"]


def test_ocr_parse_error_attributes():
    """OCRParseError should have correct error_code and retryable."""
    err = OCRParseError("custom message")
    assert err.error_code == "parse_error"
    assert err.retryable is False
    assert err.message == "custom message"
    d = err.to_dict()
    assert d["error_code"] == "parse_error"
    assert d["retryable"] is False
    assert d["message"] == "custom message"


def test_ocr_service_error_attributes():
    """OCRServiceError should be retryable."""
    err = OCRServiceError("service down")
    assert err.error_code == "service_error"
    assert err.retryable is True
    assert err.message == "service down"


def test_ocr_network_error_attributes():
    """OCRNetworkError should be retryable."""
    err = OCRNetworkError("timeout")
    assert err.error_code == "network_error"
    assert err.retryable is True
    assert err.message == "timeout"


@pytest.mark.asyncio
async def test_paddle_ocr_raises_service_error_on_500(monkeypatch):
    """PaddleOCRProvider should raise OCRServiceError when the service returns 500."""
    import httpx

    from app.integrations.ocr.providers import PaddleOCRProvider

    mock_response = httpx.Response(500, request=httpx.Request("POST", "http://test"))
    mock_response._content = b"Internal Server Error"

    async def mock_post(*args, **kwargs):
        raise httpx.HTTPStatusError("Server Error", request=mock_response.request, response=mock_response)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    provider = PaddleOCRProvider(service_url="http://localhost:9999")
    with pytest.raises(OCRServiceError) as exc_info:
        await provider.parse_document("test.pdf", b"content")
    assert exc_info.value.error_code == "service_error"
    assert exc_info.value.retryable is True
    assert "500" in exc_info.value.message


@pytest.mark.asyncio
async def test_paddle_ocr_raises_network_error_on_timeout(monkeypatch):
    """PaddleOCRProvider should raise OCRNetworkError on timeout."""
    import httpx

    from app.integrations.ocr.providers import PaddleOCRProvider

    async def mock_post(*args, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    provider = PaddleOCRProvider(service_url="http://localhost:9999")
    with pytest.raises(OCRNetworkError) as exc_info:
        await provider.parse_document("test.pdf", b"content")
    assert exc_info.value.error_code == "network_error"
    assert exc_info.value.retryable is True


@pytest.mark.asyncio
async def test_paddle_ocr_raises_network_error_on_connection_error(monkeypatch):
    """PaddleOCRProvider should raise OCRNetworkError on connection failure."""
    import httpx

    from app.integrations.ocr.providers import PaddleOCRProvider

    async def mock_post(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    provider = PaddleOCRProvider(service_url="http://localhost:9999")
    with pytest.raises(OCRNetworkError) as exc_info:
        await provider.parse_document("test.pdf", b"content")
    assert exc_info.value.error_code == "network_error"
    assert exc_info.value.retryable is True


@pytest.mark.asyncio
async def test_paddle_ocr_calls_remote_service_even_for_docx_with_text(monkeypatch):
    """Uploaded DOCX files should still hit PaddleOCR instead of short-circuiting to local parsing."""
    from app.integrations.ocr.providers import PaddleOCRProvider

    calls: list[dict] = []

    class MockResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "raw_text": "姓名：张三\n技能：Python",
                "layout_blocks": [{"section": "page_0", "text": "姓名：张三\n技能：Python"}],
                "structured_json": {
                    "document_type": "resume",
                    "name": "张三",
                    "school": "",
                    "major": "",
                    "grade": "",
                    "graduation_year": "",
                    "target_job": "",
                    "skills": ["Python"],
                    "projects": [],
                    "internships": [],
                    "certificates": [],
                    "competitions": [],
                    "self_evaluation": "",
                    "gpa": None,
                },
            }

    async def mock_post(self, url, **kwargs):
        calls.append({"url": url, "payload": kwargs.get("json")})
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
    provider = PaddleOCRProvider(service_url="http://localhost:9999")

    result = await provider.parse_document(
        "resume.docx",
        _build_docx("姓名：张三\n技能：Python"),
        document_type="resume",
    )

    assert len(calls) == 1
    assert calls[0]["payload"]["fileType"] == 0
    assert result["structured_json"]["name"] == "张三"
@pytest.mark.asyncio
async def test_paddle_ocr_retries_queue_full_then_succeeds(monkeypatch):
    """PaddleOCRProvider should retry transient 503 queue-full responses and return parsed text."""
    import httpx

    from app.integrations.ocr.providers import PaddleOCRProvider

    attempts: list[int] = []

    async def mock_post(self, url, **kwargs):
        attempts.append(len(attempts) + 1)
        request = httpx.Request("POST", url)
        if len(attempts) == 1:
            return httpx.Response(
                503,
                request=request,
                json={"errorCode": 10010, "errorMsg": "任务提交队列已满，请稍后重试"},
            )
        return httpx.Response(
            200,
            request=request,
            json={
                "result": {
                    "layoutParsingResults": [
                        {
                            "markdown": {
                                "text": "姓名：张三\n技能：Python SQL\n项目：职业规划系统",
                            }
                        }
                    ]
                }
            },
        )

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
    monkeypatch.setattr("asyncio.sleep", no_sleep)
    provider = PaddleOCRProvider(
        service_url="http://localhost:9999",
        max_retries=3,
        retry_base_delay_seconds=0.01,
    )

    result = await provider.parse_document("resume.pdf", b"content", document_type="resume")

    assert attempts == [1, 2]
    assert result["structured_json"]["name"] == "张三"
    assert "Python" in result["structured_json"]["skills"]
