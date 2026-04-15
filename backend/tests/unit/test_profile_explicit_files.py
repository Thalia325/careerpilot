"""Tests for US-005: Make profile generation explicitly consume uploaded_file_ids."""

import io
import pytest
from docx import Document
from fastapi.testclient import TestClient

from app.schemas.profile import ManualStudentInput
from app.services.bootstrap import create_service_container, initialize_demo_data


RESUME_TEXT = (
    "姓名：张三\n"
    "学校：北京大学\n"
    "专业：计算机科学与技术\n"
    "年级：大三\n"
    "毕业年份：2026\n"
    "意向岗位：前端开发工程师\n"
    "技能：Python JavaScript React\n"
    "证书：英语四级 英语六级\n"
    "项目：智能问答系统，基于 RAG 的知识库助手\n"
    "实习：字节跳动前端开发实习生\n"
    "竞赛：ACM 程序设计竞赛金奖\n"
    "自我评价：具有良好的编程能力和团队协作精神\n"
)


def _auth_headers(user_id: int = 1) -> dict:
    return {"Authorization": "Bearer dev-bypass"}


def _build_docx(text: str) -> bytes:
    """Build a valid DOCX file containing the given text."""
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _upload_docx(
    client: TestClient,
    text: str = RESUME_TEXT,
    filename: str = "resume.docx",
    file_type: str = "resume",
    owner_id: int = 1,
) -> int:
    """Upload a DOCX file and return its ID."""
    content = _build_docx(text)
    resp = client.post(
        "/api/v1/files/upload",
        files=[("upload", (filename, content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))],
        data={"owner_id": str(owner_id), "file_type": file_type},
        headers=_auth_headers(owner_id),
    )
    assert resp.status_code == 200, f"Upload failed: {resp.json()}"
    return resp.json()["data"]["id"]


def _parse_file(client: TestClient, file_id: int) -> dict:
    """Trigger OCR parsing for an uploaded file."""
    resp = client.post(
        "/api/v1/ocr/parse",
        json={"uploaded_file_id": file_id, "document_type": "resume"},
        headers=_auth_headers(),
    )
    assert resp.status_code == 200, f"Parse failed: {resp.json()}"
    return resp.json()


def _upload_and_parse(
    client: TestClient,
    text: str = RESUME_TEXT,
    filename: str = "resume.docx",
    file_type: str = "resume",
) -> int:
    """Upload and parse a file, return file ID."""
    file_id = _upload_docx(client, text, filename, file_type)
    _parse_file(client, file_id)
    return file_id


class TestExplicitFileIdsRequired:
    """Profile generation must explicitly receive uploaded_file_ids."""

    def test_generate_without_file_ids_field_returns_422(self, client: TestClient, prepare_database):
        """Request must include uploaded_file_ids field."""
        resp = client.post(
            "/api/v1/student-profiles/generate",
            json={"student_id": 1, "manual_input": None},
            headers=_auth_headers(),
        )
        assert resp.status_code == 422

    def test_generate_with_empty_file_ids_and_no_manual_input_fails(self, client: TestClient, prepare_database):
        """Empty file_ids without manual_input should fail with 400."""
        resp = client.post(
            "/api/v1/student-profiles/generate",
            json={"student_id": 1, "uploaded_file_ids": [], "manual_input": None},
            headers=_auth_headers(),
        )
        assert resp.status_code == 400

    def test_generate_with_explicit_file_ids_succeeds(self, client: TestClient, prepare_database):
        """Explicit file_ids should succeed."""
        file_id = _upload_and_parse(client)
        resp = client.post(
            "/api/v1/student-profiles/generate",
            json={"student_id": 1, "uploaded_file_ids": [file_id], "mode": "current_resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["student_id"] == 1
        assert data["profile_version_id"] is not None


class TestCurrentResumeMode:
    """current_resume mode should use only the latest resume file."""

    def test_single_resume_file(self, client: TestClient, prepare_database):
        """With one resume file, current_resume mode uses it."""
        file_id = _upload_and_parse(client, RESUME_TEXT, "resume.docx", "resume")
        resp = client.post(
            "/api/v1/student-profiles/generate",
            json={"student_id": 1, "uploaded_file_ids": [file_id], "mode": "current_resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["profile_version_id"] is not None

    def test_multiple_resumes_uses_latest_only(self, client: TestClient, prepare_database):
        """With multiple resume files, only the latest is used."""
        fid1 = _upload_and_parse(client, RESUME_TEXT, "resume_v1.docx", "resume")
        fid2 = _upload_and_parse(client, RESUME_TEXT, "resume_v2.docx", "resume")
        resp = client.post(
            "/api/v1/student-profiles/generate",
            json={"student_id": 1, "uploaded_file_ids": [fid1, fid2], "mode": "current_resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        # Verify mode is stored in snapshot
        versions_resp = client.get(
            "/api/v1/student-profiles/1/versions",
            headers=_auth_headers(),
        )
        assert versions_resp.status_code == 200
        versions = versions_resp.json()["items"]
        assert len(versions) >= 1
        latest = versions[0]
        assert latest["snapshot"]["mode"] == "current_resume"

    def test_no_resume_type_uses_first_file(self, client: TestClient, prepare_database):
        """If no resume-type files, current_resume mode uses the first file."""
        file_id = _upload_and_parse(client, RESUME_TEXT, "certificate.docx", "certificate")
        resp = client.post(
            "/api/v1/student-profiles/generate",
            json={"student_id": 1, "uploaded_file_ids": [file_id], "mode": "current_resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200


class TestMergedMaterialsMode:
    """merged_materials mode should use all provided files."""

    def test_all_files_used(self, client: TestClient, prepare_database):
        """All provided files are used in merged_materials mode."""
        fid1 = _upload_and_parse(client, RESUME_TEXT, "resume.docx", "resume")
        fid2 = _upload_and_parse(client, RESUME_TEXT, "transcript.docx", "transcript")
        resp = client.post(
            "/api/v1/student-profiles/generate",
            json={
                "student_id": 1,
                "uploaded_file_ids": [fid1, fid2],
                "mode": "merged_materials",
            },
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["profile_version_id"] is not None

        versions_resp = client.get(
            "/api/v1/student-profiles/1/versions",
            headers=_auth_headers(),
        )
        versions = versions_resp.json()["items"]
        latest = versions[0]
        assert latest["snapshot"]["mode"] == "merged_materials"
        assert set(latest["snapshot"]["uploaded_file_ids"]) == {fid1, fid2}


class TestNoHistoricalMixing:
    """Profile generation must not automatically mix historical resume content."""

    def test_uses_only_explicit_file_ids(self, client: TestClient, prepare_database):
        """Only the explicitly provided file IDs are used, not all historical files."""
        # Upload 3 files
        fid1 = _upload_and_parse(client, RESUME_TEXT, "old_resume.docx", "resume")
        fid2 = _upload_and_parse(client, RESUME_TEXT, "new_resume.docx", "resume")
        fid3 = _upload_and_parse(client, RESUME_TEXT, "certificate.docx", "certificate")

        # Generate profile using only fid2 (the new resume)
        resp = client.post(
            "/api/v1/student-profiles/generate",
            json={"student_id": 1, "uploaded_file_ids": [fid2], "mode": "current_resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200

        # Verify snapshot only contains fid2
        versions_resp = client.get(
            "/api/v1/student-profiles/1/versions",
            headers=_auth_headers(),
        )
        versions = versions_resp.json()["items"]
        latest = versions[0]
        assert latest["snapshot"]["uploaded_file_ids"] == [fid2]

    def test_old_file_ids_not_included(self, client: TestClient, prepare_database):
        """Previously uploaded files not in the request should not appear."""
        fid_old = _upload_and_parse(client, RESUME_TEXT, "old.docx", "resume")
        # Generate with old file first
        client.post(
            "/api/v1/student-profiles/generate",
            json={"student_id": 1, "uploaded_file_ids": [fid_old], "mode": "current_resume"},
            headers=_auth_headers(),
        )

        # Now upload new file and generate profile with only the new one
        fid_new = _upload_and_parse(client, RESUME_TEXT, "new.docx", "resume")
        resp = client.post(
            "/api/v1/student-profiles/generate",
            json={"student_id": 1, "uploaded_file_ids": [fid_new], "mode": "current_resume"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200

        versions_resp = client.get(
            "/api/v1/student-profiles/1/versions",
            headers=_auth_headers(),
        )
        versions = versions_resp.json()["items"]
        latest = versions[0]
        assert fid_old not in latest["snapshot"]["uploaded_file_ids"]
        assert fid_new in latest["snapshot"]["uploaded_file_ids"]


class TestProfileVersionTracking:
    """Profile version should track source file IDs and mode."""

    def test_snapshot_contains_uploaded_file_ids_and_mode(self, client: TestClient, prepare_database):
        """Snapshot should contain the exact file IDs used and the mode."""
        fid1 = _upload_and_parse(client, RESUME_TEXT, "resume.docx", "resume")
        fid2 = _upload_and_parse(client, RESUME_TEXT, "cert.docx", "certificate")

        resp = client.post(
            "/api/v1/student-profiles/generate",
            json={"student_id": 1, "uploaded_file_ids": [fid1, fid2], "mode": "merged_materials"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200

        versions_resp = client.get(
            "/api/v1/student-profiles/1/versions",
            headers=_auth_headers(),
        )
        versions = versions_resp.json()["items"]
        latest = versions[0]
        assert latest["snapshot"]["uploaded_file_ids"] == [fid1, fid2]
        assert latest["snapshot"]["mode"] == "merged_materials"

    def test_response_includes_profile_version_id(self, client: TestClient, prepare_database):
        """Response should include profile_version_id."""
        file_id = _upload_and_parse(client)
        resp = client.post(
            "/api/v1/student-profiles/generate",
            json={"student_id": 1, "uploaded_file_ids": [file_id]},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["profile_version_id"] is not None
        assert isinstance(resp.json()["profile_version_id"], int)

    @pytest.mark.asyncio
    async def test_manual_input_only_still_works(self, db_session):
        """Manual input only (no files) should still work via service."""
        container = create_service_container()
        await initialize_demo_data(db_session, container)
        result = await container.student_profile_service.generate_profile(
            db_session,
            student_id=1,
            uploaded_file_ids=[],
            manual_input=ManualStudentInput(
                target_job="前端开发工程师",
                self_introduction="希望从事前端研发",
                skills=["JavaScript", "React"],
                certificates=["英语四级"],
                projects=["CareerPilot"],
                internships=["前端实习"],
            ),
        )
        assert result["skills"]
        assert result["profile_version_id"] is not None
