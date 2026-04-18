"""US-019: Teacher roster management backend tests.

Verify that teachers can search, add, and remove students from their roster,
and that cross-teacher binding is properly rejected.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import create_access_token
from app.models import Student, Teacher, TeacherStudentLink, User
from app.services.auth_service import hash_password


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


def _make_student(db: Session, username: str, major: str = "软件工程", grade: str = "大三") -> tuple[User, Student, dict]:
    """Create a student user and return (user, student, auth_headers)."""
    user = User(
        username=username,
        password_hash=hash_password("test123"),
        role="student",
        full_name=f"学生_{username}",
        email=f"{username}@test.local",
    )
    db.add(user)
    db.flush()
    student = Student(user_id=user.id, major=major, grade=grade)
    db.add(student)
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    return user, student, headers


def _bind(teacher: Teacher, student: Student, db: Session) -> TeacherStudentLink:
    """Create an active binding between teacher and student."""
    link = TeacherStudentLink(
        teacher_id=teacher.id,
        student_id=student.id,
        status="active",
        is_primary=True,
        source="test",
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


# ---------------------------------------------------------------------------
# Tests: Roster search
# ---------------------------------------------------------------------------


class TestRosterSearch:
    """GET /teacher/roster/search — search candidate students."""

    def test_search_by_username(self, client: TestClient, db_session: Session):
        """Search returns students matching username."""
        _, teacher, headers = _make_teacher(db_session, "tch_search1")
        _, student_a, _ = _make_student(db_session, "stu_search_alpha")

        resp = client.get("/api/v1/teacher/roster/search", params={"keyword": "alpha"}, headers=headers)
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) >= 1
        assert any(i["username"] == "stu_search_alpha" for i in items)

    def test_search_by_email(self, client: TestClient, db_session: Session):
        """Search returns students matching email."""
        _, teacher, headers = _make_teacher(db_session, "tch_search2")
        _, student_a, _ = _make_student(db_session, "stu_email_test")

        resp = client.get("/api/v1/teacher/roster/search", params={"keyword": "stu_email_test"}, headers=headers)
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert any(i["email"] == "stu_email_test@test.local" for i in items)

    def test_search_by_major(self, client: TestClient, db_session: Session):
        """Search returns students matching major."""
        _, teacher, headers = _make_teacher(db_session, "tch_search3")
        _, student_a, _ = _make_student(db_session, "stu_major_test", major="人工智能")

        resp = client.get("/api/v1/teacher/roster/search", params={"keyword": "人工智能"}, headers=headers)
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert any(i["major"] == "人工智能" for i in items)

    def test_search_by_grade(self, client: TestClient, db_session: Session):
        """Search returns students matching grade."""
        _, teacher, headers = _make_teacher(db_session, "tch_search4")
        _, student_a, _ = _make_student(db_session, "stu_grade_test", grade="研一")

        resp = client.get("/api/v1/teacher/roster/search", params={"keyword": "研一"}, headers=headers)
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert any(i["grade"] == "研一" for i in items)

    def test_search_marks_already_bound(self, client: TestClient, db_session: Session):
        """Search results indicate whether student is already bound to teacher."""
        _, teacher, headers = _make_teacher(db_session, "tch_search5")
        _, student_a, _ = _make_student(db_session, "stu_bound_marker")
        _bind(teacher, student_a, db_session)

        resp = client.get("/api/v1/teacher/roster/search", params={"keyword": "stu_bound_marker"}, headers=headers)
        assert resp.status_code == 200
        items = resp.json()["data"]
        found = [i for i in items if i["username"] == "stu_bound_marker"]
        assert len(found) == 1
        assert found[0]["already_bound"] is True

    def test_search_requires_keyword(self, client: TestClient, db_session: Session):
        """Search rejects empty keyword."""
        _, teacher, headers = _make_teacher(db_session, "tch_search6")

        resp = client.get("/api/v1/teacher/roster/search", params={"keyword": ""}, headers=headers)
        assert resp.status_code == 422

    def test_search_student_role_rejected(self, client: TestClient, db_session: Session):
        """Student role cannot access roster search."""
        _, _, headers = _make_student(db_session, "stu_search_role")

        resp = client.get("/api/v1/teacher/roster/search", params={"keyword": "test"}, headers=headers)
        assert resp.status_code == 403

    def test_search_unauthenticated_rejected(self, client: TestClient, db_session: Session):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/teacher/roster/search", params={"keyword": "test"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: Add student to roster
# ---------------------------------------------------------------------------


class TestAddStudentToRoster:
    """POST /teacher/roster/{student_id} — bind student to teacher."""

    def test_add_student_success(self, client: TestClient, db_session: Session):
        """Teacher can add an unbound student."""
        _, teacher, headers = _make_teacher(db_session, "tch_add1")
        _, student_a, _ = _make_student(db_session, "stu_add1")

        resp = client.post(f"/api/v1/teacher/roster/{student_a.id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["student_id"] == student_a.id
        assert data["teacher_id"] == teacher.id
        assert data["status"] == "active"

        # Verify link exists in DB
        link = db_session.scalar(
            select(TeacherStudentLink).where(
                TeacherStudentLink.teacher_id == teacher.id,
                TeacherStudentLink.student_id == student_a.id,
            )
        )
        assert link is not None
        assert link.status == "active"

    def test_add_with_group_name(self, client: TestClient, db_session: Session):
        """Teacher can add student with a group name."""
        _, teacher, headers = _make_teacher(db_session, "tch_add2")
        _, student_a, _ = _make_student(db_session, "stu_add2")

        resp = client.post(
            f"/api/v1/teacher/roster/{student_a.id}",
            params={"group_name": "ClassA"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["group_name"] == "ClassA"

    def test_add_already_bound_same_teacher(self, client: TestClient, db_session: Session):
        """Adding an already-bound student returns 409."""
        _, teacher, headers = _make_teacher(db_session, "tch_add3")
        _, student_a, _ = _make_student(db_session, "stu_add3")
        _bind(teacher, student_a, db_session)

        resp = client.post(f"/api/v1/teacher/roster/{student_a.id}", headers=headers)
        assert resp.status_code == 409

    def test_add_already_bound_other_teacher(self, client: TestClient, db_session: Session):
        """Adding a student bound to another teacher returns 403."""
        _, teacher_a, _ = _make_teacher(db_session, "tch_add4a")
        _, teacher_b, headers_b = _make_teacher(db_session, "tch_add4b")
        _, student_a, _ = _make_student(db_session, "stu_add4")
        _bind(teacher_a, student_a, db_session)

        resp = client.post(f"/api/v1/teacher/roster/{student_a.id}", headers=headers_b)
        assert resp.status_code == 403

    def test_add_nonexistent_student(self, client: TestClient, db_session: Session):
        """Adding a nonexistent student returns 404."""
        _, teacher, headers = _make_teacher(db_session, "tch_add5")

        resp = client.post("/api/v1/teacher/roster/99999", headers=headers)
        assert resp.status_code == 404

    def test_add_student_role_rejected(self, client: TestClient, db_session: Session):
        """Student role cannot add to roster."""
        _, _, headers = _make_student(db_session, "stu_add_role")
        _, student_a, _ = _make_student(db_session, "stu_add_target")

        resp = client.post(f"/api/v1/teacher/roster/{student_a.id}", headers=headers)
        assert resp.status_code == 403

    def test_add_unauthenticated_rejected(self, client: TestClient, db_session: Session):
        """Unauthenticated request returns 401."""
        resp = client.post("/api/v1/teacher/roster/1")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: Remove student from roster
# ---------------------------------------------------------------------------


class TestRemoveStudentFromRoster:
    """DELETE /teacher/roster/{student_id} — unbind student from teacher."""

    def test_remove_student_success(self, client: TestClient, db_session: Session):
        """Teacher can remove a bound student."""
        _, teacher, headers = _make_teacher(db_session, "tch_rm1")
        _, student_a, _ = _make_student(db_session, "stu_rm1")
        _bind(teacher, student_a, db_session)

        resp = client.delete(f"/api/v1/teacher/roster/{student_a.id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["removed"] is True

        # Verify link is now inactive
        link = db_session.scalar(
            select(TeacherStudentLink).where(
                TeacherStudentLink.teacher_id == teacher.id,
                TeacherStudentLink.student_id == student_a.id,
            )
        )
        assert link is not None
        assert link.status == "inactive"

    def test_remove_not_bound(self, client: TestClient, db_session: Session):
        """Removing a student not in roster returns 404."""
        _, teacher, headers = _make_teacher(db_session, "tch_rm2")
        _, student_a, _ = _make_student(db_session, "stu_rm2")

        resp = client.delete(f"/api/v1/teacher/roster/{student_a.id}", headers=headers)
        assert resp.status_code == 404

    def test_remove_nonexistent_student(self, client: TestClient, db_session: Session):
        """Removing a nonexistent student returns 404."""
        _, teacher, headers = _make_teacher(db_session, "tch_rm3")

        resp = client.delete("/api/v1/teacher/roster/99999", headers=headers)
        assert resp.status_code == 404

    def test_remove_other_teacher_student(self, client: TestClient, db_session: Session):
        """Teacher cannot remove student bound to another teacher."""
        _, teacher_a, _ = _make_teacher(db_session, "tch_rm4a")
        _, teacher_b, headers_b = _make_teacher(db_session, "tch_rm4b")
        _, student_a, _ = _make_student(db_session, "stu_rm4")
        _bind(teacher_a, student_a, db_session)

        resp = client.delete(f"/api/v1/teacher/roster/{student_a.id}", headers=headers_b)
        assert resp.status_code == 404

        # Verify original link is still active
        link = db_session.scalar(
            select(TeacherStudentLink).where(
                TeacherStudentLink.teacher_id == teacher_a.id,
                TeacherStudentLink.student_id == student_a.id,
            )
        )
        assert link is not None
        assert link.status == "active"

    def test_remove_student_role_rejected(self, client: TestClient, db_session: Session):
        """Student role cannot remove from roster."""
        _, _, headers = _make_student(db_session, "stu_rm_role")

        resp = client.delete("/api/v1/teacher/roster/1", headers=headers)
        assert resp.status_code == 403

    def test_remove_unauthenticated_rejected(self, client: TestClient, db_session: Session):
        """Unauthenticated request returns 401."""
        resp = client.delete("/api/v1/teacher/roster/1")
        assert resp.status_code == 401
