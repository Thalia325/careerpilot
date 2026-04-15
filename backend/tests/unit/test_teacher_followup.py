"""Tests for teacher followup status update (US-022)."""
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


def test_update_followup_status(teacher_client):
    """PATCH followup updates GrowthTask status."""
    # Use first student
    resp = teacher_client.patch(
        "/api/v1/teacher/students/1/followup?status_value=read",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["student_id"] == 1
    assert data["status"] == "read"
    assert data["updated"] is True


def test_update_followup_with_notes(teacher_client):
    """PATCH followup with teacher notes creates FollowupRecord."""
    resp = teacher_client.patch(
        "/api/v1/teacher/students/1/followup?status_value=communicated&teacher_notes=Test+note",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["updated"] is True


def test_update_followup_with_date(teacher_client):
    """PATCH followup with next_followup_date sets deadline."""
    resp = teacher_client.patch(
        "/api/v1/teacher/students/1/followup?status_value=in_progress&next_followup_date=2026-05-01",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["deadline"] is not None


def test_update_followup_invalid_status(teacher_client):
    """PATCH followup with invalid status returns 400."""
    resp = teacher_client.patch(
        "/api/v1/teacher/students/1/followup?status_value=invalid_status",
    )
    assert resp.status_code == 400


def test_update_followup_nonexistent_student(teacher_client):
    """PATCH followup for non-existent student returns 404."""
    resp = teacher_client.patch(
        "/api/v1/teacher/students/99999/followup?status_value=read",
    )
    assert resp.status_code == 404


def test_update_followup_all_valid_statuses(teacher_client):
    """All valid followup statuses are accepted."""
    valid = ["pending", "in_progress", "completed", "overdue", "read", "communicated", "review"]
    for s in valid:
        resp = teacher_client.patch(
            f"/api/v1/teacher/students/2/followup?status_value={s}",
        )
        assert resp.status_code == 200, f"Status {s} should be accepted"
