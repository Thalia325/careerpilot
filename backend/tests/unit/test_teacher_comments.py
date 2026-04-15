"""Tests for teacher comment CRUD (US-023)."""
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


def _get_report_id(teacher_client) -> int:
    """Find an existing report ID from seed data."""
    resp = teacher_client.get("/api/v1/teacher/students/reports")
    data = resp.json()["data"]
    for s in data:
        if s["report_status"] != "未开始":
            list_resp = teacher_client.get(f"/api/v1/teacher/students/{s['student_id']}/reports")
            reports = list_resp.json()["data"]
            if reports:
                return reports[0]["report_id"]
    pytest.skip("No reports found")


def test_create_comment(teacher_client):
    """POST creates a new comment on a report."""
    report_id = _get_report_id(teacher_client)
    resp = teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Great+work&priority=high&visible_to_student=true",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["comment"] == "Great work"
    assert data["priority"] == "high"
    assert data["visible_to_student"] is True
    assert "id" in data
    assert data["report_id"] == report_id


def test_list_comments(teacher_client):
    """GET returns comments for a report."""
    report_id = _get_report_id(teacher_client)
    # Create a comment first
    teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Test+comment",
    )
    resp = teacher_client.get(f"/api/v1/teacher/reports/{report_id}/comments")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    for c in data:
        assert "id" in c
        assert "comment" in c
        assert "teacher_name" in c
        assert "priority" in c
        assert "visible_to_student" in c
        assert "created_at" in c


def test_update_comment(teacher_client):
    """PUT updates an existing comment."""
    report_id = _get_report_id(teacher_client)
    create_resp = teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Original",
    )
    comment_id = create_resp.json()["data"]["id"]

    resp = teacher_client.put(
        f"/api/v1/teacher/comments/{comment_id}?comment_text=Updated&priority=urgent",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["comment"] == "Updated"
    assert data["priority"] == "urgent"


def test_delete_comment(teacher_client):
    """DELETE removes a comment."""
    report_id = _get_report_id(teacher_client)
    create_resp = teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=To+delete",
    )
    comment_id = create_resp.json()["data"]["id"]

    resp = teacher_client.delete(f"/api/v1/teacher/comments/{comment_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["deleted"] is True

    # Verify it's gone
    list_resp = teacher_client.get(f"/api/v1/teacher/reports/{report_id}/comments")
    ids = [c["id"] for c in list_resp.json()["data"]]
    assert comment_id not in ids


def test_create_comment_nonexistent_report(teacher_client):
    """POST returns 404 for non-existent report."""
    resp = teacher_client.post(
        "/api/v1/teacher/reports/99999/comments?comment_text=Test",
    )
    assert resp.status_code == 404


def test_update_comment_invalid_priority(teacher_client):
    """PUT returns 400 for invalid priority."""
    report_id = _get_report_id(teacher_client)
    create_resp = teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Test",
    )
    comment_id = create_resp.json()["data"]["id"]

    resp = teacher_client.put(
        f"/api/v1/teacher/comments/{comment_id}?priority=invalid",
    )
    assert resp.status_code == 400


def test_delete_nonexistent_comment(teacher_client):
    """DELETE returns 404 for non-existent comment."""
    resp = teacher_client.delete("/api/v1/teacher/comments/99999")
    assert resp.status_code == 404
