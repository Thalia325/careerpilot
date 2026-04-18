"""US-021: Admin user management backend tests.

Verify admin user search, detail, update, and delete operations
with proper authorization and data scoping.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import create_access_token
from app.models import Student, Teacher, User
from app.services.auth_service import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ADMIN_BASE = "/api/v1/admin/users"


def _auth_headers(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def _make_user(db: Session, username: str, role: str, email: str = "", full_name: str = "") -> User:
    user = User(
        username=username,
        password_hash=hash_password("test123"),
        role=role,
        full_name=full_name or username,
        email=email or f"{username}@test.local",
    )
    db.add(user)
    db.commit()
    return user


def _make_student(db: Session, username: str) -> tuple[User, Student]:
    user = _make_user(db, username, "student")
    student = Student(
        user_id=user.id,
        major="软件工程",
        grade="大三",
        career_goal="成为全栈工程师",
        learning_preferences={"style": "visual"},
    )
    db.add(student)
    db.commit()
    return user, student


def _make_teacher(db: Session, username: str) -> tuple[User, Teacher]:
    user = _make_user(db, username, "teacher")
    teacher = Teacher(user_id=user.id, department="计算机科学", title="副教授")
    db.add(teacher)
    db.commit()
    return user, teacher


# ---------------------------------------------------------------------------
# Tests: User search
# ---------------------------------------------------------------------------


class TestAdminUserSearch:
    """Verify admin user list supports keyword and role filtering."""

    def test_list_users_without_filter(self, client: TestClient, db_session: Session):
        """GET /admin/users returns paginated user list."""
        admin = _make_user(db_session, "admin_search_test", "admin")
        _make_student(db_session, "search_student_a")
        _make_student(db_session, "search_student_b")

        resp = client.get(ADMIN_BASE, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total" in data
        assert "items" in data
        assert data["total"] >= 2

    def test_search_by_username(self, client: TestClient, db_session: Session):
        """Keyword search matches username."""
        admin = _make_user(db_session, "admin_search_uname", "admin")
        _make_student(db_session, "unique_username_xyz")
        _make_student(db_session, "other_student_abc")

        resp = client.get(ADMIN_BASE, params={"keyword": "unique_username"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1
        assert any(u["username"] == "unique_username_xyz" for u in items)

    def test_search_by_email(self, client: TestClient, db_session: Session):
        """Keyword search matches email."""
        admin = _make_user(db_session, "admin_search_email", "admin")
        _make_user(db_session, "email_user", "student", email="unique@example.com")

        resp = client.get(ADMIN_BASE, params={"keyword": "unique@example"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert any(u["email"] == "unique@example.com" for u in items)

    def test_search_by_full_name(self, client: TestClient, db_session: Session):
        """Keyword search matches full_name."""
        admin = _make_user(db_session, "admin_search_fname", "admin")
        _make_user(db_session, "fname_user", "student", full_name="张三丰")

        resp = client.get(ADMIN_BASE, params={"keyword": "张三"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert any(u["full_name"] == "张三丰" for u in items)

    def test_filter_by_role(self, client: TestClient, db_session: Session):
        """Role filter returns only users of that role."""
        admin = _make_user(db_session, "admin_search_role", "admin")
        _make_student(db_session, "role_filter_student")
        _make_teacher(db_session, "role_filter_teacher")

        resp = client.get(ADMIN_BASE, params={"role": "teacher"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert all(u["role"] == "teacher" for u in items)
        assert any(u["username"] == "role_filter_teacher" for u in items)

    def test_combined_keyword_and_role_filter(self, client: TestClient, db_session: Session):
        """Keyword + role filter combines both conditions."""
        admin = _make_user(db_session, "admin_search_combo", "admin")
        _make_user(db_session, "combo_teacher_a", "teacher", full_name="组合教师A")
        _make_user(db_session, "combo_student_a", "student", full_name="组合学生A")

        resp = client.get(
            ADMIN_BASE,
            params={"keyword": "组合", "role": "teacher"},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["username"] == "combo_teacher_a"

    def test_search_no_results(self, client: TestClient, db_session: Session):
        """Search with non-matching keyword returns empty list."""
        admin = _make_user(db_session, "admin_search_empty", "admin")

        resp = client.get(ADMIN_BASE, params={"keyword": "nonexistent_xyz_123"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []

    def test_search_pagination(self, client: TestClient, db_session: Session):
        """Pagination parameters work correctly with search."""
        admin = _make_user(db_session, "admin_search_page", "admin")
        for i in range(5):
            _make_user(db_session, f"page_user_{i}", "student")

        resp = client.get(ADMIN_BASE, params={"limit": 2, "skip": 0, "role": "student"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) <= 2


# ---------------------------------------------------------------------------
# Tests: User detail
# ---------------------------------------------------------------------------


class TestAdminUserDetail:
    """Verify admin user detail returns full editable fields."""

    def test_get_user_returns_basic_fields(self, client: TestClient, db_session: Session):
        """GET /admin/users/{id} returns id, username, full_name, role, email, timestamps."""
        admin = _make_user(db_session, "admin_detail_basic", "admin")
        target, _ = _make_student(db_session, "detail_target")

        resp = client.get(f"{ADMIN_BASE}/{target.id}", headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == target.id
        assert data["username"] == "detail_target"
        assert data["full_name"] == "detail_target"
        assert data["role"] == "student"
        assert data["email"] == "detail_target@test.local"
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    def test_get_user_includes_student_profile(self, client: TestClient, db_session: Session):
        """User detail includes student profile for student role."""
        admin = _make_user(db_session, "admin_detail_sprofile", "admin")
        user, student = _make_student(db_session, "detail_student_profile")

        resp = client.get(f"{ADMIN_BASE}/{user.id}", headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "profile" in data
        profile = data["profile"]
        assert profile["student_id"] == student.id
        assert profile["major"] == "软件工程"
        assert profile["grade"] == "大三"
        assert profile["career_goal"] == "成为全栈工程师"
        assert profile["learning_preferences"]["style"] == "visual"

    def test_get_user_includes_teacher_profile(self, client: TestClient, db_session: Session):
        """User detail includes teacher profile for teacher role."""
        admin = _make_user(db_session, "admin_detail_tprofile", "admin")
        user, teacher = _make_teacher(db_session, "detail_teacher_profile")

        resp = client.get(f"{ADMIN_BASE}/{user.id}", headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "profile" in data
        profile = data["profile"]
        assert profile["teacher_id"] == teacher.id
        assert profile["department"] == "计算机科学"
        assert profile["title"] == "副教授"

    def test_get_user_not_found(self, client: TestClient, db_session: Session):
        """GET /admin/users/99999 returns 404."""
        admin = _make_user(db_session, "admin_detail_404", "admin")

        resp = client.get(f"{ADMIN_BASE}/99999", headers=_auth_headers(admin.id))
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests: User update
# ---------------------------------------------------------------------------


class TestAdminUserUpdate:
    """Verify admin user update persists changes and rejects invalid input."""

    def test_update_full_name(self, client: TestClient, db_session: Session):
        """Admin can update user's full_name."""
        admin = _make_user(db_session, "admin_update_name", "admin")
        target = _make_user(db_session, "update_name_target", "student")

        resp = client.put(
            f"{ADMIN_BASE}/{target.id}",
            json={"full_name": "新名字"},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["full_name"] == "新名字"

    def test_update_email(self, client: TestClient, db_session: Session):
        """Admin can update user's email."""
        admin = _make_user(db_session, "admin_update_email", "admin")
        target = _make_user(db_session, "update_email_target", "student")

        resp = client.put(
            f"{ADMIN_BASE}/{target.id}",
            json={"email": "new_email@test.com"},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == "new_email@test.com"

    def test_update_role(self, client: TestClient, db_session: Session):
        """Admin can change user's role."""
        admin = _make_user(db_session, "admin_update_role", "admin")
        target = _make_user(db_session, "update_role_target", "student")

        resp = client.put(
            f"{ADMIN_BASE}/{target.id}",
            json={"role": "teacher"},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["role"] == "teacher"

    def test_update_invalid_role_rejected(self, client: TestClient, db_session: Session):
        """Update with invalid role returns 400."""
        admin = _make_user(db_session, "admin_update_badrole", "admin")
        target = _make_user(db_session, "update_badrole_target", "student")

        resp = client.put(
            f"{ADMIN_BASE}/{target.id}",
            json={"role": "superadmin"},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 400

    def test_update_cannot_remove_own_admin_role(self, client: TestClient, db_session: Session):
        """Admin cannot demote themselves from admin role."""
        admin = _make_user(db_session, "admin_update_self", "admin")

        resp = client.put(
            f"{ADMIN_BASE}/{admin.id}",
            json={"role": "student"},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 400

    def test_update_duplicate_username_rejected(self, client: TestClient, db_session: Session):
        """Update with existing username returns 400."""
        admin = _make_user(db_session, "admin_update_dup", "admin")
        target_a = _make_user(db_session, "dup_user_a", "student")
        _make_user(db_session, "dup_user_b", "student")

        resp = client.put(
            f"{ADMIN_BASE}/{target_a.id}",
            json={"username": "dup_user_b"},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 400

    def test_update_password(self, client: TestClient, db_session: Session):
        """Admin can update user's password."""
        admin = _make_user(db_session, "admin_update_pwd", "admin")
        target = _make_user(db_session, "update_pwd_target", "student")

        resp = client.put(
            f"{ADMIN_BASE}/{target.id}",
            json={"password": "newpassword456"},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 200

        # Verify new password works for login
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "update_pwd_target", "password": "newpassword456"},
        )
        assert login_resp.status_code == 200

    def test_update_nonexistent_user(self, client: TestClient, db_session: Session):
        """Update non-existent user returns 404."""
        admin = _make_user(db_session, "admin_update_404", "admin")

        resp = client.put(
            f"{ADMIN_BASE}/99999",
            json={"full_name": "ghost"},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests: User delete
# ---------------------------------------------------------------------------


class TestAdminUserDelete:
    """Verify admin user delete with safety checks."""

    def test_delete_simple_user(self, client: TestClient, db_session: Session):
        """Admin can delete a user with no related data."""
        admin = _make_user(db_session, "admin_delete_simple", "admin")
        target = _make_user(db_session, "delete_target", "student")

        resp = client.delete(f"{ADMIN_BASE}/{target.id}", headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True

    def test_delete_nonexistent_user(self, client: TestClient, db_session: Session):
        """Delete non-existent user returns 404."""
        admin = _make_user(db_session, "admin_delete_404", "admin")

        resp = client.delete(f"{ADMIN_BASE}/99999", headers=_auth_headers(admin.id))
        assert resp.status_code == 404

    def test_cannot_delete_self(self, client: TestClient, db_session: Session):
        """Admin cannot delete themselves."""
        admin = _make_user(db_session, "admin_delete_self", "admin")

        resp = client.delete(f"{ADMIN_BASE}/{admin.id}", headers=_auth_headers(admin.id))
        assert resp.status_code == 400

    def test_delete_user_with_related_data_blocked(self, client: TestClient, db_session: Session):
        """Deleting a user with reports/matches/links returns 400 with clear reason."""
        from app.models import CareerReport, MatchResult, TeacherStudentLink

        admin = _make_user(db_session, "admin_delete_related", "admin")
        # Create student with teacher binding
        user, student = _make_student(db_session, "delete_related_student")
        teacher_user, teacher = _make_teacher(db_session, "delete_related_teacher")

        # Create a binding
        from app.models import TeacherStudentLink as TSL
        link = TSL(teacher_id=teacher.id, student_id=student.id, status="active")
        db_session.add(link)
        db_session.commit()

        resp = client.delete(f"{ADMIN_BASE}/{user.id}", headers=_auth_headers(admin.id))
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert "绑定" in (detail if isinstance(detail, str) else detail.get("message", ""))


# ---------------------------------------------------------------------------
# Tests: Authorization
# ---------------------------------------------------------------------------


class TestAdminUserAuth:
    """Verify authorization for admin user management endpoints."""

    def test_unauthenticated_access_denied(self, client: TestClient):
        """Unauthenticated requests return 401."""
        resp = client.get(ADMIN_BASE)
        assert resp.status_code == 401
        detail = resp.json()["detail"]
        error_code = detail.get("error_code") if isinstance(detail, dict) else None
        assert error_code == "AUTH_REQUIRED"

    def test_student_cannot_access(self, client: TestClient, db_session: Session):
        """Student role returns 403."""
        user, _ = _make_student(db_session, "auth_student_user_mgmt")

        resp = client.get(ADMIN_BASE, headers=_auth_headers(user.id))
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        error_code = detail.get("error_code") if isinstance(detail, dict) else None
        assert error_code == "INSUFFICIENT_ROLE"

    def test_teacher_cannot_access(self, client: TestClient, db_session: Session):
        """Teacher role returns 403."""
        user, _ = _make_teacher(db_session, "auth_teacher_user_mgmt")

        resp = client.get(ADMIN_BASE, headers=_auth_headers(user.id))
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        error_code = detail.get("error_code") if isinstance(detail, dict) else None
        assert error_code == "INSUFFICIENT_ROLE"

    def test_admin_can_access(self, client: TestClient, db_session: Session):
        """Admin role can access user list."""
        admin = _make_user(db_session, "auth_admin_user_mgmt", "admin")

        resp = client.get(ADMIN_BASE, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
