"""Tests for US-001: Multi-type file upload storage and metadata."""

import io
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient


def _auth_headers(user_id: int = 1) -> dict:
    """Return dev-bypass auth headers for the given user."""
    return {"Authorization": "Bearer dev-bypass"}


def _make_upload_payload(
    filename: str = "resume.pdf",
    content: bytes = b"%PDF-1.4 test content",
    owner_id: int = 1,
    file_type: str = "resume",
    content_type: str = "application/pdf",
):
    return {
        "files": ("upload", (filename, content, content_type)),
        "data": {"owner_id": str(owner_id), "file_type": file_type},
    }


class TestFileUploadValidation:
    """Test file type and extension validation on upload."""

    def test_upload_pdf_resume(self, client: TestClient, prepare_database):
        payload = _make_upload_payload("resume.pdf", file_type="resume")
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("resume.pdf", b"%PDF-1.4 test", "application/pdf"))],
            data={"owner_id": "1", "file_type": "resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "id" in data
        assert data["file_name"].endswith(".pdf")
        assert data["file_type"] == "resume"
        assert data["created_at"] is not None
        assert "url" in data

    def test_upload_docx(self, client: TestClient, prepare_database):
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("doc.docx", b"PK\x03\x04test", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))],
            data={"owner_id": "1", "file_type": "resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200

    def test_upload_doc(self, client: TestClient, prepare_database):
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("old.doc", b"\xd0\xcf\x11\xe0test", "application/msword"))],
            data={"owner_id": "1", "file_type": "certificate"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200

    def test_upload_png(self, client: TestClient, prepare_database):
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("scan.png", b"\x89PNG\r\n\x1a\ntest", "image/png"))],
            data={"owner_id": "1", "file_type": "certificate"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200

    def test_upload_jpg(self, client: TestClient, prepare_database):
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("photo.jpg", b"\xff\xd8\xff\xe0test", "image/jpeg"))],
            data={"owner_id": "1", "file_type": "other"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200

    def test_upload_jpeg(self, client: TestClient, prepare_database):
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("photo.jpeg", b"\xff\xd8\xff\xe0test", "image/jpeg"))],
            data={"owner_id": "1", "file_type": "transcript"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200

    def test_reject_txt_extension(self, client: TestClient, prepare_database):
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("notes.txt", b"hello", "text/plain"))],
            data={"owner_id": "1", "file_type": "resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 400

    def test_reject_unsupported_extension(self, client: TestClient, prepare_database):
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("file.xyz", b"binary", "application/octet-stream"))],
            data={"owner_id": "1", "file_type": "resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 400


class TestFileTypeLabelValidation:
    """Test file_type label validation: resume, certificate, transcript, other."""

    @pytest.mark.parametrize("valid_type", ["resume", "certificate", "transcript", "other"])
    def test_accept_valid_file_type(self, client: TestClient, prepare_database, valid_type):
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("file.pdf", b"%PDF-1.4 test", "application/pdf"))],
            data={"owner_id": "1", "file_type": valid_type},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["file_type"] == valid_type

    def test_reject_invalid_file_type(self, client: TestClient, prepare_database):
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("file.pdf", b"%PDF-1.4 test", "application/pdf"))],
            data={"owner_id": "1", "file_type": "invalid_type"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 400


class TestFileSizeLimit:
    """Test 10MB file size limit."""

    def test_reject_file_over_10mb(self, client: TestClient, prepare_database):
        big_content = b"x" * (10 * 1024 * 1024 + 1)
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("big.pdf", big_content, "application/pdf"))],
            data={"owner_id": "1", "file_type": "resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 413

    def test_accept_file_at_10mb(self, client: TestClient, prepare_database):
        content = b"x" * (10 * 1024 * 1024)
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("max.pdf", content, "application/pdf"))],
            data={"owner_id": "1", "file_type": "resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200


class TestUploadResponseFields:
    """Test that upload response returns all required metadata fields."""

    def test_response_contains_all_fields(self, client: TestClient, prepare_database):
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("resume.pdf", b"%PDF-1.4 test", "application/pdf"))],
            data={"owner_id": "1", "file_type": "resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        # Required fields: 文件 ID、文件名、文件类型、上传时间和访问地址
        assert isinstance(data["id"], int)
        assert isinstance(data["file_name"], str)
        assert data["file_type"] == "resume"
        assert isinstance(data["created_at"], str)
        assert isinstance(data["url"], str)

    def test_reject_empty_file(self, client: TestClient, prepare_database):
        resp = client.post(
            "/api/v1/files/upload",
            files=[("upload", ("empty.pdf", b"", "application/pdf"))],
            data={"owner_id": "1", "file_type": "resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 400
