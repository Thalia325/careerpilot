"""US-023: Admin position (JobProfile) management backend tests.

Verify admin position search, create, update, and delete operations
with proper authorization and data integrity.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import create_access_token
from app.models import JobProfile, User
from app.services.auth_service import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ADMIN_BASE = "/api/v1/admin/positions"


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


def _make_position(db: Session, job_code: str, title: str, **kwargs) -> JobProfile:
    position = JobProfile(
        job_code=job_code,
        title=title,
        summary=kwargs.get("summary", ""),
        skill_requirements=kwargs.get("skill_requirements", []),
        certificate_requirements=kwargs.get("certificate_requirements", []),
        capability_scores=kwargs.get("capability_scores", {}),
        dimension_weights=kwargs.get("dimension_weights", {}),
        explanation_json=kwargs.get("explanation_json", {}),
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    return position


# ---------------------------------------------------------------------------
# Search tests
# ---------------------------------------------------------------------------

class TestPositionSearch:
    def test_list_all(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_pos", "admin")
        _make_position(db_session, "JOB-001", "前端工程师")
        _make_position(db_session, "JOB-002", "后端工程师")
        _make_position(db_session, "JOB-003", "数据分析师")

        resp = client.get(ADMIN_BASE, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 3
        assert len(data["items"]) >= 3

    def test_search_by_keyword_job_code(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_search1", "admin")
        _make_position(db_session, "UNIQUE-CODE-XYZ", "测试岗位A")

        resp = client.get(ADMIN_BASE, params={"keyword": "UNIQUE-CODE"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert any(i["job_code"] == "UNIQUE-CODE-XYZ" for i in items)

    def test_search_by_keyword_title(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_search2", "admin")
        _make_position(db_session, "JOB-T1", "人工智能算法工程师")

        resp = client.get(ADMIN_BASE, params={"keyword": "人工智能"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert any(i["title"] == "人工智能算法工程师" for i in items)

    def test_search_empty_keyword_returns_all(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_search3", "admin")
        _make_position(db_session, "JOB-E1", "岗位E")

        resp_empty = client.get(ADMIN_BASE, params={"keyword": ""}, headers=_auth_headers(admin.id))
        resp_none = client.get(ADMIN_BASE, headers=_auth_headers(admin.id))
        assert resp_empty.json()["data"]["total"] == resp_none.json()["data"]["total"]

    def test_search_no_match(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_search4", "admin")
        resp = client.get(ADMIN_BASE, params={"keyword": "不存在xyz"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 0


# ---------------------------------------------------------------------------
# Create tests
# ---------------------------------------------------------------------------

class TestPositionCreate:
    def test_create_minimal(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_create1", "admin")
        body = {"job_code": "NEW-JOB-001", "title": "全栈工程师"}
        resp = client.post(ADMIN_BASE, json=body, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["job_code"] == "NEW-JOB-001"
        assert data["title"] == "全栈工程师"
        assert data["id"] is not None

    def test_create_full_fields(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_create2", "admin")
        body = {
            "job_code": "FULL-JOB-001",
            "title": "产品经理",
            "summary": "负责产品规划",
            "skill_requirements": ["沟通", "分析"],
            "certificate_requirements": ["PMP"],
            "capability_scores": {"communication": 90},
            "dimension_weights": {"basic_requirements": 0.3},
        }
        resp = client.post(ADMIN_BASE, json=body, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["skill_requirements"] == ["沟通", "分析"]
        assert data["certificate_requirements"] == ["PMP"]
        assert data["capability_scores"] == {"communication": 90}

    def test_create_missing_job_code(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_create3", "admin")
        resp = client.post(ADMIN_BASE, json={"title": "无编码岗位"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 400

    def test_create_missing_title(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_create4", "admin")
        resp = client.post(ADMIN_BASE, json={"job_code": "NO-TITLE"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 400

    def test_create_duplicate_job_code(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_create5", "admin")
        _make_position(db_session, "DUP-001", "岗位A")
        resp = client.post(ADMIN_BASE, json={"job_code": "DUP-001", "title": "岗位B"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 400
        assert "已存在" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Update tests
# ---------------------------------------------------------------------------

class TestPositionUpdate:
    def test_update_title(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_update1", "admin")
        pos = _make_position(db_session, "UPD-001", "旧标题")
        resp = client.put(f"{ADMIN_BASE}/{pos.id}", json={"title": "新标题"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "新标题"

    def test_update_multiple_fields(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_update2", "admin")
        pos = _make_position(db_session, "UPD-002", "原始岗位")
        body = {
            "title": "更新后岗位",
            "summary": "更新后摘要",
            "skill_requirements": ["Python", "SQL"],
        }
        resp = client.put(f"{ADMIN_BASE}/{pos.id}", json=body, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "更新后岗位"
        assert data["summary"] == "更新后摘要"
        assert data["skill_requirements"] == ["Python", "SQL"]

    def test_update_nonexistent(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_update3", "admin")
        resp = client.put(f"{ADMIN_BASE}/99999", json={"title": "X"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 404

    def test_update_duplicate_job_code(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_update4", "admin")
        _make_position(db_session, "ORIG-001", "原始")
        pos2 = _make_position(db_session, "ORIG-002", "第二个")
        resp = client.put(f"{ADMIN_BASE}/{pos2.id}", json={"job_code": "ORIG-001"}, headers=_auth_headers(admin.id))
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Delete tests
# ---------------------------------------------------------------------------

class TestPositionDelete:
    def test_delete_success(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_del1", "admin")
        pos = _make_position(db_session, "DEL-001", "待删除岗位")
        resp = client.delete(f"{ADMIN_BASE}/{pos.id}", headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True

        # 确认已删除
        resp2 = client.get(f"{ADMIN_BASE}/{pos.id}", headers=_auth_headers(admin.id))
        assert resp2.status_code == 404

    def test_delete_nonexistent(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "admin_del2", "admin")
        resp = client.delete(f"{ADMIN_BASE}/99999", headers=_auth_headers(admin.id))
        assert resp.status_code == 404

    def test_delete_with_certificates_cascade(self, client: TestClient, db_session: Session):
        """删除职位画像时应同时清理关联的证书记录。"""
        from app.models import CertificateRequired
        admin = _make_user(db_session, "admin_del3", "admin")
        pos = _make_position(db_session, "DEL-CERT-001", "有证书岗位")
        cert = CertificateRequired(
            job_profile_id=pos.id,
            certificate_name="PMP",
            reason="项目管理",
        )
        db_session.add(cert)
        db_session.commit()

        resp = client.delete(f"{ADMIN_BASE}/{pos.id}", headers=_auth_headers(admin.id))
        assert resp.status_code == 200

        # 证书记录也应被清理
        remaining = db_session.query(CertificateRequired).filter_by(job_profile_id=pos.id).count()
        assert remaining == 0


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------

class TestPositionAuth:
    def test_unauthenticated_list(self, client: TestClient):
        resp = client.get(ADMIN_BASE)
        assert resp.status_code == 401

    def test_student_forbidden(self, client: TestClient, db_session: Session):
        student = _make_user(db_session, "stu_pos", "student")
        resp = client.get(ADMIN_BASE, headers=_auth_headers(student.id))
        assert resp.status_code == 403

    def test_teacher_forbidden(self, client: TestClient, db_session: Session):
        teacher = _make_user(db_session, "tch_pos", "teacher")
        resp = client.get(ADMIN_BASE, headers=_auth_headers(teacher.id))
        assert resp.status_code == 403

    def test_admin_allowed(self, client: TestClient, db_session: Session):
        admin = _make_user(db_session, "adm_pos", "admin")
        resp = client.get(ADMIN_BASE, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
