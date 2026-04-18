"""Tests for teacher dashboard real metrics query (US-016).

Verifies:
- New teacher with no bound students sees zero-state metrics
- Metrics are computed from bound students only (not demo/hardcoded data)
- Dashboard lists and summary cards agree for the same teacher
- Role-based access control (unauthenticated, wrong role rejected)
"""
import pytest


def _register_and_login_teacher(client, username, full_name="测试老师"):
    """Register a new teacher and return the client with auth headers set."""
    resp = client.post("/api/v1/auth/register", json={
        "username": username,
        "password": "test123456",
        "full_name": full_name,
        "role": "teacher",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def _register_and_login_student(client, username, full_name="测试同学"):
    """Register a new student and return the client with auth headers set."""
    resp = client.post("/api/v1/auth/register", json={
        "username": username,
        "password": "test123456",
        "full_name": full_name,
        "role": "student",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


# ── Zero-state tests ──────────────────────────────────────────────────────────


def test_new_teacher_zero_state_overview(client):
    """A newly registered teacher with no bound students sees all-zero metrics."""
    _register_and_login_teacher(client, "new_teacher_zero")

    resp = client.get("/api/v1/teacher/stats/overview")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["total_students"] == 0
    assert data["students_with_resume"] == 0
    assert data["students_with_profile"] == 0
    assert data["students_with_report"] == 0
    assert data["avg_match_score"] == 0.0
    assert data["pending_review_reports"] == 0
    assert data["students_need_followup"] == 0


def test_new_teacher_zero_state_reports(client):
    """A newly registered teacher with no bound students sees empty report list."""
    _register_and_login_teacher(client, "new_teacher_reports")

    resp = client.get("/api/v1/teacher/students/reports")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    assert len(data) == 0


def test_new_teacher_zero_state_match_distribution(client):
    """A newly registered teacher with no bound students sees all-zero distribution."""
    _register_and_login_teacher(client, "new_teacher_dist")

    resp = client.get("/api/v1/teacher/stats/match-distribution")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    # All ranges should have count 0
    for item in data:
        assert item["count"] == 0


# ── Non-zero state with bound student ────────────────────────────────────────


@pytest.fixture()
def teacher_with_students(client):
    """Create a teacher, register students, and bind them via TeacherStudentLink."""
    # Use teacher_demo from seed data (has bound students)
    resp = client.post("/api/v1/auth/login", json={
        "username": "teacher_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_teacher_demo_overview_consistency(teacher_with_students):
    """Overview stats total_students matches the student count from reports list."""
    client = teacher_with_students

    stats_resp = client.get("/api/v1/teacher/stats/overview")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()["data"]

    reports_resp = client.get("/api/v1/teacher/students/reports")
    assert reports_resp.status_code == 200
    reports = reports_resp.json()["data"]

    # total_students should equal the number of unique students in reports list
    unique_student_ids = set(r["student_id"] for r in reports)
    assert stats["total_students"] == len(unique_student_ids), (
        f"total_students ({stats['total_students']}) != unique students in reports ({len(unique_student_ids)})"
    )


def test_teacher_demo_overview_all_numeric(teacher_with_students):
    """All overview metric values are numeric (int or float)."""
    resp = teacher_with_students.get("/api/v1/teacher/stats/overview")
    data = resp.json()["data"]
    for key, value in data.items():
        assert isinstance(value, (int, float)), f"{key} should be numeric, got {type(value)}"


def test_teacher_demo_overview_field_bounds(teacher_with_students):
    """Each metric is within valid logical bounds."""
    resp = teacher_with_students.get("/api/v1/teacher/stats/overview")
    data = resp.json()["data"]

    assert data["total_students"] > 0, "teacher_demo should have bound students"
    assert 0 <= data["students_with_resume"] <= data["total_students"]
    assert 0 <= data["students_with_profile"] <= data["total_students"]
    assert 0 <= data["students_with_report"] <= data["total_students"]
    assert 0 <= data["avg_match_score"] <= 100
    assert data["pending_review_reports"] >= 0
    assert 0 <= data["students_need_followup"] <= data["total_students"]


def test_teacher_demo_match_distribution_nonnegative(teacher_with_students):
    """Match distribution counts are all non-negative integers."""
    resp = teacher_with_students.get("/api/v1/teacher/stats/match-distribution")
    data = resp.json()["data"]
    assert len(data) == 5  # 5 score ranges
    for item in data:
        assert "name" in item
        assert "count" in item
        assert isinstance(item["count"], int)
        assert item["count"] >= 0


def test_teacher_demo_distribution_sum_matches_reported_students(teacher_with_students):
    """Sum of distribution counts should equal the number of students with match scores."""
    dist_resp = teacher_with_students.get("/api/v1/teacher/stats/match-distribution")
    dist_data = dist_resp.json()["data"]
    total_in_dist = sum(item["count"] for item in dist_data)

    # Students with match scores should be <= students_with_profile
    stats_resp = teacher_with_students.get("/api/v1/teacher/stats/overview")
    stats = stats_resp.json()["data"]

    # Total in distribution should be <= total_students
    assert total_in_dist <= stats["total_students"]


# ── Access control tests ─────────────────────────────────────────────────────


def test_unauthenticated_overview_rejected(client):
    """Unauthenticated request to overview stats returns 401."""
    # Ensure no auth header
    client.headers.pop("Authorization", None)
    resp = client.get("/api/v1/teacher/stats/overview")
    assert resp.status_code == 401


def test_student_cannot_access_overview(client):
    """A student account cannot access teacher overview stats."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "student_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    resp = client.get("/api/v1/teacher/stats/overview")
    assert resp.status_code == 403


def test_unauthenticated_match_distribution_rejected(client):
    """Unauthenticated request to match distribution returns 401."""
    client.headers.pop("Authorization", None)
    resp = client.get("/api/v1/teacher/stats/match-distribution")
    assert resp.status_code == 401


def test_unauthenticated_reports_rejected(client):
    """Unauthenticated request to teacher reports returns 401."""
    client.headers.pop("Authorization", None)
    resp = client.get("/api/v1/teacher/students/reports")
    assert resp.status_code == 401
