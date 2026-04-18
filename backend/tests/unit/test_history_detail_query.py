"""US-011: History detail query by record type.

Verify that each history record type resolves to a dedicated detail query
with correct ownership scoping:
- Report detail returns the specific report data tied to the record ID
- Chat history detail returns messages around the target message ID
- Profile, matching, path, upload, and feedback details return correct data
- A student cannot access another student's history record
- Refreshing the same endpoint returns consistent data
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import create_access_token
from app.models import (
    CareerReport,
    ChatMessageRecord,
    FollowupRecord,
    JobProfile,
    MatchResult,
    PathRecommendation,
    ProfileVersion,
    Student,
    StudentProfile,
    UploadedFile,
    User,
)
from app.services.auth_service import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_student(db: Session, username: str, full_name: str) -> tuple[User, Student, dict]:
    """Create a student user and return (user, student, auth_headers)."""
    user = User(
        username=username,
        password_hash=hash_password("test123"),
        role="student",
        full_name=full_name,
        email=f"{username}@test.local",
    )
    db.add(user)
    db.flush()
    student = Student(user_id=user.id, major="软件工程", grade="大三")
    db.add(student)
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    return user, student, headers


def _seed_report(db: Session, student_id: int, job_code: str = "RD001") -> int:
    r = CareerReport(
        student_id=student_id,
        target_job_code=job_code,
        status="completed",
        content_json={"sections": ["test"]},
        markdown_content="# Report Content",
    )
    db.add(r)
    db.flush()
    db.commit()
    return r.id


def _seed_chat_pair(db: Session, user_id: int, user_msg: str = "你好", ai_msg: str = "你好！"):
    """Create a user+assistant chat message pair. Return (user_msg_id, assistant_msg_id)."""
    um = ChatMessageRecord(user_id=user_id, role="user", content=user_msg)
    db.add(um)
    db.flush()
    am = ChatMessageRecord(user_id=user_id, role="assistant", content=ai_msg)
    db.add(am)
    db.flush()
    db.commit()
    return um.id, am.id


def _seed_profile_version(db: Session, student_id: int) -> int:
    pv = ProfileVersion(
        student_id=student_id,
        version_no=1,
        snapshot_json={"skills": ["Python", "SQL"]},
    )
    db.add(pv)
    db.flush()
    db.commit()
    return pv.id


def _seed_student_profile(db: Session, student_id: int) -> int:
    sp = StudentProfile(student_id=student_id)
    db.add(sp)
    db.flush()
    db.commit()
    return sp.id


def _seed_job_profile(db: Session, code: str) -> int:
    jp = JobProfile(job_code=code, title=f"测试岗位-{code}")
    db.add(jp)
    db.flush()
    db.commit()
    return jp.id


def _seed_match(db: Session, student_profile_id: int, job_profile_id: int, score: float = 85.0) -> int:
    m = MatchResult(
        student_profile_id=student_profile_id,
        job_profile_id=job_profile_id,
        total_score=score,
        summary="匹配摘要",
    )
    db.add(m)
    db.flush()
    db.commit()
    return m.id


def _seed_path(db: Session, student_id: int, job_code: str = "PD001") -> int:
    p = PathRecommendation(
        student_id=student_id,
        target_job_code=job_code,
    )
    db.add(p)
    db.flush()
    db.commit()
    return p.id


def _seed_upload(db: Session, user_id: int) -> int:
    f = UploadedFile(
        owner_id=user_id,
        file_type="resume",
        file_name="resume.pdf",
        storage_key="/tmp/resume.pdf",
    )
    db.add(f)
    db.flush()
    db.commit()
    return f.id


def _seed_feedback(db: Session, student_id: int) -> int:
    fb = FollowupRecord(
        student_id=student_id,
        record_type="advice",
        content="继续加强算法练习",
    )
    db.add(fb)
    db.flush()
    db.commit()
    return fb.id


# ---------------------------------------------------------------------------
# Tests: History detail endpoint (GET /students/me/history/detail)
# ---------------------------------------------------------------------------


class TestReportDetail:
    """Report detail queries return the specific report tied to the record ID."""

    def test_report_detail_returns_correct_report(self, client: TestClient, db_session: Session):
        """A student can fetch a specific report by ref_id via the history detail endpoint."""
        user_a, stu_a, headers_a = _make_student(db_session, "stu_report_a", "Report Student A")
        report_id = _seed_report(db_session, stu_a.id, "RPT01")

        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "report", "ref_id": report_id},
            headers=headers_a,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "report"
        assert data["ref_id"] == report_id
        assert data["status"] == "completed"
        assert data["markdown_content"] == "# Report Content"

    def test_report_detail_cross_student_forbidden(self, client: TestClient, db_session: Session):
        """Student A cannot fetch Student B's report via history detail."""
        _, stu_a, headers_a = _make_student(db_session, "stu_report_a2", "Report Student A2")
        _, stu_b, _ = _make_student(db_session, "stu_report_b", "Report Student B")
        report_id_b = _seed_report(db_session, stu_b.id, "RPT02")

        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "report", "ref_id": report_id_b},
            headers=headers_a,
        )
        assert resp.status_code == 404  # Should not leak existence

    def test_report_detail_consistency_on_refresh(self, client: TestClient, db_session: Session):
        """Calling the same endpoint twice returns the same data (refresh stability)."""
        _, stu, headers = _make_student(db_session, "stu_report_refresh", "Report Refresh")
        report_id = _seed_report(db_session, stu.id, "RPT03")

        r1 = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "report", "ref_id": report_id},
            headers=headers,
        )
        r2 = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "report", "ref_id": report_id},
            headers=headers,
        )
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json() == r2.json()


class TestChatHistoryDetail:
    """Chat history endpoint returns messages around the target message with ownership."""

    def test_chat_history_returns_surrounding_messages(self, client: TestClient, db_session: Session):
        """Fetching a chat message returns the user+assistant pair."""
        user_a, _, headers_a = _make_student(db_session, "stu_chat_a", "Chat Student A")
        user_msg_id, assistant_msg_id = _seed_chat_pair(db_session, user_a.id)

        resp = client.get(f"/api/v1/chat/history/{user_msg_id}", headers=headers_a)
        assert resp.status_code == 200
        data = resp.json()
        assert data["target_message_id"] == user_msg_id
        assert len(data["messages"]) == 2
        roles = [m["role"] for m in data["messages"]]
        assert "user" in roles
        assert "assistant" in roles

    def test_chat_history_cross_student_forbidden(self, client: TestClient, db_session: Session):
        """Student A cannot fetch Student B's chat history."""
        user_a, _, headers_a = _make_student(db_session, "stu_chat_a2", "Chat A2")
        user_b, _, _ = _make_student(db_session, "stu_chat_b", "Chat B")
        user_msg_id_b, _ = _seed_chat_pair(db_session, user_b.id, "B的消息", "B的回复")

        resp = client.get(f"/api/v1/chat/history/{user_msg_id_b}", headers=headers_a)
        # Should be 403 (resource forbidden)
        assert resp.status_code == 403

    def test_chat_history_nonexistent_message(self, client: TestClient, db_session: Session):
        """Requesting a non-existent chat message returns 404."""
        _, _, headers = _make_student(db_session, "stu_chat_404", "Chat 404")
        resp = client.get("/api/v1/chat/history/999999", headers=headers)
        assert resp.status_code == 404

    def test_chat_history_unauthenticated(self, client: TestClient, db_session: Session):
        """Unauthenticated requests to chat history are rejected."""
        user_a, _, _ = _make_student(db_session, "stu_chat_noauth", "Chat NoAuth")
        msg_id, _ = _seed_chat_pair(db_session, user_a.id)

        resp = client.get(f"/api/v1/chat/history/{msg_id}")
        assert resp.status_code == 401

    def test_chat_history_consistency_on_refresh(self, client: TestClient, db_session: Session):
        """Calling the same chat history endpoint twice returns the same data."""
        user_a, _, headers_a = _make_student(db_session, "stu_chat_refresh", "Chat Refresh")
        msg_id, _ = _seed_chat_pair(db_session, user_a.id, "刷新测试", "刷新回复")

        r1 = client.get(f"/api/v1/chat/history/{msg_id}", headers=headers_a)
        r2 = client.get(f"/api/v1/chat/history/{msg_id}", headers=headers_a)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json() == r2.json()


class TestProfileDetail:
    """Profile version detail queries return the specific version with ownership."""

    def test_profile_detail_returns_correct_version(self, client: TestClient, db_session: Session):
        _, stu, headers = _make_student(db_session, "stu_prof_det", "Profile Detail")
        pv_id = _seed_profile_version(db_session, stu.id)

        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "profile", "ref_id": pv_id},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "profile"
        assert data["ref_id"] == pv_id
        assert data["version_no"] == 1
        assert data["snapshot"]["skills"] == ["Python", "SQL"]

    def test_profile_detail_cross_student_forbidden(self, client: TestClient, db_session: Session):
        _, stu_a, headers_a = _make_student(db_session, "stu_prof_a", "Profile A")
        _, stu_b, _ = _make_student(db_session, "stu_prof_b", "Profile B")
        pv_id_b = _seed_profile_version(db_session, stu_b.id)

        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "profile", "ref_id": pv_id_b},
            headers=headers_a,
        )
        assert resp.status_code == 404


class TestMatchingDetail:
    """Matching detail queries return specific match result with ownership."""

    def test_matching_detail_returns_correct_data(self, client: TestClient, db_session: Session):
        _, stu, headers = _make_student(db_session, "stu_match_det", "Match Detail")
        sp_id = _seed_student_profile(db_session, stu.id)
        jp_id = _seed_job_profile(db_session, "MDT01")
        match_id = _seed_match(db_session, sp_id, jp_id, 92.5)

        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "matching", "ref_id": match_id},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "matching"
        assert data["ref_id"] == match_id
        assert data["total_score"] == 92.5

    def test_matching_detail_cross_student_forbidden(self, client: TestClient, db_session: Session):
        _, stu_a, headers_a = _make_student(db_session, "stu_match_a", "Match A")
        _, stu_b, _ = _make_student(db_session, "stu_match_b", "Match B")
        sp_id_b = _seed_student_profile(db_session, stu_b.id)
        jp_id = _seed_job_profile(db_session, "MDT02")
        match_id_b = _seed_match(db_session, sp_id_b, jp_id)

        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "matching", "ref_id": match_id_b},
            headers=headers_a,
        )
        assert resp.status_code == 404


class TestPathDetail:
    """Path detail queries return specific path recommendation with ownership."""

    def test_path_detail_returns_correct_data(self, client: TestClient, db_session: Session):
        _, stu, headers = _make_student(db_session, "stu_path_det", "Path Detail")
        path_id = _seed_path(db_session, stu.id, "PTH01")

        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "path", "ref_id": path_id},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "path"
        assert data["ref_id"] == path_id
        assert data["target_job_code"] == "PTH01"

    def test_path_detail_cross_student_forbidden(self, client: TestClient, db_session: Session):
        _, stu_a, headers_a = _make_student(db_session, "stu_path_a", "Path A")
        _, stu_b, _ = _make_student(db_session, "stu_path_b", "Path B")
        path_id_b = _seed_path(db_session, stu_b.id, "PTH02")

        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "path", "ref_id": path_id_b},
            headers=headers_a,
        )
        assert resp.status_code == 404


class TestUploadDetail:
    """Upload detail queries return specific file info with ownership."""

    def test_upload_detail_returns_correct_data(self, client: TestClient, db_session: Session):
        user, _, headers = _make_student(db_session, "stu_upl_det", "Upload Detail")
        file_id = _seed_upload(db_session, user.id)

        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "upload", "ref_id": file_id},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "upload"
        assert data["ref_id"] == file_id
        assert data["file_name"] == "resume.pdf"

    def test_upload_detail_cross_student_forbidden(self, client: TestClient, db_session: Session):
        user_a, _, headers_a = _make_student(db_session, "stu_upl_a", "Upload A")
        user_b, _, _ = _make_student(db_session, "stu_upl_b", "Upload B")
        file_id_b = _seed_upload(db_session, user_b.id)

        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "upload", "ref_id": file_id_b},
            headers=headers_a,
        )
        assert resp.status_code == 404


class TestFeedbackDetail:
    """Feedback detail queries return specific feedback with ownership."""

    def test_feedback_detail_returns_correct_data(self, client: TestClient, db_session: Session):
        _, stu, headers = _make_student(db_session, "stu_fb_det", "Feedback Detail")
        fb_id = _seed_feedback(db_session, stu.id)

        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "feedback", "ref_id": fb_id},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "feedback"
        assert data["ref_id"] == fb_id
        assert data["content"] == "继续加强算法练习"

    def test_feedback_detail_cross_student_forbidden(self, client: TestClient, db_session: Session):
        _, stu_a, headers_a = _make_student(db_session, "stu_fb_a", "Feedback A")
        _, stu_b, _ = _make_student(db_session, "stu_fb_b", "Feedback B")
        fb_id_b = _seed_feedback(db_session, stu_b.id)

        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "feedback", "ref_id": fb_id_b},
            headers=headers_a,
        )
        assert resp.status_code == 404


class TestHistoryDetailEdgeCases:
    """Edge cases for the history detail endpoint."""

    def test_unsupported_type_returns_400(self, client: TestClient, db_session: Session):
        _, _, headers = _make_student(db_session, "stu_edge_type", "Edge Type")
        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "unknown_type", "ref_id": 1},
            headers=headers,
        )
        assert resp.status_code == 400

    def test_unauthenticated_rejected(self, client: TestClient, db_session: Session):
        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "report", "ref_id": 1},
        )
        assert resp.status_code == 401

    def test_nonexistent_record_returns_404(self, client: TestClient, db_session: Session):
        _, _, headers = _make_student(db_session, "stu_edge_404", "Edge 404")
        resp = client.get(
            "/api/v1/students/me/history/detail",
            params={"type": "report", "ref_id": 999999},
            headers=headers,
        )
        assert resp.status_code == 404
