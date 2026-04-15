"""Tests for US-003: Per-resume independent parsing result persistence."""

import io

import pytest
from docx import Document
from fastapi.testclient import TestClient


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


def _upload_resume(
    client: TestClient,
    resume_text: str,
    filename: str = "resume.docx",
    owner_id: int = 1,
) -> int:
    """Upload a resume file (as valid DOCX) and return the file ID."""
    content = _build_docx(resume_text)
    resp = client.post(
        "/api/v1/files/upload",
        files=[("upload", (filename, content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))],
        data={"owner_id": str(owner_id), "file_type": "resume"},
        headers=_auth_headers(owner_id),
    )
    assert resp.status_code == 200, f"Upload failed: {resp.json()}"
    return resp.json()["data"]["id"]


def _parse_file(client: TestClient, file_id: int, document_type: str = "resume") -> dict:
    """Trigger OCR parsing for an uploaded file and return the response."""
    resp = client.post(
        "/api/v1/ocr/parse",
        json={"uploaded_file_id": file_id, "document_type": document_type},
        headers=_auth_headers(),
    )
    assert resp.status_code == 200, f"Parse failed: {resp.json()}"
    return resp.json()


RESUME_A_TEXT = (
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
    "竞赛：\n"
    "- ACM 程序设计竞赛金奖\n"
    "- 数学建模竞赛一等奖\n"
    "自我评价：具有良好的编程能力和团队协作精神\n"
    "GPA：3.8"
)

RESUME_B_TEXT = (
    "姓名：李四\n"
    "学校：清华大学\n"
    "专业：数据科学与大数据技术\n"
    "年级：研一\n"
    "毕业年份：2027\n"
    "意向岗位：数据分析师\n"
    "技能：Python SQL 数据分析 数据可视化\n"
    "证书：数据分析师证书\n"
    "项目：电商用户行为分析系统\n"
    "实习：阿里巴巴数据分析实习生\n"
    "自我评价：对数据驱动决策有浓厚兴趣\n"
    "GPA：3.6"
)


class TestStructuredParseFields:
    """Test that parse results contain all required fields."""

    def test_parse_result_contains_required_fields(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)

        sj = result["structured_json"]
        required_fields = [
            "name", "school", "major", "grade", "graduation_year",
            "target_job", "skills", "projects", "internships",
            "certificates", "competitions", "self_evaluation",
        ]
        for field in required_fields:
            assert field in sj, f"Missing required field: {field}"

    def test_parse_result_extracts_name(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)
        assert result["structured_json"]["name"] == "张三"

    def test_parse_result_extracts_school(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)
        assert "北京大学" in result["structured_json"]["school"]

    def test_parse_result_extracts_major(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)
        assert "计算机" in result["structured_json"]["major"]

    def test_parse_result_extracts_grade(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)
        assert "大三" in result["structured_json"]["grade"]

    def test_parse_result_extracts_graduation_year(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)
        assert result["structured_json"]["graduation_year"] == "2026"

    def test_parse_result_extracts_target_job(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)
        assert "前端开发" in result["structured_json"]["target_job"]

    def test_parse_result_extracts_skills(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)
        skills = result["structured_json"]["skills"]
        assert "Python" in skills
        assert "JavaScript" in skills
        assert "React" in skills

    def test_parse_result_extracts_projects(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)
        projects = result["structured_json"]["projects"]
        assert any("智能问答" in p for p in projects)

    def test_parse_result_extracts_internships(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)
        internships = result["structured_json"]["internships"]
        assert any("字节跳动" in i for i in internships)

    def test_parse_result_extracts_certificates(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)
        certs = result["structured_json"]["certificates"]
        assert "英语四级" in certs

    def test_parse_result_extracts_competitions(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)
        competitions = result["structured_json"]["competitions"]
        assert any("ACM" in c for c in competitions)

    def test_parse_result_extracts_self_evaluation(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        result = _parse_file(client, file_id)
        self_eval = result["structured_json"]["self_evaluation"]
        assert "编程能力" in self_eval or "团队协作" in self_eval


class TestParseResultBoundToFileId:
    """Test that parse results are bound to specific file ID."""

    def test_get_parse_result_by_file_id(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        _parse_file(client, file_id)

        resp = client.get(
            f"/api/v1/ocr/result/{file_id}",
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["file_id"] == file_id
        assert data["parsed_json"]["name"] == "张三"
        assert data["resume_id"] is not None

    def test_get_parse_result_not_found_for_unparsed(self, client: TestClient, prepare_database):
        file_id = _upload_resume(client, RESUME_A_TEXT)
        # Don't parse - should return 404
        resp = client.get(
            f"/api/v1/ocr/result/{file_id}",
            headers=_auth_headers(),
        )
        assert resp.status_code == 404


class TestMultiResumeIndependence:
    """Test that multiple resumes for the same account have independent results."""

    def test_two_resumes_have_independent_parse_results(self, client: TestClient, prepare_database):
        file_a = _upload_resume(client, RESUME_A_TEXT, filename="resume_a.docx")
        file_b = _upload_resume(client, RESUME_B_TEXT, filename="resume_b.docx")

        result_a = _parse_file(client, file_a)
        result_b = _parse_file(client, file_b)

        # Name should be different
        assert result_a["structured_json"]["name"] == "张三"
        assert result_b["structured_json"]["name"] == "李四"

        # School should be different
        assert "北京大学" in result_a["structured_json"]["school"]
        assert "清华大学" in result_b["structured_json"]["school"]

        # Major should be different
        assert "计算机" in result_a["structured_json"]["major"]
        assert "数据科学" in result_b["structured_json"]["major"]

    def test_query_each_file_independently(self, client: TestClient, prepare_database):
        file_a = _upload_resume(client, RESUME_A_TEXT, filename="resume_a.docx")
        file_b = _upload_resume(client, RESUME_B_TEXT, filename="resume_b.docx")

        _parse_file(client, file_a)
        _parse_file(client, file_b)

        # Query each independently
        resp_a = client.get(f"/api/v1/ocr/result/{file_a}", headers=_auth_headers())
        resp_b = client.get(f"/api/v1/ocr/result/{file_b}", headers=_auth_headers())

        assert resp_a.status_code == 200
        assert resp_b.status_code == 200

        data_a = resp_a.json()["data"]
        data_b = resp_b.json()["data"]

        # Each file's result is independent
        assert data_a["file_id"] == file_a
        assert data_b["file_id"] == file_b
        assert data_a["parsed_json"]["name"] == "张三"
        assert data_b["parsed_json"]["name"] == "李四"

    def test_list_all_parse_results(self, client: TestClient, prepare_database):
        file_a = _upload_resume(client, RESUME_A_TEXT, filename="resume_a.docx")
        file_b = _upload_resume(client, RESUME_B_TEXT, filename="resume_b.docx")

        _parse_file(client, file_a)
        _parse_file(client, file_b)

        resp = client.get("/api/v1/ocr/results", headers=_auth_headers())
        assert resp.status_code == 200
        results = resp.json()["data"]
        assert len(results) == 2

        # Both results should be present
        file_ids = {r["file_id"] for r in results}
        assert file_a in file_ids
        assert file_b in file_ids

        # Each has parsed_json
        for r in results:
            assert r["parsed_json"] is not None
            assert "name" in r["parsed_json"]

    def test_parsing_resume_b_does_not_overwrite_a(self, client: TestClient, prepare_database):
        file_a = _upload_resume(client, RESUME_A_TEXT, filename="resume_a.docx")
        file_b = _upload_resume(client, RESUME_B_TEXT, filename="resume_b.docx")

        # Parse A first
        _parse_file(client, file_a)

        # Then parse B
        _parse_file(client, file_b)

        # A's result should still be intact
        resp_a = client.get(f"/api/v1/ocr/result/{file_a}", headers=_auth_headers())
        assert resp_a.status_code == 200
        assert resp_a.json()["data"]["parsed_json"]["name"] == "张三"
        assert "北京大学" in resp_a.json()["data"]["parsed_json"]["school"]

    def test_same_filename_different_file_ids(self, client: TestClient, prepare_database):
        """Two files with same content should get different file IDs and independent results."""
        file_1 = _upload_resume(client, RESUME_A_TEXT, filename="resume.docx")
        file_2 = _upload_resume(client, RESUME_A_TEXT, filename="resume.docx")

        assert file_1 != file_2

        _parse_file(client, file_1)
        _parse_file(client, file_2)

        resp_1 = client.get(f"/api/v1/ocr/result/{file_1}", headers=_auth_headers())
        resp_2 = client.get(f"/api/v1/ocr/result/{file_2}", headers=_auth_headers())

        assert resp_1.status_code == 200
        assert resp_2.status_code == 200
        # Same content but different file IDs and resume IDs
        assert resp_1.json()["data"]["file_id"] != resp_2.json()["data"]["file_id"]
        assert resp_1.json()["data"]["resume_id"] != resp_2.json()["data"]["resume_id"]
