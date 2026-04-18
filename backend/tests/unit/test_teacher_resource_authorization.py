"""US-003: Teacher resource authorization tests.

Verify that teachers can only access data for students bound to them
via TeacherStudentLink, and cross-class access is rejected.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import create_access_token
from app.models import (
    CareerReport,
    GrowthTask,
    Student,
    Teacher,
    TeacherComment,
    TeacherStudentLink,
    User,
)
from app.services.auth_service import hash_password

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


def _make_teacher(db: Session, username: str) -> tuple[User, Teacher, dict]:
    """Create a teacher user and return (user, teacher, auth_headers)."""
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
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    return user, teacher, headers


def _make_student(db: Session, username: str) -> tuple[User, Student, dict]:
    """Create a student user and return (user, student, auth_headers)."""
    user = User(
        username=username,
        password_hash=hash_password("test123"),
        role="student",
        full_name=username,
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


def _bind(teacher: Teacher, student: Student, db: Session) -> None:
    """Create an active binding between teacher and student."""
    db.add(TeacherStudentLink(
        teacher_id=teacher.id,
        student_id=student.id,
        status="active",
        is_primary=True,
        source="test",
    ))
    db.commit()


def _make_report(db: Session, student: Student) -> CareerReport:
    """Create a completed report for a student."""
    report = CareerReport(
        student_id=student.id,
        target_job_code="test",
        content_json=dict(_MINIMAL_REPORT_CONTENT),
        markdown_content="# Test",
        status="completed",
    )
    db.add(report)
    db.commit()
    return report


# ---------------------------------------------------------------------------
# Tests: Followup authorization
# ---------------------------------------------------------------------------


class TestFollowupAuthorization:
    """Verify followup update enforces teacher-student binding."""

    def test_teacher_can_update_followup_for_bound_student(self, client: TestClient, db_session: Session):
        """PATCH /teacher/students/{student_id}/followup succeeds for bound student."""
        _, teacher_a, headers_a = _make_teacher(db_session, "tch_follow_a")
        _, student_a, _ = _make_student(db_session, "stu_follow_a")
        _bind(teacher_a, student_a, db_session)

        resp = client.patch(
            f"/api/v1/teacher/students/{student_a.id}/followup",
            params={"status_value": "in_progress"},
            headers=headers_a,
        )
        assert resp.status_code == 200

    def test_teacher_cannot_update_followup_for_unbound_student(self, client: TestClient, db_session: Session):
        """PATCH /teacher/students/{student_id}/followup rejects unbound student."""
        _, teacher_a, headers_a = _make_teacher(db_session, "tch_follow_b")
        _, student_b, _ = _make_student(db_session, "stu_follow_b")

        resp = client.patch(
            f"/api/v1/teacher/students/{student_b.id}/followup",
            params={"status_value": "in_progress"},
            headers=headers_a,
        )
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        # errors.py returns structured detail dict
        assert "无权" in (detail["message"] if isinstance(detail, dict) else detail)

    def test_admin_can_update_followup_for_any_student(self, client: TestClient, db_session: Session):
        """Admin can bypass teacher-student binding check."""
        admin_user = User(
            username="admin_follow_test",
            password_hash=hash_password("test123"),
            role="admin",
            full_name="Admin Follow",
            email="admin_follow@test.local",
        )
        db_session.add(admin_user)
        db_session.commit()
        token = create_access_token({"sub": str(admin_user.id)})
        admin_headers = {"Authorization": f"Bearer {token}"}

        _, student_x, _ = _make_student(db_session, "stu_follow_admin")
        resp = client.patch(
            f"/api/v1/teacher/students/{student_x.id}/followup",
            params={"status_value": "pending"},
            headers=admin_headers,
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Tests: Comment authorization
# ---------------------------------------------------------------------------


class TestCommentAuthorization:
    """Verify comment CRUD enforces teacher-student binding."""

    def test_teacher_can_comment_on_bound_student_report(self, client: TestClient, db_session: Session):
        """POST /teacher/reports/{report_id}/comments succeeds for bound student."""
        _, teacher_a, headers_a = _make_teacher(db_session, "tch_cmt_a")
        _, student_a, _ = _make_student(db_session, "stu_cmt_a")
        _bind(teacher_a, student_a, db_session)
        report = _make_report(db_session, student_a)

        resp = client.post(
            f"/api/v1/teacher/reports/{report.id}/comments",
            params={"comment_text": "Good work"},
            headers=headers_a,
        )
        assert resp.status_code == 200

    def test_teacher_cannot_comment_on_unbound_student_report(self, client: TestClient, db_session: Session):
        """POST /teacher/reports/{report_id}/comments rejects unbound student."""
        _, teacher_a, headers_a = _make_teacher(db_session, "tch_cmt_b")
        _, student_b, _ = _make_student(db_session, "stu_cmt_b")
        report = _make_report(db_session, student_b)

        resp = client.post(
            f"/api/v1/teacher/reports/{report.id}/comments",
            params={"comment_text": "Unauthorized"},
            headers=headers_a,
        )
        assert resp.status_code == 403

    def test_teacher_can_list_comments_for_bound_student_report(self, client: TestClient, db_session: Session):
        """GET /teacher/reports/{report_id}/comments succeeds for bound student."""
        _, teacher_a, headers_a = _make_teacher(db_session, "tch_cmt_c")
        _, student_a, _ = _make_student(db_session, "stu_cmt_c")
        _bind(teacher_a, student_a, db_session)
        report = _make_report(db_session, student_a)

        resp = client.get(
            f"/api/v1/teacher/reports/{report.id}/comments",
            headers=headers_a,
        )
        assert resp.status_code == 200

    def test_teacher_cannot_list_comments_for_unbound_student_report(self, client: TestClient, db_session: Session):
        """GET /teacher/reports/{report_id}/comments rejects unbound student."""
        _, teacher_a, headers_a = _make_teacher(db_session, "tch_cmt_d")
        _, student_b, _ = _make_student(db_session, "stu_cmt_d")
        report = _make_report(db_session, student_b)

        resp = client.get(
            f"/api/v1/teacher/reports/{report.id}/comments",
            headers=headers_a,
        )
        assert resp.status_code == 403

    def test_teacher_cannot_update_unbound_student_comment(self, client: TestClient, db_session: Session):
        """PUT /teacher/comments/{comment_id} rejects comment for unbound student."""
        _, teacher_a, headers_a = _make_teacher(db_session, "tch_cmt_e")
        _, teacher_b, _ = _make_teacher(db_session, "tch_cmt_f")
        _, student_b, _ = _make_student(db_session, "stu_cmt_f")
        _bind(teacher_b, student_b, db_session)
        report = _make_report(db_session, student_b)

        # Teacher B creates a comment
        comment = TeacherComment(
            teacher_id=teacher_b.user_id,
            student_id=student_b.id,
            report_id=report.id,
            comment="Original comment",
            priority="normal",
            visible_to_student=True,
        )
        db_session.add(comment)
        db_session.commit()

        # Teacher A (unbound) cannot update teacher B's comment
        resp = client.put(
            f"/api/v1/teacher/comments/{comment.id}",
            params={"comment_text": "Hacked"},
            headers=headers_a,
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Tests: Report detail authorization
# ---------------------------------------------------------------------------


class TestReportDetailAuthorization:
    """Verify teacher report access is limited to bound students."""

    def test_teacher_can_view_bound_student_report(self, client: TestClient, db_session: Session):
        """GET /teacher/reports/{report_id} succeeds for bound student."""
        _, teacher_a, headers_a = _make_teacher(db_session, "tch_rpt_a")
        _, student_a, _ = _make_student(db_session, "stu_rpt_a")
        _bind(teacher_a, student_a, db_session)
        report = _make_report(db_session, student_a)

        resp = client.get(f"/api/v1/teacher/reports/{report.id}", headers=headers_a)
        assert resp.status_code == 200

    def test_teacher_cannot_view_unbound_student_report(self, client: TestClient, db_session: Session):
        """GET /teacher/reports/{report_id} rejects unbound student."""
        _, teacher_a, headers_a = _make_teacher(db_session, "tch_rpt_b")
        _, student_b, _ = _make_student(db_session, "stu_rpt_b")
        report = _make_report(db_session, student_b)

        resp = client.get(f"/api/v1/teacher/reports/{report.id}", headers=headers_a)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Tests: Overview stats scoping
# ---------------------------------------------------------------------------


class TestOverviewStatsScoping:
    """Verify overview stats are scoped to bound students for teachers."""

    def test_teacher_overview_only_counts_bound_students(self, client: TestClient, db_session: Session):
        """GET /teacher/stats/overview returns counts only for bound students."""
        _, teacher_a, headers_a = _make_teacher(db_session, "tch_stats_a")
        _, student_a, _ = _make_student(db_session, "stu_stats_a")
        _, student_b, _ = _make_student(db_session, "stu_stats_b")
        _bind(teacher_a, student_a, db_session)

        # Create report for student_b (unbound)
        _make_report(db_session, student_b)

        resp = client.get("/api/v1/teacher/stats/overview", headers=headers_a)
        assert resp.status_code == 200
        data = resp.json()["data"]
        # total_students should only count bound students (1)
        assert data["total_students"] == 1

    def test_unbound_teacher_overview_shows_zero(self, client: TestClient, db_session: Session):
        """Unbound teacher sees zero students in overview."""
        _, teacher_x, headers_x = _make_teacher(db_session, "tch_stats_b")

        resp = client.get("/api/v1/teacher/stats/overview", headers=headers_x)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_students"] == 0

    def test_teacher_class_overview_scoped_to_bound(self, client: TestClient, db_session: Session):
        """GET /teacher/stats/class-overview filters by binding."""
        _, teacher_a, headers_a = _make_teacher(db_session, "tch_stats_c")
        _, student_a, _ = _make_student(db_session, "stu_stats_c")
        _, student_b, _ = _make_student(db_session, "stu_stats_d")
        _bind(teacher_a, student_a, db_session)

        # student_b is unbound and has a report
        _make_report(db_session, student_b)

        resp = client.get("/api/v1/teacher/stats/class-overview", headers=headers_a)
        assert resp.status_code == 200
        data = resp.json()["data"]
        # Only 1 bound student, so report_completion_rate should reflect that
        assert data["report_completion_rate"] == 0.0  # student_a has no report
