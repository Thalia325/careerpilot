"""Tests for teacher permission boundary based on binding (US-025)."""
import pytest


@pytest.fixture(autouse=True)
def admin_client(client):
    """Admin sees all data."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_admin_sees_all_students(admin_client):
    """Admin can see all students regardless of binding."""
    resp = admin_client.get("/api/v1/teacher/students/reports")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 30  # seed data has 35 students


def test_admin_sees_all_match_distribution(admin_client):
    """Admin sees match distribution for all students."""
    resp = admin_client.get("/api/v1/teacher/stats/match-distribution")
    assert resp.status_code == 200
    data = resp.json()["data"]
    total = sum(d["count"] for d in data)
    assert total > 0


def test_admin_sees_all_major_distribution(admin_client):
    """Admin sees major distribution for all students."""
    resp = admin_client.get("/api/v1/teacher/stats/major-distribution")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 5


def test_admin_sees_all_advice(admin_client):
    """Admin sees advice for all students."""
    resp = admin_client.get("/api/v1/teacher/advice")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 30


def test_admin_sees_class_overview(admin_client):
    """Admin sees full class overview."""
    resp = admin_client.get("/api/v1/teacher/stats/class-overview")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "job_distribution" in data
    assert "skill_gaps" in data


def test_unbound_teacher_sees_filtered_data(client):
    """Teacher without bindings sees no students (or filtered list)."""
    # Register a fresh teacher with no bindings
    resp = client.post("/api/v1/auth/register", json={
        "username": "unbound_teacher",
        "password": "test123",
        "full_name": "Unbound Teacher",
        "role": "teacher",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    reports_resp = client.get("/api/v1/teacher/students/reports")
    assert reports_resp.status_code == 200
    # Unbound teacher should see 0 students
    data = reports_resp.json()["data"]
    assert len(data) == 0


def test_student_role_cannot_access_teacher_endpoints(client):
    """Student role is rejected from teacher endpoints."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "student_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    reports_resp = client.get("/api/v1/teacher/students/reports")
    assert reports_resp.status_code == 403

    stats_resp = client.get("/api/v1/teacher/stats/overview")
    assert stats_resp.status_code == 403

    advice_resp = client.get("/api/v1/teacher/advice")
    assert advice_resp.status_code == 403
