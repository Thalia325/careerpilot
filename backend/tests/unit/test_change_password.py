"""Tests for self-service change password flow (US-028)."""

import pytest
from sqlalchemy.orm import Session

from app.api.deps import create_access_token
from app.models import User
from app.services.auth_service import hash_password, verify_password


def _auth_headers(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def _make_user(db: Session, username: str, password: str = "test123") -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        full_name=username,
        role="student",
    )
    db.add(user)
    db.commit()
    return user


class TestChangePassword:
    def test_change_password_success(self, client, db_session):
        user = _make_user(db_session, "chgpw_user", "oldpw123")
        resp = client.post("/api/v1/auth/change-password", headers=_auth_headers(user.id), json={
            "old_password": "oldpw123",
            "new_password": "newpw456",
        })
        assert resp.status_code == 200
        assert resp.json()["message"] == "密码修改成功"

        # Verify old password no longer works, new password does
        db_session.refresh(user)
        assert verify_password("newpw456", user.password_hash)
        assert not verify_password("oldpw123", user.password_hash)

    def test_change_password_wrong_old(self, client, db_session):
        user = _make_user(db_session, "chgpw_wrong", "correct123")
        resp = client.post("/api/v1/auth/change-password", headers=_auth_headers(user.id), json={
            "old_password": "wrong123",
            "new_password": "newpw456",
        })
        assert resp.status_code == 400
        assert "旧密码不正确" in resp.json()["detail"]

    def test_change_password_too_short(self, client, db_session):
        user = _make_user(db_session, "chgpw_short", "oldpw123")
        resp = client.post("/api/v1/auth/change-password", headers=_auth_headers(user.id), json={
            "old_password": "oldpw123",
            "new_password": "abc",
        })
        assert resp.status_code == 400
        assert "至少6位" in resp.json()["detail"]

    def test_change_password_empty_fields(self, client, db_session):
        user = _make_user(db_session, "chgpw_empty", "oldpw123")
        resp = client.post("/api/v1/auth/change-password", headers=_auth_headers(user.id), json={
            "old_password": "",
            "new_password": "",
        })
        assert resp.status_code == 400

    def test_change_password_unauthenticated(self, client, db_session):
        resp = client.post("/api/v1/auth/change-password", json={
            "old_password": "old",
            "new_password": "new",
        })
        assert resp.status_code == 401

    def test_login_with_new_password_after_change(self, client, db_session):
        user = _make_user(db_session, "chgpw_login", "original123")
        # Change password
        client.post("/api/v1/auth/change-password", headers=_auth_headers(user.id), json={
            "old_password": "original123",
            "new_password": "updated456",
        })
        # Login with new password should succeed
        login_resp = client.post("/api/v1/auth/login", json={
            "username": "chgpw_login",
            "password": "updated456",
        })
        assert login_resp.status_code == 200
        assert login_resp.json()["access_token"]

        # Login with old password should fail
        login_old = client.post("/api/v1/auth/login", json={
            "username": "chgpw_login",
            "password": "original123",
        })
        assert login_old.status_code == 401
