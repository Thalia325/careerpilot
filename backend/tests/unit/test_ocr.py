import pytest

from app.integrations.ocr.providers import (
    MockOCRProvider,
    OCRParseError,
    OCRServiceError,
    OCRNetworkError,
)


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
