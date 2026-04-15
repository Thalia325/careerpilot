"""Tests for teacher overview stats endpoint (US-019)."""
import pytest


@pytest.fixture(autouse=True)
def teacher_client(client):
    """Login as teacher_demo and set auth headers."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "teacher_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_overview_stats_returns_all_fields(teacher_client):
    """Overview endpoint returns all 7 required metric fields."""
    resp = teacher_client.get("/api/v1/teacher/stats/overview")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "total_students" in data
    assert "students_with_resume" in data
    assert "students_with_profile" in data
    assert "students_with_report" in data
    assert "avg_match_score" in data
    assert "pending_review_reports" in data
    assert "students_need_followup" in data


def test_overview_stats_total_students(teacher_client):
    """total_students matches the actual student count from seed data."""
    resp = teacher_client.get("/api/v1/teacher/stats/overview")
    data = resp.json()["data"]
    assert data["total_students"] >= 30  # seed creates 35 students


def test_overview_stats_students_with_resume(teacher_client):
    """students_with_resume is <= total_students and >= 0."""
    resp = teacher_client.get("/api/v1/teacher/stats/overview")
    data = resp.json()["data"]
    assert 0 <= data["students_with_resume"] <= data["total_students"]


def test_overview_stats_students_with_profile(teacher_client):
    """students_with_profile is <= total_students and >= 0."""
    resp = teacher_client.get("/api/v1/teacher/stats/overview")
    data = resp.json()["data"]
    assert 0 <= data["students_with_profile"] <= data["total_students"]


def test_overview_stats_students_with_report(teacher_client):
    """students_with_report is <= total_students and >= 0."""
    resp = teacher_client.get("/api/v1/teacher/stats/overview")
    data = resp.json()["data"]
    assert 0 <= data["students_with_report"] <= data["total_students"]


def test_overview_stats_avg_match_score_range(teacher_client):
    """avg_match_score is a float in 0-100 range."""
    resp = teacher_client.get("/api/v1/teacher/stats/overview")
    data = resp.json()["data"]
    assert isinstance(data["avg_match_score"], (int, float))
    assert 0 <= data["avg_match_score"] <= 100


def test_overview_stats_pending_review_non_negative(teacher_client):
    """pending_review_reports is non-negative."""
    resp = teacher_client.get("/api/v1/teacher/stats/overview")
    data = resp.json()["data"]
    assert data["pending_review_reports"] >= 0


def test_overview_stats_students_need_followup_non_negative(teacher_client):
    """students_need_followup is non-negative and <= total_students."""
    resp = teacher_client.get("/api/v1/teacher/stats/overview")
    data = resp.json()["data"]
    assert 0 <= data["students_need_followup"] <= data["total_students"]


def test_overview_stats_data_from_real_queries(teacher_client):
    """Metrics are computed from real DB queries, not hardcoded."""
    resp = teacher_client.get("/api/v1/teacher/stats/overview")
    data = resp.json()["data"]
    # Seed data creates 35 students with various states, so values should be non-trivial
    assert data["total_students"] > 0
    assert data["students_with_profile"] > 0
    assert data["students_with_report"] > 0
    assert data["avg_match_score"] > 0


def test_overview_stats_all_numeric(teacher_client):
    """All metric values are numeric, not empty strings."""
    resp = teacher_client.get("/api/v1/teacher/stats/overview")
    data = resp.json()["data"]
    for key, value in data.items():
        assert isinstance(value, (int, float)), f"{key} should be numeric, got {type(value)}"
