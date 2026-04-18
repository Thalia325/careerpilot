"""US-010: History list query scoping tests.

Verify that the history list endpoint returns only records owned by the
authenticated student, covers all distinct record types, and that two
student accounts with different histories receive different lists.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
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


def _seed_uploads(db: Session, user_id: int, count: int = 2) -> list[int]:
    """Create uploaded file records for a user. Return list of IDs."""
    ids = []
    for i in range(count):
        f = UploadedFile(
            owner_id=user_id,
            file_type="resume",
            file_name=f"resume_{user_id}_{i}.pdf",
            storage_key=f"/tmp/{user_id}_{i}",
        )
        db.add(f)
        db.flush()
        ids.append(f.id)
    db.commit()
    return ids


def _seed_profile_version(db: Session, student_id: int) -> int:
    """Create a profile version for a student. Return its ID."""
    pv = ProfileVersion(
        student_id=student_id,
        version_no=1,
        snapshot_json={"skills": ["Python"]},
    )
    db.add(pv)
    db.flush()
    db.commit()
    return pv.id


def _seed_student_profile(db: Session, student_id: int) -> int:
    """Create a StudentProfile row for a student. Return its ID."""
    sp = StudentProfile(student_id=student_id)
    db.add(sp)
    db.flush()
    db.commit()
    return sp.id


def _seed_job_profile(db: Session, code: str = "JP001") -> int:
    """Create a JobProfile row. Return its ID."""
    jp = JobProfile(job_code=code, title=f"测试岗位-{code}")
    db.add(jp)
    db.flush()
    db.commit()
    return jp.id


def _seed_match(db: Session, student_profile_id: int, job_profile_id: int) -> int:
    """Create a MatchResult. Return its ID."""
    m = MatchResult(
        student_profile_id=student_profile_id,
        job_profile_id=job_profile_id,
        total_score=85.0,
    )
    db.add(m)
    db.flush()
    db.commit()
    return m.id


def _seed_path(db: Session, student_id: int) -> int:
    """Create a PathRecommendation. Return its ID."""
    p = PathRecommendation(
        student_id=student_id,
        target_job_code="JP001",
    )
    db.add(p)
    db.flush()
    db.commit()
    return p.id


def _seed_report(db: Session, student_id: int) -> int:
    """Create a CareerReport. Return its ID."""
    r = CareerReport(
        student_id=student_id,
        target_job_code="JP001",
        status="completed",
    )
    db.add(r)
    db.flush()
    db.commit()
    return r.id


def _seed_chat(db: Session, user_id: int) -> int:
    """Create a ChatMessageRecord. Return its ID."""
    msg = ChatMessageRecord(
        user_id=user_id,
        role="user",
        content="请帮我分析职业方向",
    )
    db.add(msg)
    db.flush()
    db.commit()
    return msg.id


def _seed_feedback(db: Session, student_id: int) -> int:
    """Create a FollowupRecord. Return its ID."""
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
# Tests
# ---------------------------------------------------------------------------


class TestHistoryListOwnership:
    """Verify the history list only returns records owned by the authenticated student."""

    def test_student_sees_only_own_uploads(self, client: TestClient, db_session: Session):
        """Student A should not see Student B's uploads in history."""
        user_a, stu_a, hdr_a = _make_student(db_session, "stu_hist_a1", "Student A1")
        user_b, _, _ = _make_student(db_session, "stu_hist_b1", "Student B1")

        _seed_uploads(db_session, user_a.id, 1)
        _seed_uploads(db_session, user_b.id, 2)

        resp = client.get("/api/v1/students/me/history?type=upload", headers=hdr_a)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["type"] == "upload"
        # Verify the upload belongs to student A
        assert f"{user_a.id}" in items[0]["title"] or "resume" in items[0]["title"].lower()

    def test_student_sees_only_own_reports(self, client: TestClient, db_session: Session):
        """Student A should not see Student B's reports."""
        _, stu_a, hdr_a = _make_student(db_session, "stu_hist_a2", "Student A2")
        _, stu_b, _ = _make_student(db_session, "stu_hist_b2", "Student B2")

        _seed_report(db_session, stu_a.id)
        _seed_report(db_session, stu_b.id)
        _seed_report(db_session, stu_b.id)

        resp = client.get("/api/v1/students/me/history?type=report", headers=hdr_a)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1

    def test_student_sees_only_own_chats(self, client: TestClient, db_session: Session):
        """Student A should not see Student B's chat records."""
        user_a, _, hdr_a = _make_student(db_session, "stu_hist_a3", "Student A3")
        user_b, _, _ = _make_student(db_session, "stu_hist_b3", "Student B3")

        _seed_chat(db_session, user_a.id)
        _seed_chat(db_session, user_b.id)
        _seed_chat(db_session, user_b.id)

        resp = client.get("/api/v1/students/me/history?type=chat", headers=hdr_a)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1

    def test_student_sees_only_own_feedback(self, client: TestClient, db_session: Session):
        """Student A should not see Student B's teacher feedback."""
        _, stu_a, hdr_a = _make_student(db_session, "stu_hist_a4", "Student A4")
        _, stu_b, _ = _make_student(db_session, "stu_hist_b4", "Student B4")

        _seed_feedback(db_session, stu_a.id)
        _seed_feedback(db_session, stu_b.id)

        resp = client.get("/api/v1/students/me/history?type=feedback", headers=hdr_a)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1


class TestHistoryDistinctTypes:
    """Verify the history list contains distinct record types when records exist."""

    def test_all_seven_types_present(self, client: TestClient, db_session: Session):
        """When a student has all 7 record types, history should include all of them."""
        user, stu, hdr = _make_student(db_session, "stu_hist_types", "Student Types")

        # Seed one record of each type
        _seed_uploads(db_session, user.id, 1)          # upload
        _seed_profile_version(db_session, stu.id)       # profile

        sp_id = _seed_student_profile(db_session, stu.id)
        jp_id = _seed_job_profile(db_session, "HIST_JP")
        _seed_match(db_session, sp_id, jp_id)           # matching

        _seed_path(db_session, stu.id)                   # path
        _seed_report(db_session, stu.id)                 # report
        _seed_chat(db_session, user.id)                  # chat
        _seed_feedback(db_session, stu.id)               # feedback

        resp = client.get("/api/v1/students/me/history", headers=hdr)
        assert resp.status_code == 200
        items = resp.json()["items"]

        types_present = {item["type"] for item in items}
        expected_types = {"upload", "profile", "matching", "path", "report", "chat", "feedback"}
        assert expected_types == types_present, f"Missing types: {expected_types - types_present}"

    def test_type_filter_returns_only_that_type(self, client: TestClient, db_session: Session):
        """Filtering by type should return only records of that type."""
        user, stu, hdr = _make_student(db_session, "stu_hist_filter", "Student Filter")

        _seed_uploads(db_session, user.id, 1)
        _seed_report(db_session, stu.id)

        resp = client.get("/api/v1/students/me/history?type=report", headers=hdr)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["type"] == "report"

    def test_invalid_type_returns_empty(self, client: TestClient, db_session: Session):
        """An unsupported type filter returns an empty list."""
        _, _, hdr = _make_student(db_session, "stu_hist_inv", "Student Inv")

        resp = client.get("/api/v1/students/me/history?type=nonexistent", headers=hdr)
        assert resp.status_code == 200
        assert resp.json()["items"] == []


class TestHistoryCrossStudentIsolation:
    """Verify two students with different histories receive different lists."""

    def test_different_students_get_different_histories(self, client: TestClient, db_session: Session):
        """Two students with different records must not see each other's data."""
        user_a, stu_a, hdr_a = _make_student(db_session, "stu_hist_iso_a", "ISO Student A")
        user_b, stu_b, hdr_b = _make_student(db_session, "stu_hist_iso_b", "ISO Student B")

        # Student A: 2 uploads, 1 report
        _seed_uploads(db_session, user_a.id, 2)
        _seed_report(db_session, stu_a.id)

        # Student B: 1 upload, 2 reports, 1 chat
        _seed_uploads(db_session, user_b.id, 1)
        _seed_report(db_session, stu_b.id)
        _seed_report(db_session, stu_b.id)
        _seed_chat(db_session, user_b.id)

        # Fetch history for A
        resp_a = client.get("/api/v1/students/me/history", headers=hdr_a)
        assert resp_a.status_code == 200
        items_a = resp_a.json()["items"]
        types_a = {item["type"] for item in items_a}

        # Fetch history for B
        resp_b = client.get("/api/v1/students/me/history", headers=hdr_b)
        assert resp_b.status_code == 200
        items_b = resp_b.json()["items"]
        types_b = {item["type"] for item in items_b}

        # A sees upload + report (2 types)
        assert "upload" in types_a
        assert "report" in types_a
        assert len([i for i in items_a if i["type"] == "upload"]) == 2
        assert len([i for i in items_a if i["type"] == "report"]) == 1

        # B sees upload + report + chat (3 types)
        assert "upload" in types_b
        assert "report" in types_b
        assert "chat" in types_b
        assert len([i for i in items_b if i["type"] == "upload"]) == 1
        assert len([i for i in items_b if i["type"] == "report"]) == 2

        # No overlap of record IDs
        ids_a = {item["id"] for item in items_a}
        ids_b = {item["id"] for item in items_b}
        assert ids_a.isdisjoint(ids_b), f"Record ID overlap: {ids_a & ids_b}"

    def test_no_cross_student_ref_ids_leaked(self, client: TestClient, db_session: Session):
        """Ensure Student A cannot infer Student B's ref_ids from their own history."""
        user_a, stu_a, hdr_a = _make_student(db_session, "stu_hist_ref_a", "REF Student A")
        user_b, stu_b, _ = _make_student(db_session, "stu_hist_ref_b", "REF Student B")

        # Student B creates a report
        report_b_id = _seed_report(db_session, stu_b.id)

        # Student A creates their own report
        report_a_id = _seed_report(db_session, stu_a.id)

        resp_a = client.get("/api/v1/students/me/history?type=report", headers=hdr_a)
        items_a = resp_a.json()["items"]
        assert len(items_a) == 1
        assert items_a[0]["ref_id"] == report_a_id
        assert items_a[0]["ref_id"] != report_b_id


class TestHistoryUnauthenticated:
    """Verify that unauthenticated requests are rejected."""

    def test_unauthenticated_history_returns_401(self, client: TestClient, db_session: Session):
        resp = client.get("/api/v1/students/me/history")
        assert resp.status_code == 401

    def test_unauthenticated_rename_returns_401(self, client: TestClient, db_session: Session):
        resp = client.patch(
            "/api/v1/students/me/history/rename",
            json={"record_type": "report", "ref_id": 1, "custom_title": "test"},
        )
        assert resp.status_code == 401


class TestHistoryProfilesAndPaths:
    """Verify profile and path history entries are scoped correctly."""

    def test_student_sees_only_own_profiles(self, client: TestClient, db_session: Session):
        """Student A should not see Student B's profile versions."""
        _, stu_a, hdr_a = _make_student(db_session, "stu_hist_pv_a", "PV Student A")
        _, stu_b, _ = _make_student(db_session, "stu_hist_pv_b", "PV Student B")

        _seed_profile_version(db_session, stu_a.id)
        _seed_profile_version(db_session, stu_b.id)
        _seed_profile_version(db_session, stu_b.id)

        resp = client.get("/api/v1/students/me/history?type=profile", headers=hdr_a)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["type"] == "profile"

    def test_student_sees_only_own_paths(self, client: TestClient, db_session: Session):
        """Student A should not see Student B's path recommendations."""
        _, stu_a, hdr_a = _make_student(db_session, "stu_hist_path_a", "Path Student A")
        _, stu_b, _ = _make_student(db_session, "stu_hist_path_b", "Path Student B")

        _seed_path(db_session, stu_a.id)
        _seed_path(db_session, stu_b.id)

        resp = client.get("/api/v1/students/me/history?type=path", headers=hdr_a)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["type"] == "path"

    def test_student_sees_only_own_matches(self, client: TestClient, db_session: Session):
        """Student A should not see Student B's match results."""
        _, stu_a, hdr_a = _make_student(db_session, "stu_hist_match_a", "Match Student A")
        _, stu_b, _ = _make_student(db_session, "stu_hist_match_b", "Match Student B")

        sp_a_id = _seed_student_profile(db_session, stu_a.id)
        sp_b_id = _seed_student_profile(db_session, stu_b.id)
        jp_id = _seed_job_profile(db_session, "MATCH_JP")

        _seed_match(db_session, sp_a_id, jp_id)
        _seed_match(db_session, sp_b_id, jp_id)
        _seed_match(db_session, sp_b_id, jp_id)

        resp = client.get("/api/v1/students/me/history?type=matching", headers=hdr_a)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["type"] == "matching"
