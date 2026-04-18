"""US-015: Optional teacher binding flow tests.

Verify that:
1. Registration succeeds without teacher binding fields
2. Unbound student session returns teacher=null
3. Profile update works without teacher binding
4. Later teacher binding from profile update works
5. Admin can delete unbound student
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import create_access_token
from app.models import (
    Student,
    Teacher,
    TeacherStudentLink,
    User,
)
from app.services.auth_service import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(db: Session, username: str, role: str = "student", **kwargs) -> User:
    user = User(
        username=username,
        password_hash=hash_password("test123"),
        role=role,
        full_name=kwargs.get("full_name", f"{username}_name"),
        email=kwargs.get("email", f"{username}@test.local"),
    )
    db.add(user)
    db.flush()
    if role == "student":
        student = Student(user_id=user.id, major="软件工程", grade="大三")
        db.add(student)
        db.flush()
    elif role == "teacher":
        teacher = Teacher(user_id=user.id, department="计算机学院", title="讲师")
        db.add(teacher)
        db.flush()
    db.commit()
    return user


def _auth_headers(user: User) -> dict:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRegisterWithoutTeacher:
    """AC1: Registration succeeds when teacher-binding fields are left empty."""

    def test_register_student_no_teacher_code(self, client: TestClient):
        resp = client.post("/api/v1/auth/register", json={
            "username": "student_nobind",
            "password": "test123abc",
            "full_name": "无绑定学生",
            "role": "student",
            "email": "nobind@test.local",
            # teacher_code omitted
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "student"
        assert data["access_token"]

    def test_register_student_empty_teacher_code(self, client: TestClient):
        resp = client.post("/api/v1/auth/register", json={
            "username": "student_empty_bind",
            "password": "test123abc",
            "full_name": "空绑定学生",
            "role": "student",
            "email": "empty_bind@test.local",
            "teacher_code": "",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "student"
        assert data["access_token"]

    def test_register_student_null_teacher_code(self, client: TestClient):
        resp = client.post("/api/v1/auth/register", json={
            "username": "student_null_bind",
            "password": "test123abc",
            "full_name": "Null绑定学生",
            "role": "student",
            "email": "null_bind@test.local",
            "teacher_code": None,
        })
        assert resp.status_code == 200


class TestUnboundStudentSession:
    """AC2: Unbound student session returns teacher=null and clear explanation."""

    def test_session_teacher_null_when_unbound(self, client: TestClient, db_session: Session):
        user = _make_user(db_session, "unbound_session")
        headers = _auth_headers(user)
        resp = client.get("/api/v1/students/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["teacher"] is None

    def test_session_teacher_present_when_bound(self, client: TestClient, db_session: Session):
        teacher_user = _make_user(db_session, "bound_teacher", role="teacher")
        teacher = db_session.scalar(select(Teacher).where(Teacher.user_id == teacher_user.id))
        student_user = _make_user(db_session, "bound_student")
        student = db_session.scalar(select(Student).where(Student.user_id == student_user.id))
        db_session.add(TeacherStudentLink(
            teacher_id=teacher.id, student_id=student.id,
            group_name="test", is_primary=True, source="invite_code", status="active",
        ))
        db_session.commit()

        headers = _auth_headers(student_user)
        resp = client.get("/api/v1/students/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["teacher"] is not None
        assert data["teacher"]["teacher_username"] == "bound_teacher"


class TestProfileUpdateWithoutTeacher:
    """AC4: Profile update flows work when student has no bound teacher."""

    def test_update_profile_without_teacher_code(self, client: TestClient, db_session: Session):
        user = _make_user(db_session, "update_nobind")
        headers = _auth_headers(user)
        resp = client.put("/api/v1/students/me", headers=headers, json={
            "full_name": "更新后姓名",
            "email": "updated@test.local",
            "major": "数据科学",
            "grade": "大四",
            "career_goal": "数据分析师",
            "teacher_code": "",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_name"] == "更新后姓名"
        assert data["major"] == "数据科学"
        assert data["teacher"] is None  # still unbound

    def test_update_profile_omitting_teacher_code(self, client: TestClient, db_session: Session):
        user = _make_user(db_session, "update_omit")
        headers = _auth_headers(user)
        resp = client.put("/api/v1/students/me", headers=headers, json={
            "full_name": "省略teacher_code",
            "email": "omit@test.local",
        })
        assert resp.status_code == 200


class TestLaterTeacherBinding:
    """AC3: A logged-in student can later add teacher binding from profile."""

    def test_bind_teacher_via_profile_update(self, client: TestClient, db_session: Session):
        teacher_user = _make_user(db_session, "later_teacher", role="teacher")
        student_user = _make_user(db_session, "later_student")
        headers = _auth_headers(student_user)

        # Verify initially unbound
        resp = client.get("/api/v1/students/me", headers=headers)
        assert resp.json()["teacher"] is None

        # Bind teacher via profile update
        resp = client.put("/api/v1/students/me", headers=headers, json={
            "teacher_code": "later_teacher",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["teacher"] is not None
        assert data["teacher"]["teacher_username"] == "later_teacher"

    def test_bind_teacher_by_email(self, client: TestClient, db_session: Session):
        teacher_user = _make_user(db_session, "email_teacher", role="teacher", email="teacher@school.edu")
        student_user = _make_user(db_session, "email_student")
        headers = _auth_headers(student_user)

        resp = client.put("/api/v1/students/me", headers=headers, json={
            "teacher_code": "teacher@school.edu",
        })
        assert resp.status_code == 200
        assert resp.json()["teacher"]["teacher_email"] == "teacher@school.edu"

    def test_bind_invalid_teacher_code(self, client: TestClient, db_session: Session):
        student_user = _make_user(db_session, "invalid_bind")
        headers = _auth_headers(student_user)

        resp = client.put("/api/v1/students/me", headers=headers, json={
            "teacher_code": "nonexistent_teacher",
        })
        assert resp.status_code == 400
        assert "未找到" in resp.json()["detail"]


class TestDeleteUnboundStudent:
    """AC4: Admin can delete student without teacher binding."""

    def test_admin_delete_unbound_student(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "delete_admin", role="admin")
        student = _make_user(db_session, "delete_target")
        admin_headers = _auth_headers(admin)

        resp = client.delete(f"/api/v1/admin/users/{student.id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True

    def test_admin_delete_bound_student_blocked(self, client: TestClient, db_session: Session):
        teacher_user = _make_user(db_session, "del_bound_teacher", role="teacher")
        teacher = db_session.scalar(select(Teacher).where(Teacher.user_id == teacher_user.id))
        student_user = _make_user(db_session, "del_bound_student")
        student = db_session.scalar(select(Student).where(Student.user_id == student_user.id))
        db_session.add(TeacherStudentLink(
            teacher_id=teacher.id, student_id=student.id,
            group_name="test", is_primary=True, source="manual", status="active",
        ))
        db_session.commit()

        admin = _make_user(db_session, "del_bound_admin", role="admin")
        admin_headers = _auth_headers(admin)

        resp = client.delete(f"/api/v1/admin/users/{student_user.id}", headers=admin_headers)
        assert resp.status_code == 400
        assert "绑定" in resp.json()["detail"]
