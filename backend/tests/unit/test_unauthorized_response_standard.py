"""US-004: Unauthorized response standard tests.

Verify that all protected APIs return consistent structured error payloads:
- 401 with error_code AUTH_REQUIRED for missing auth
- 401 with error_code INVALID_CREDENTIALS for bad credentials
- 403 with error_code INSUFFICIENT_ROLE for wrong role
- 403 with error_code RESOURCE_FORBIDDEN for wrong owner / out-of-scope

Tests cover at least one endpoint in each portal area:
  student (analysis), teacher (overview), admin (user list)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import create_access_token
from app.models import Student, User
from app.services.auth_service import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_headers(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def _make_user(db: Session, username: str, role: str) -> User:
    user = User(
        username=username,
        password_hash=hash_password("test123"),
        role=role,
        full_name=username,
        email=f"{username}@test.local",
    )
    db.add(user)
    db.commit()
    return user


def _make_student(db: Session, username: str) -> tuple[User, Student]:
    user = _make_user(db, username, "student")
    student = Student(user_id=user.id, major="软件工程", grade="大三")
    db.add(student)
    db.commit()
    return user, student


def _extract_error_code(detail) -> str | None:
    """Extract error_code from either a structured dict or plain string detail."""
    if isinstance(detail, dict):
        return detail.get("error_code")
    return None


def _extract_message(detail) -> str:
    """Extract message from either a structured dict or plain string detail."""
    if isinstance(detail, dict):
        return detail.get("message", "")
    return str(detail)


# ---------------------------------------------------------------------------
# Tests: Unauthenticated (missing auth)
# ---------------------------------------------------------------------------


class TestUnauthenticatedAccess:
    """Verify 401 with AUTH_REQUIRED when no auth header is provided."""

    def test_student_endpoint_requires_auth(self, client: TestClient):
        """GET /api/v1/analysis/1 returns 401 with AUTH_REQUIRED."""
        resp = client.get("/api/v1/analysis/1")
        assert resp.status_code == 401
        detail = resp.json()["detail"]
        assert _extract_error_code(detail) == "AUTH_REQUIRED"

    def test_teacher_endpoint_requires_auth(self, client: TestClient):
        """GET /api/v1/teacher/stats/overview returns 401 with AUTH_REQUIRED."""
        resp = client.get("/api/v1/teacher/stats/overview")
        assert resp.status_code == 401
        detail = resp.json()["detail"]
        assert _extract_error_code(detail) == "AUTH_REQUIRED"

    def test_admin_endpoint_requires_auth(self, client: TestClient):
        """GET /api/v1/admin/users returns 401 with AUTH_REQUIRED."""
        resp = client.get("/api/v1/admin/users")
        assert resp.status_code == 401
        detail = resp.json()["detail"]
        assert _extract_error_code(detail) == "AUTH_REQUIRED"


# ---------------------------------------------------------------------------
# Tests: Invalid credentials (bad token)
# ---------------------------------------------------------------------------


class TestInvalidCredentials:
    """Verify 401 with INVALID_CREDENTIALS for bad/expired tokens."""

    def test_invalid_token_returns_invalid_credentials(self, client: TestClient):
        """Request with invalid JWT returns 401 with INVALID_CREDENTIALS."""
        resp = client.get(
            "/api/v1/analysis/1",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401
        detail = resp.json()["detail"]
        assert _extract_error_code(detail) == "INVALID_CREDENTIALS"

    def test_login_failure_returns_invalid_credentials(self, client: TestClient):
        """POST /api/v1/auth/login with wrong password returns 401 with INVALID_CREDENTIALS."""
        # Create a user first
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            user = _make_user(db, "login_test_user", "student")
        finally:
            db.close()

        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "login_test_user", "password": "wrong_password"},
        )
        assert resp.status_code == 401
        detail = resp.json()["detail"]
        assert _extract_error_code(detail) == "INVALID_CREDENTIALS"


# ---------------------------------------------------------------------------
# Tests: Insufficient role (wrong role)
# ---------------------------------------------------------------------------


class TestInsufficientRole:
    """Verify 403 with INSUFFICIENT_ROLE for wrong-role access."""

    def test_student_cannot_access_teacher_stats(self, client: TestClient, db_session: Session):
        """Student calling teacher overview gets 403 with INSUFFICIENT_ROLE."""
        user, _ = _make_student(db_session, "role_test_student")
        resp = client.get("/api/v1/teacher/stats/overview", headers=_auth_headers(user.id))
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        assert _extract_error_code(detail) == "INSUFFICIENT_ROLE"

    def test_student_cannot_access_admin_users(self, client: TestClient, db_session: Session):
        """Student calling admin user list gets 403 with INSUFFICIENT_ROLE."""
        user, _ = _make_student(db_session, "role_test_student2")
        resp = client.get("/api/v1/admin/users", headers=_auth_headers(user.id))
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        assert _extract_error_code(detail) == "INSUFFICIENT_ROLE"

    def test_teacher_cannot_access_admin_scheduler(self, client: TestClient, db_session: Session):
        """Teacher calling admin scheduler gets 403 with INSUFFICIENT_ROLE."""
        user = _make_user(db_session, "role_test_teacher", "teacher")
        resp = client.get("/api/v1/scheduler/jobs", headers=_auth_headers(user.id))
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        assert _extract_error_code(detail) == "INSUFFICIENT_ROLE"


# ---------------------------------------------------------------------------
# Tests: Resource forbidden (wrong owner / out of scope)
# ---------------------------------------------------------------------------


class TestResourceForbidden:
    """Verify 403 with RESOURCE_FORBIDDEN for wrong-owner access."""

    def test_student_cannot_access_other_student_analysis(self, client: TestClient, db_session: Session):
        """Student accessing another student's analysis gets 403 with RESOURCE_FORBIDDEN."""
        _, student_a = _make_student(db_session, "owner_test_a")
        _, student_b = _make_student(db_session, "owner_test_b")

        resp = client.post(
            "/api/v1/analysis/start",
            json={"student_id": student_b.id, "job_code": "", "file_ids": []},
            headers=_auth_headers(student_a.user_id),
        )
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        assert _extract_error_code(detail) == "RESOURCE_FORBIDDEN"

    def test_teacher_cannot_access_unbound_student_followup(self, client: TestClient, db_session: Session):
        """Teacher accessing unbound student gets 403 with RESOURCE_FORBIDDEN."""
        from app.models import Teacher
        teacher_user = _make_user(db_session, "scope_test_teacher", "teacher")
        teacher = Teacher(user_id=teacher_user.id)
        db_session.add(teacher)
        db_session.commit()

        _, student = _make_student(db_session, "scope_test_student")

        resp = client.patch(
            f"/api/v1/teacher/students/{student.id}/followup",
            params={"status_value": "in_progress"},
            headers=_auth_headers(teacher_user.id),
        )
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        assert _extract_error_code(detail) == "RESOURCE_FORBIDDEN"


# ---------------------------------------------------------------------------
# Tests: Consistent response structure
# ---------------------------------------------------------------------------


class TestConsistentResponseStructure:
    """Verify all error payloads follow the same {message, error_code} structure."""

    def test_401_payload_has_message_and_error_code(self, client: TestClient):
        """401 response detail is a dict with 'message' and 'error_code' keys."""
        resp = client.get("/api/v1/analysis/1")
        assert resp.status_code == 401
        detail = resp.json()["detail"]
        assert isinstance(detail, dict)
        assert "message" in detail
        assert "error_code" in detail

    def test_403_role_payload_has_message_and_error_code(self, client: TestClient, db_session: Session):
        """403 role-check response detail is a dict with 'message' and 'error_code' keys."""
        user, _ = _make_student(db_session, "struct_test_student")
        resp = client.get("/api/v1/teacher/stats/overview", headers=_auth_headers(user.id))
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        assert isinstance(detail, dict)
        assert "message" in detail
        assert "error_code" in detail

    def test_403_resource_payload_has_message_and_error_code(self, client: TestClient, db_session: Session):
        """403 ownership-check response detail is a dict with 'message' and 'error_code' keys."""
        _, student_a = _make_student(db_session, "struct_test_a")
        _, student_b = _make_student(db_session, "struct_test_b")

        resp = client.post(
            "/api/v1/analysis/start",
            json={"student_id": student_b.id, "job_code": "", "file_ids": []},
            headers=_auth_headers(student_a.user_id),
        )
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        assert isinstance(detail, dict)
        assert "message" in detail
        assert "error_code" in detail
        assert "无权" in detail["message"]
