"""Tests for admin statistics aggregation and timezone normalization (US-025)."""

import pytest
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import create_access_token
from app.models import CareerReport, Student, User
from app.services.auth_service import hash_password


ADMIN_BASE = "/api/v1/admin"


def _auth_headers(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def _make_admin(db: Session, suffix: str) -> tuple[dict, int]:
    user = User(
        username=f"stats_admin_{suffix}",
        password_hash=hash_password("pw123456"),
        full_name=f"Stats Admin {suffix}",
        role="admin",
    )
    db.add(user)
    db.commit()
    return _auth_headers(user.id), user.id


def _make_student(db: Session, suffix: str) -> int:
    user = User(
        username=f"stu_{suffix}",
        password_hash=hash_password("pw123456"),
        full_name=f"Student {suffix}",
        role="student",
    )
    db.add(user)
    db.flush()
    student = Student(user_id=user.id, major="CS", grade="2024")
    db.add(student)
    db.commit()
    return user.id


class TestStatsOverviewAggregation:
    """Verify overview stats match real DB counts."""

    def test_overview_fields_complete(self, client, db_session):
        headers, _ = _make_admin(db_session, "fields")
        resp = client.get(f"{ADMIN_BASE}/stats/overview", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        required = {"total_users", "total_positions", "total_reports", "total_matches", "avg_match_score"}
        assert required.issubset(set(data.keys()))

    def test_overview_counts_are_non_negative(self, client, db_session):
        headers, _ = _make_admin(db_session, "counts")
        resp = client.get(f"{ADMIN_BASE}/stats/overview", headers=headers)
        data = resp.json()["data"]
        for key in ["total_users", "total_positions", "total_reports", "total_matches"]:
            assert data[key] >= 0, f"{key} should be non-negative"
        assert 0 <= data["avg_match_score"] <= 100

    def test_overview_counts_match_db(self, client, db_session):
        headers, _ = _make_admin(db_session, "match")
        resp = client.get(f"{ADMIN_BASE}/stats/overview", headers=headers)
        data = resp.json()["data"]

        db_users = db_session.scalar(select(func.count(User.id))) or 0
        db_reports = db_session.scalar(select(func.count(CareerReport.id))) or 0
        assert data["total_users"] == db_users
        assert data["total_reports"] == db_reports


class TestTimezoneBoundary:
    """Verify timezone conversion in trend queries does not shift same-local-day dates."""

    def test_utc_late_maps_to_next_local_day(self, client, db_session):
        headers, _ = _make_admin(db_session, "tzlate")
        # Create a report at UTC 23:30 — should map to next day in +08:00
        user = User(username="stu_tz_late", password_hash="x", full_name="Stu Late", role="student")
        db_session.add(user)
        db_session.flush()
        student = Student(user_id=user.id, major="CS", grade="2024")
        db_session.add(student)
        db_session.flush()
        report = CareerReport(
            student_id=student.id, target_job_code="DEV",
            status="completed", content_json={},
        )
        report.created_at = datetime(2026, 4, 15, 23, 30, tzinfo=timezone.utc)
        db_session.add(report)
        db_session.commit()

        resp = client.get(f"{ADMIN_BASE}/stats/trends?days=30", headers=headers)
        assert resp.status_code == 200
        trends = resp.json()["data"]
        dates = [t["date"] for t in trends]
        assert "2026-04-16" in dates, f"UTC 23:30 → Shanghai next day, got {dates}"

    def test_utc_early_maps_to_same_local_day(self, client, db_session):
        headers, _ = _make_admin(db_session, "tzearly")
        user = User(username="stu_tz_early", password_hash="x", full_name="Stu Early", role="student")
        db_session.add(user)
        db_session.flush()
        student = Student(user_id=user.id, major="CS", grade="2024")
        db_session.add(student)
        db_session.flush()
        report = CareerReport(
            student_id=student.id, target_job_code="DEV",
            status="completed", content_json={},
        )
        report.created_at = datetime(2026, 4, 15, 1, 0, tzinfo=timezone.utc)
        db_session.add(report)
        db_session.commit()

        resp = client.get(f"{ADMIN_BASE}/stats/trends?days=30", headers=headers)
        trends = resp.json()["data"]
        dates = [t["date"] for t in trends]
        assert "2026-04-15" in dates, f"UTC 01:00 → Shanghai same day, got {dates}"


class TestStatsAuthorization:
    """Verify stats endpoints require admin role."""

    def test_unauthenticated_overview(self, client, db_session):
        resp = client.get(f"{ADMIN_BASE}/stats/overview")
        assert resp.status_code == 401

    def test_student_forbidden_overview(self, client, db_session):
        uid = _make_student(db_session, "forbidden")
        headers = _auth_headers(uid)
        resp = client.get(f"{ADMIN_BASE}/stats/overview", headers=headers)
        assert resp.status_code == 403

    def test_unauthenticated_trends(self, client, db_session):
        resp = client.get(f"{ADMIN_BASE}/stats/trends")
        assert resp.status_code == 401

    def test_unauthenticated_weekly(self, client, db_session):
        resp = client.get(f"{ADMIN_BASE}/stats/weekly")
        assert resp.status_code == 401
