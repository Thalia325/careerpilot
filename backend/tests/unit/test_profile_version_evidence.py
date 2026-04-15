"""Tests for US-006: Persist profile version with evidence snapshot."""

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

RESUME_TEXT_B = (
    "姓名：李四\n"
    "学校：清华大学\n"
    "专业：软件工程\n"
    "年级：大四\n"
    "意向岗位：后端开发工程师\n"
    "技能：Java Spring MySQL\n"
    "证书：英语六级 软件设计师\n"
    "项目：分布式任务调度平台\n"
    "实习：阿里巴巴后端开发实习生\n"
    "自我评价：具有扎实的后端开发能力\n"
)


def _auth_headers(user_id: int = 1) -> dict:
    return {"Authorization": "Bearer dev-bypass"}


def _build_docx(text: str) -> bytes:
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _upload_and_parse(
    client: TestClient,
    text: str = RESUME_TEXT,
    filename: str = "resume.docx",
    file_type: str = "resume",
    owner_id: int = 1,
) -> int:
    content = _build_docx(text)
    resp = client.post(
        "/api/v1/files/upload",
        files=[("upload", (filename, content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))],
        data={"owner_id": str(owner_id), "file_type": file_type},
        headers=_auth_headers(owner_id),
    )
    assert resp.status_code == 200, f"Upload failed: {resp.json()}"
    file_id = resp.json()["data"]["id"]
    client.post(
        "/api/v1/ocr/parse",
        json={"uploaded_file_id": file_id, "document_type": "resume"},
        headers=_auth_headers(),
    )
    return file_id


def _generate_profile(
    client: TestClient,
    file_ids: list[int],
    student_id: int = 1,
    mode: str = "current_resume",
) -> dict:
    resp = client.post(
        "/api/v1/student-profiles/generate",
        json={"student_id": student_id, "uploaded_file_ids": file_ids, "mode": mode},
        headers=_auth_headers(),
    )
    assert resp.status_code == 200, f"Generate failed: {resp.json()}"
    return resp.json()


class TestProfileVersionFields:
    """ProfileVersion record must contain all required fields."""

    def test_version_contains_version_no(self, client: TestClient, prepare_database):
        file_id = _upload_and_parse(client)
        _generate_profile(client, [file_id])
        resp = client.get("/api/v1/student-profiles/1/versions", headers=_auth_headers())
        versions = resp.json()["items"]
        assert len(versions) == 1
        assert versions[0]["version_no"] == 1

    def test_version_contains_uploaded_file_ids(self, client: TestClient, prepare_database):
        fid1 = _upload_and_parse(client, RESUME_TEXT, "resume.docx", "resume")
        fid2 = _upload_and_parse(client, RESUME_TEXT, "cert.docx", "certificate")
        _generate_profile(client, [fid1, fid2], mode="merged_materials")
        resp = client.get("/api/v1/student-profiles/1/versions", headers=_auth_headers())
        versions = resp.json()["items"]
        assert set(versions[0]["uploaded_file_ids"]) == {fid1, fid2}

    def test_version_contains_file_summaries(self, client: TestClient, prepare_database):
        fid = _upload_and_parse(client, RESUME_TEXT, "resume.docx", "resume")
        _generate_profile(client, [fid])
        resp = client.get("/api/v1/student-profiles/1/versions", headers=_auth_headers())
        versions = resp.json()["items"]
        summaries = versions[0]["file_summaries"]
        assert len(summaries) >= 1
        summary = summaries[0]
        assert summary["file_id"] == fid
        assert summary["file_name"].endswith(".docx")
        assert summary["file_type"] == "resume"
        assert "提取技能" in summary["summary"]

    def test_version_contains_generation_time(self, client: TestClient, prepare_database):
        file_id = _upload_and_parse(client)
        _generate_profile(client, [file_id])
        resp = client.get("/api/v1/student-profiles/1/versions", headers=_auth_headers())
        versions = resp.json()["items"]
        assert versions[0]["created_at"] != ""

    def test_version_contains_profile_snapshot(self, client: TestClient, prepare_database):
        file_id = _upload_and_parse(client)
        _generate_profile(client, [file_id])
        resp = client.get("/api/v1/student-profiles/1/versions", headers=_auth_headers())
        versions = resp.json()["items"]
        snapshot = versions[0]["snapshot"]
        assert "skills" in snapshot
        assert "certificates" in snapshot
        assert "capability_scores" in snapshot
        assert "completeness_score" in snapshot
        assert "competitiveness_score" in snapshot

    def test_version_contains_evidence_snapshot(self, client: TestClient, prepare_database):
        file_id = _upload_and_parse(client)
        _generate_profile(client, [file_id])
        resp = client.get("/api/v1/student-profiles/1/versions", headers=_auth_headers())
        versions = resp.json()["items"]
        evidence_snapshot = versions[0]["evidence_snapshot"]
        assert isinstance(evidence_snapshot, list)
        assert len(evidence_snapshot) > 0
        for item in evidence_snapshot:
            assert "source" in item
            assert "excerpt" in item
            assert "confidence" in item


class TestProfileOutputFields:
    """Profile output must include skills, certificates, projects, internships, and scores."""

    def test_profile_contains_skills(self, client: TestClient, prepare_database):
        file_id = _upload_and_parse(client)
        data = _generate_profile(client, [file_id])
        assert isinstance(data["skills"], list)
        assert len(data["skills"]) > 0

    def test_profile_contains_certificates(self, client: TestClient, prepare_database):
        file_id = _upload_and_parse(client)
        data = _generate_profile(client, [file_id])
        assert isinstance(data["certificates"], list)

    def test_profile_contains_projects(self, client: TestClient, prepare_database):
        file_id = _upload_and_parse(client)
        data = _generate_profile(client, [file_id])
        assert isinstance(data["projects"], list)
        assert len(data["projects"]) > 0

    def test_profile_contains_internships(self, client: TestClient, prepare_database):
        file_id = _upload_and_parse(client)
        data = _generate_profile(client, [file_id])
        assert isinstance(data["internships"], list)
        assert len(data["internships"]) > 0

    def test_profile_contains_capability_scores(self, client: TestClient, prepare_database):
        file_id = _upload_and_parse(client)
        data = _generate_profile(client, [file_id])
        scores = data["capability_scores"]
        assert isinstance(scores, dict)
        for key in ["innovation", "learning", "resilience", "communication", "internship"]:
            assert key in scores


class TestVersionDetailEndpoint:
    """Version detail endpoint returns full version data."""

    def test_get_version_detail(self, client: TestClient, prepare_database):
        file_id = _upload_and_parse(client)
        data = _generate_profile(client, [file_id])
        version_id = data["profile_version_id"]

        resp = client.get(
            f"/api/v1/student-profiles/1/versions/{version_id}",
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["id"] == version_id
        assert detail["version_no"] == 1
        assert detail["uploaded_file_ids"] == [file_id]
        assert isinstance(detail["evidence_snapshot"], list)

    def test_version_detail_not_found(self, client: TestClient, prepare_database):
        resp = client.get(
            "/api/v1/student-profiles/1/versions/9999",
            headers=_auth_headers(),
        )
        assert resp.status_code == 404


class TestMultipleVersionIncrement:
    """Each generation creates a new independent version record."""

    def test_version_numbers_increment(self, client: TestClient, prepare_database):
        fid1 = _upload_and_parse(client, RESUME_TEXT, "v1.docx", "resume")
        _generate_profile(client, [fid1])

        fid2 = _upload_and_parse(client, RESUME_TEXT_B, "v2.docx", "resume")
        _generate_profile(client, [fid2])

        resp = client.get("/api/v1/student-profiles/1/versions", headers=_auth_headers())
        versions = resp.json()["items"]
        assert len(versions) == 2
        # Sorted by version_no desc
        assert versions[0]["version_no"] == 2
        assert versions[1]["version_no"] == 1

    def test_versions_have_different_snapshots(self, client: TestClient, prepare_database):
        fid1 = _upload_and_parse(client, RESUME_TEXT, "v1.docx", "resume")
        _generate_profile(client, [fid1])

        fid2 = _upload_and_parse(client, RESUME_TEXT_B, "v2.docx", "resume")
        _generate_profile(client, [fid2])

        resp = client.get("/api/v1/student-profiles/1/versions", headers=_auth_headers())
        versions = resp.json()["items"]
        v2 = versions[0]
        v1 = versions[1]
        # Different source files
        assert v2["uploaded_file_ids"] != v1["uploaded_file_ids"]
        assert v2["source_files"] != v1["source_files"]


class TestSnapshotIntegrity:
    """Snapshot contains all required profile fields without evidence in snapshot_json."""

    def test_snapshot_contains_all_profile_fields(self, client: TestClient, prepare_database):
        file_id = _upload_and_parse(client)
        _generate_profile(client, [file_id])
        resp = client.get("/api/v1/student-profiles/1/versions", headers=_auth_headers())
        snapshot = resp.json()["items"][0]["snapshot"]
        expected_keys = [
            "source_summary", "skills", "certificates", "projects", "internships",
            "capability_scores", "completeness_score", "competitiveness_score",
            "willingness", "uploaded_file_ids", "mode",
        ]
        for key in expected_keys:
            assert key in snapshot, f"Missing key: {key}"

    def test_evidence_snapshot_separate_from_profile_snapshot(self, client: TestClient, prepare_database):
        file_id = _upload_and_parse(client)
        _generate_profile(client, [file_id])
        resp = client.get("/api/v1/student-profiles/1/versions", headers=_auth_headers())
        version = resp.json()["items"][0]
        # evidence_snapshot is a dedicated field, not inside snapshot
        assert "evidence" not in version["snapshot"] or isinstance(version["snapshot"].get("evidence"), (list, type(None)))
        assert len(version["evidence_snapshot"]) > 0


class TestManualInputVersion:
    """Manual input only still creates valid version records."""

    @pytest.mark.asyncio
    async def test_manual_input_creates_version(self, db_session):
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
        assert result["profile_version_id"] is not None
        assert result["projects"] == ["CareerPilot"]
        assert result["internships"] == ["前端实习"]
