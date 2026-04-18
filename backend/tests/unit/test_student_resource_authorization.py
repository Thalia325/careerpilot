"""US-002: Student resource authorization tests.

Verify that authenticated students can only access their own resources
and receive 403 Forbidden when attempting to access another student's data.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import create_access_token
from app.models import (
    AnalysisRun,
    CareerReport,
    ChatMessageRecord,
    FollowupRecord,
    MatchResult,
    PathRecommendation,
    ProfileVersion,
    Student,
    TeacherComment,
    UploadedFile,
    User,
)
from app.schemas.report import ReportContent
from app.services.auth_service import hash_password

# Minimal valid report content matching ReportContent schema
_MINIMAL_REPORT_CONTENT: dict = {
    "student_summary": {},
    "resume_summary": {},
    "capability_profile": {},
    "target_job_analysis": {},
    "matching_analysis": {},
    "gap_analysis": {},
    "career_path": {},
    "short_term_plan": {},
    "mid_term_plan": {},
    "evaluation_cycle": {},
    "teacher_comments": {},
}


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


def _make_admin(db: Session, username: str = "admin_auth_test") -> tuple[User, dict]:
    """Create an admin user and return (user, auth_headers)."""
    user = User(
        username=username,
        password_hash=hash_password("test123"),
        role="admin",
        full_name="Auth Test Admin",
        email=f"{username}@test.local",
    )
    db.add(user)
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAnalysisAuthorization:
    """Verify analysis run endpoints enforce student ownership."""

    def test_student_cannot_start_analysis_for_other_student(self, client: TestClient, db_session: Session):
        """POST /api/v1/analysis/start should reject student_id not owned by caller."""
        _, student_a, headers_a = _make_student(db_session, "stu_auth_a", "Student A")
        _, student_b, _ = _make_student(db_session, "stu_auth_b", "Student B")

        resp = client.post(
            "/api/v1/analysis/start",
            json={"student_id": student_b.id, "job_code": "", "file_ids": []},
            headers=headers_a,
        )
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        # errors.py returns structured detail dict
        assert "无权" in (detail["message"] if isinstance(detail, dict) else detail)

    def test_student_can_start_own_analysis(self, client: TestClient, db_session: Session):
        """POST /api/v1/analysis/start should succeed for own student_id."""
        _, student_a, headers_a = _make_student(db_session, "stu_auth_c", "Student C")

        resp = client.post(
            "/api/v1/analysis/start",
            json={"student_id": student_a.id, "job_code": "", "file_ids": []},
            headers=headers_a,
        )
        assert resp.status_code == 200

    def test_student_cannot_read_other_analysis(self, client: TestClient, db_session: Session):
        """GET /api/v1/analysis/{run_id} should reject if run belongs to another student."""
        _, student_a, headers_a = _make_student(db_session, "stu_auth_d", "Student D")
        _, student_b, _ = _make_student(db_session, "stu_auth_e", "Student E")

        run = AnalysisRun(student_id=student_b.id, status="pending", current_step="")
        db_session.add(run)
        db_session.commit()

        resp = client.get(f"/api/v1/analysis/{run.id}", headers=headers_a)
        assert resp.status_code == 403

    def test_student_can_read_own_analysis(self, client: TestClient, db_session: Session):
        """GET /api/v1/analysis/{run_id} should succeed for own run."""
        _, student_a, headers_a = _make_student(db_session, "stu_auth_f", "Student F")

        run = AnalysisRun(student_id=student_a.id, status="pending", current_step="")
        db_session.add(run)
        db_session.commit()

        resp = client.get(f"/api/v1/analysis/{run.id}", headers=headers_a)
        assert resp.status_code == 200

    def test_student_cannot_update_other_analysis_context(self, client: TestClient, db_session: Session):
        """PATCH /api/v1/analysis/{run_id}/context should reject foreign run."""
        _, student_a, headers_a = _make_student(db_session, "stu_auth_g", "Student G")
        _, student_b, _ = _make_student(db_session, "stu_auth_h", "Student H")

        run = AnalysisRun(student_id=student_b.id, status="pending", current_step="")
        db_session.add(run)
        db_session.commit()

        resp = client.patch(
            f"/api/v1/analysis/{run.id}/context",
            json={"target_job_code": "test"},
            headers=headers_a,
        )
        assert resp.status_code == 403

    def test_student_cannot_reset_other_analysis(self, client: TestClient, db_session: Session):
        """POST /api/v1/analysis/{run_id}/reset should reject foreign run."""
        _, student_a, headers_a = _make_student(db_session, "stu_auth_i", "Student I")
        _, student_b, _ = _make_student(db_session, "stu_auth_j", "Student J")

        run = AnalysisRun(student_id=student_b.id, status="completed", current_step="reported")
        db_session.add(run)
        db_session.commit()

        resp = client.post(f"/api/v1/analysis/{run.id}/reset", headers=headers_a)
        assert resp.status_code == 403

    def test_admin_can_access_any_analysis(self, client: TestClient, db_session: Session):
        """Admin should bypass student ownership check."""
        _, student_a, _ = _make_student(db_session, "stu_auth_k", "Student K")
        _, admin_headers = _make_admin(db_session)

        run = AnalysisRun(student_id=student_a.id, status="pending", current_step="")
        db_session.add(run)
        db_session.commit()

        resp = client.get(f"/api/v1/analysis/{run.id}", headers=admin_headers)
        assert resp.status_code == 200


class TestProfileAuthorization:
    """Verify student profile endpoints enforce student ownership."""

    def test_student_cannot_read_other_profile(self, client: TestClient, db_session: Session):
        """GET /api/v1/student-profiles/{student_id} should reject foreign student."""
        _, student_a, headers_a = _make_student(db_session, "stu_prof_a", "Profile A")
        _, student_b, _ = _make_student(db_session, "stu_prof_b", "Profile B")

        resp = client.get(f"/api/v1/student-profiles/{student_b.id}", headers=headers_a)
        assert resp.status_code == 403

    def test_student_can_read_own_profile(self, client: TestClient, db_session: Session):
        """GET /api/v1/student-profiles/{student_id} returns own profile (404 if no profile yet)."""
        _, student_a, headers_a = _make_student(db_session, "stu_prof_c", "Profile C")

        resp = client.get(f"/api/v1/student-profiles/{student_a.id}", headers=headers_a)
        # 404 is acceptable (no profile generated yet), but NOT 403
        assert resp.status_code in (200, 404)

    def test_student_cannot_read_other_profile_versions(self, client: TestClient, db_session: Session):
        """GET /api/v1/student-profiles/{student_id}/versions should reject foreign student."""
        _, student_a, headers_a = _make_student(db_session, "stu_prof_d", "Profile D")
        _, student_b, _ = _make_student(db_session, "stu_prof_e", "Profile E")

        resp = client.get(f"/api/v1/student-profiles/{student_b.id}/versions", headers=headers_a)
        assert resp.status_code == 403


class TestReportAuthorization:
    """Verify report endpoints enforce student ownership."""

    def test_student_cannot_read_other_report(self, client: TestClient, db_session: Session):
        """GET /api/v1/reports/{report_id} should reject foreign report."""
        _, student_a, headers_a = _make_student(db_session, "stu_rpt_a", "Report A")
        _, student_b, _ = _make_student(db_session, "stu_rpt_b", "Report B")

        report = CareerReport(
            student_id=student_b.id,
            target_job_code="test",
            content_json=dict(_MINIMAL_REPORT_CONTENT),
            markdown_content="# Test",
            status="completed",
        )
        db_session.add(report)
        db_session.commit()

        resp = client.get(f"/api/v1/reports/{report.id}", headers=headers_a)
        assert resp.status_code == 403

    def test_student_can_read_own_report(self, client: TestClient, db_session: Session):
        """GET /api/v1/reports/{report_id} should succeed for own report."""
        _, student_a, headers_a = _make_student(db_session, "stu_rpt_c", "Report C")

        report = CareerReport(
            student_id=student_a.id,
            target_job_code="test",
            content_json=dict(_MINIMAL_REPORT_CONTENT),
            markdown_content="# Test",
            status="completed",
        )
        db_session.add(report)
        db_session.commit()

        resp = client.get(f"/api/v1/reports/{report.id}", headers=headers_a)
        assert resp.status_code == 200

    def test_student_cannot_save_other_report(self, client: TestClient, db_session: Session):
        """POST /api/v1/reports/save should reject foreign report."""
        _, student_a, headers_a = _make_student(db_session, "stu_rpt_d", "Report D")
        _, student_b, _ = _make_student(db_session, "stu_rpt_e", "Report E")

        report = CareerReport(
            student_id=student_b.id,
            target_job_code="test",
            content_json={},
            markdown_content="",
            status="draft",
        )
        db_session.add(report)
        db_session.commit()

        resp = client.post(
            "/api/v1/reports/save",
            json={"report_id": report.id, "markdown_content": "modified"},
            headers=headers_a,
        )
        assert resp.status_code == 403

    def test_student_cannot_export_other_report(self, client: TestClient, db_session: Session):
        """POST /api/v1/reports/export should reject foreign report."""
        _, student_a, headers_a = _make_student(db_session, "stu_rpt_f", "Report F")
        _, student_b, _ = _make_student(db_session, "stu_rpt_g", "Report G")

        report = CareerReport(
            student_id=student_b.id,
            target_job_code="test",
            content_json={},
            markdown_content="",
            status="draft",
        )
        db_session.add(report)
        db_session.commit()

        resp = client.post(
            "/api/v1/reports/export",
            json={"report_id": report.id, "format": "pdf"},
            headers=headers_a,
        )
        assert resp.status_code == 403


class TestMatchingAuthorization:
    """Verify matching endpoints enforce student ownership."""

    def test_student_cannot_analyze_other_student(self, client: TestClient, db_session: Session):
        """POST /api/v1/matching/analyze should reject foreign student_id."""
        _, student_a, headers_a = _make_student(db_session, "stu_match_a", "Match A")
        _, student_b, _ = _make_student(db_session, "stu_match_b", "Match B")

        resp = client.post(
            "/api/v1/matching/analyze",
            json={"student_id": student_b.id, "job_code": "test", "profile_version_id": None},
            headers=headers_a,
        )
        assert resp.status_code == 403

    def test_student_cannot_read_other_match_result(self, client: TestClient, db_session: Session):
        """GET /api/v1/matching/{match_id} should reject if match belongs to another student."""
        _, student_a, headers_a = _make_student(db_session, "stu_match_c", "Match C")
        _, student_b, _ = _make_student(db_session, "stu_match_d", "Match D")

        match = MatchResult(
            student_profile_id=0,
            job_profile_id=0,
            total_score=80.0,
            student_id=student_b.id,
        )
        db_session.add(match)
        db_session.commit()

        resp = client.get(f"/api/v1/matching/{match.id}", headers=headers_a)
        assert resp.status_code == 403


class TestCareerPathAuthorization:
    """Verify career path endpoints enforce student ownership."""

    def test_student_cannot_plan_path_for_other(self, client: TestClient, db_session: Session):
        """POST /api/v1/career-paths/plan should reject foreign student_id."""
        _, student_a, headers_a = _make_student(db_session, "stu_path_a", "Path A")
        _, student_b, _ = _make_student(db_session, "stu_path_b", "Path B")

        resp = client.post(
            "/api/v1/career-paths/plan",
            json={"student_id": student_b.id, "job_code": "test"},
            headers=headers_a,
        )
        assert resp.status_code == 403

    def test_student_cannot_read_other_path(self, client: TestClient, db_session: Session):
        """GET /api/v1/career-paths/{path_id} should reject foreign path."""
        _, student_a, headers_a = _make_student(db_session, "stu_path_c", "Path C")
        _, student_b, _ = _make_student(db_session, "stu_path_d", "Path D")

        path = PathRecommendation(
            student_id=student_b.id,
            target_job_code="test",
            primary_path_json=["Step 1"],
        )
        db_session.add(path)
        db_session.commit()

        resp = client.get(f"/api/v1/career-paths/{path.id}", headers=headers_a)
        assert resp.status_code == 403


class TestOCRAuthorization:
    """Verify OCR parse endpoint enforces file ownership for students."""

    def test_student_cannot_parse_other_file(self, client: TestClient, db_session: Session):
        """POST /api/v1/ocr/parse should reject file_id owned by another user."""
        user_a, student_a, headers_a = _make_student(db_session, "stu_ocr_a", "OCR A")
        user_b, _, _ = _make_student(db_session, "stu_ocr_b", "OCR B")

        # Upload a file owned by user_b
        uploaded = UploadedFile(
            owner_id=user_b.id,
            file_type="resume",
            file_name="resume.pdf",
            content_type="application/pdf",
            storage_key="test/resume.pdf",
        )
        db_session.add(uploaded)
        db_session.commit()

        resp = client.post(
            "/api/v1/ocr/parse",
            json={"uploaded_file_id": uploaded.id, "document_type": "resume"},
            headers=headers_a,
        )
        assert resp.status_code == 403


class TestChatAuthorization:
    """Verify chat endpoints scope messages to the authenticated user."""

    def test_student_sees_only_own_chat_messages(self, client: TestClient, db_session: Session):
        """GET /api/v1/chat/greeting should only reflect the authenticated student's context."""
        user_a, _, headers_a = _make_student(db_session, "stu_chat_a", "Chat A")
        user_b, _, _ = _make_student(db_session, "stu_chat_b", "Chat B")

        # Insert a chat message for user_b
        db_session.add(ChatMessageRecord(
            user_id=user_b.id,
            role="user",
            content="Secret message from B",
            has_context=False,
        ))
        db_session.commit()

        # user_a's greeting should not contain user_b's context
        resp = client.get("/api/v1/chat/greeting", headers=headers_a)
        assert resp.status_code == 200
        assert "Secret message from B" not in resp.json().get("greeting", "")

    def test_student_can_read_own_ocr_result(self, client: TestClient, db_session: Session):
        """GET /api/v1/ocr/result/{file_id} should allow access to own files."""
        user_a, student_a, headers_a = _make_student(db_session, "stu_chat_c", "Chat C")

        from app.models import Resume
        uploaded = UploadedFile(
            owner_id=user_a.id,
            file_type="resume",
            file_name="my_resume.pdf",
            content_type="application/pdf",
            storage_key="test/my_resume.pdf",
        )
        db_session.add(uploaded)
        db_session.flush()

        resume = Resume(
            student_id=student_a.id,
            file_id=uploaded.id,
            parsed_json={"name": "Test"},
        )
        db_session.add(resume)
        db_session.commit()

        resp = client.get(f"/api/v1/ocr/result/{uploaded.id}", headers=headers_a)
        assert resp.status_code == 200

    def test_student_cannot_read_other_ocr_result(self, client: TestClient, db_session: Session):
        """GET /api/v1/ocr/result/{file_id} should reject access to another user's files."""
        _, _, headers_a = _make_student(db_session, "stu_chat_d", "Chat D")
        user_b, student_b, _ = _make_student(db_session, "stu_chat_e", "Chat E")

        uploaded = UploadedFile(
            owner_id=user_b.id,
            file_type="resume",
            file_name="other_resume.pdf",
            content_type="application/pdf",
            storage_key="test/other_resume.pdf",
        )
        db_session.add(uploaded)
        db_session.flush()

        from app.models import Resume
        resume = Resume(
            student_id=student_b.id,
            file_id=uploaded.id,
            parsed_json={"name": "Secret"},
        )
        db_session.add(resume)
        db_session.commit()

        resp = client.get(f"/api/v1/ocr/result/{uploaded.id}", headers=headers_a)
        assert resp.status_code == 403


class TestTeacherFeedbackAuthorization:
    """Verify teacher feedback endpoints enforce student ownership."""

    def _make_teacher(self, db: Session, username: str) -> User:
        """Create a teacher user and return it."""
        from app.models import Teacher
        user = User(
            username=username,
            password_hash=hash_password("test123"),
            role="teacher",
            full_name=username,
            email=f"{username}@test.local",
        )
        db.add(user)
        db.flush()
        teacher = Teacher(user_id=user.id)
        db.add(teacher)
        db.commit()
        return user

    def _make_report(self, db: Session, student_id: int) -> CareerReport:
        """Create a minimal report for a student."""
        report = CareerReport(
            student_id=student_id,
            target_job_code="test",
            content_json=dict(_MINIMAL_REPORT_CONTENT),
            markdown_content="# Test",
            status="completed",
        )
        db.add(report)
        db.commit()
        return report

    def test_student_cannot_mark_other_feedback_as_read(self, client: TestClient, db_session: Session):
        """POST /api/v1/students/me/teacher-feedback/{comment_id}/read should reject
        feedback belonging to another student."""
        _, student_a, headers_a = _make_student(db_session, "stu_fb_a", "Feedback A")
        _, student_b, _ = _make_student(db_session, "stu_fb_b", "Feedback B")
        teacher = self._make_teacher(db_session, "teacher_fb_1")
        report = self._make_report(db_session, student_b.id)

        comment = TeacherComment(
            student_id=student_b.id,
            teacher_id=teacher.id,
            report_id=report.id,
            comment="Feedback for B",
            visible_to_student=True,
        )
        db_session.add(comment)
        db_session.commit()

        resp = client.post(
            f"/api/v1/students/me/teacher-feedback/{comment.id}/read",
            headers=headers_a,
        )
        assert resp.status_code == 403

    def test_student_can_mark_own_feedback_as_read(self, client: TestClient, db_session: Session):
        """POST /api/v1/students/me/teacher-feedback/{comment_id}/read should succeed for own feedback."""
        _, student_a, headers_a = _make_student(db_session, "stu_fb_c", "Feedback C")
        teacher = self._make_teacher(db_session, "teacher_fb_2")
        report = self._make_report(db_session, student_a.id)

        comment = TeacherComment(
            student_id=student_a.id,
            teacher_id=teacher.id,
            report_id=report.id,
            comment="Feedback for A",
            visible_to_student=True,
        )
        db_session.add(comment)
        db_session.commit()

        resp = client.post(
            f"/api/v1/students/me/teacher-feedback/{comment.id}/read",
            headers=headers_a,
        )
        assert resp.status_code == 200


class TestHistoryAuthorization:
    """Verify history list is scoped to the authenticated student."""

    def test_history_returns_only_own_records(self, client: TestClient, db_session: Session):
        """GET /api/v1/students/me/history should not include other student's data."""
        _, student_a, headers_a = _make_student(db_session, "stu_hist_a", "History A")
        _, student_b, _ = _make_student(db_session, "stu_hist_b", "History B")

        # Create a report for student_b
        report_b = CareerReport(
            student_id=student_b.id,
            target_job_code="secret_job",
            content_json={},
            markdown_content="Secret report",
            status="completed",
        )
        db_session.add(report_b)
        db_session.commit()

        # Student a's history should not contain student b's report
        resp = client.get("/api/v1/students/me/history", headers=headers_a)
        assert resp.status_code == 200
        items = resp.json().get("items", [])
        ref_ids = [item.get("ref_id") for item in items]
        assert report_b.id not in ref_ids

    def test_history_includes_own_records(self, client: TestClient, db_session: Session):
        """GET /api/v1/students/me/history should include the student's own records."""
        _, student_a, headers_a = _make_student(db_session, "stu_hist_c", "History C")

        report_a = CareerReport(
            student_id=student_a.id,
            target_job_code="my_job",
            content_json={},
            markdown_content="My report",
            status="completed",
        )
        db_session.add(report_a)
        db_session.commit()

        resp = client.get("/api/v1/students/me/history", headers=headers_a)
        assert resp.status_code == 200
        items = resp.json().get("items", [])
        ref_ids = [item.get("ref_id") for item in items if item.get("type") == "report"]
        assert report_a.id in ref_ids
