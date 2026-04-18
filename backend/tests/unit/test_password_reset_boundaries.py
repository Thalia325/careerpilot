"""Tests for admin and teacher password reset boundaries (US-029)."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import create_access_token
from app.models import Student, Teacher, TeacherStudentLink, User
from app.services.auth_service import hash_password, verify_password


def _auth_headers(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def _make_user(db: Session, username: str, role: str = "student") -> User:
    user = User(
        username=username,
        password_hash=hash_password("original123"),
        full_name=username,
        role=role,
    )
    db.add(user)
    db.commit()
    return user


class TestAdminResetPassword:
    """Admin can reset any user's password through the admin endpoint."""

    def test_admin_reset_success(self, client, db_session):
        admin = _make_user(db_session, "adm_reset", "admin")
        target = _make_user(db_session, "target_user", "student")
        # Also need a Student record
        db_session.add(Student(user_id=target.id, major="", grade=""))
        db_session.commit()

        resp = client.put(f"/api/v1/admin/users/{target.id}", headers=_auth_headers(admin.id), json={
            "password": "newpassword789",
        })
        assert resp.status_code == 200

        # Verify new password works
        db_session.refresh(target)
        assert verify_password("newpassword789", target.password_hash)

    def test_admin_reset_nonexistent_user(self, client, db_session):
        admin = _make_user(db_session, "adm_reset_404", "admin")
        resp = client.put("/api/v1/admin/users/99999", headers=_auth_headers(admin.id), json={
            "password": "newpw123456",
        })
        assert resp.status_code == 404


class TestTeacherResetPassword:
    """Teacher can only reset passwords for students in their class."""

    def test_teacher_reset_bound_student(self, client, db_session):
        teacher_user = _make_user(db_session, "tch_reset", "teacher")
        teacher = Teacher(user_id=teacher_user.id, department="CS", title="Prof")
        db_session.add(teacher)
        db_session.flush()

        student_user = _make_user(db_session, "stu_reset_bound", "student")
        student = Student(user_id=student_user.id, major="CS", grade="2024")
        db_session.add(student)
        db_session.flush()

        link = TeacherStudentLink(teacher_id=teacher.id, student_id=student.id, status="active")
        db_session.add(link)
        db_session.commit()

        resp = client.post(
            f"/api/v1/teacher/students/{student_user.id}/reset-password",
            headers=_auth_headers(teacher_user.id),
            json={"new_password": "resetpw456"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["message"] == "密码重置成功"

        db_session.refresh(student_user)
        assert verify_password("resetpw456", student_user.password_hash)

    def test_teacher_reset_unbound_student_forbidden(self, client, db_session):
        teacher_user = _make_user(db_session, "tch_reset_ub", "teacher")
        teacher = Teacher(user_id=teacher_user.id, department="CS", title="Prof")
        db_session.add(teacher)
        db_session.flush()

        student_user = _make_user(db_session, "stu_unbound", "student")
        student = Student(user_id=student_user.id, major="CS", grade="2024")
        db_session.add(student)
        db_session.commit()

        resp = client.post(
            f"/api/v1/teacher/students/{student_user.id}/reset-password",
            headers=_auth_headers(teacher_user.id),
            json={"new_password": "resetpw789"},
        )
        assert resp.status_code == 403

    def test_teacher_reset_too_short_password(self, client, db_session):
        teacher_user = _make_user(db_session, "tch_reset_short", "teacher")
        teacher = Teacher(user_id=teacher_user.id, department="CS", title="Prof")
        db_session.add(teacher)
        db_session.flush()

        student_user = _make_user(db_session, "stu_reset_short", "student")
        student = Student(user_id=student_user.id, major="CS", grade="2024")
        db_session.add(student)
        db_session.flush()

        link = TeacherStudentLink(teacher_id=teacher.id, student_id=student.id, status="active")
        db_session.add(link)
        db_session.commit()

        resp = client.post(
            f"/api/v1/teacher/students/{student_user.id}/reset-password",
            headers=_auth_headers(teacher_user.id),
            json={"new_password": "abc"},
        )
        assert resp.status_code == 400

    def test_student_cannot_use_teacher_reset(self, client, db_session):
        student_user = _make_user(db_session, "stu_abuse", "student")
        db_session.add(Student(user_id=student_user.id, major="", grade=""))
        db_session.commit()

        resp = client.post(
            f"/api/v1/teacher/students/{student_user.id}/reset-password",
            headers=_auth_headers(student_user.id),
            json={"new_password": "hacked123"},
        )
        assert resp.status_code == 403

    def test_unauthenticated_reset(self, client, db_session):
        resp = client.post(
            "/api/v1/teacher/students/1/reset-password",
            json={"new_password": "newpw456"},
        )
        assert resp.status_code == 401

    def test_admin_can_use_teacher_reset_endpoint(self, client, db_session):
        admin = _make_user(db_session, "adm_tch_reset", "admin")
        student_user = _make_user(db_session, "stu_admin_reset", "student")
        db_session.add(Student(user_id=student_user.id, major="", grade=""))
        db_session.commit()

        resp = client.post(
            f"/api/v1/teacher/students/{student_user.id}/reset-password",
            headers=_auth_headers(admin.id),
            json={"new_password": "adminreset123"},
        )
        assert resp.status_code == 200
