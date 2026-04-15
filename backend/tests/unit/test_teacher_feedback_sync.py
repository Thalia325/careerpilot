"""Tests for teacher feedback sync and student read status (US-026)."""
import pytest


@pytest.fixture(autouse=True)
def teacher_client(client):
    """Login as teacher_demo."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "teacher_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def _get_report_id(teacher_client) -> int:
    resp = teacher_client.get("/api/v1/teacher/students/reports")
    data = resp.json()["data"]
    for s in data:
        if s["report_status"] != "未开始":
            list_resp = teacher_client.get(f"/api/v1/teacher/students/{s['student_id']}/reports")
            reports = list_resp.json()["data"]
            if reports:
                return reports[0]["report_id"]
    pytest.skip("No reports found")


def test_student_can_view_feedback(client, teacher_client):
    """Student sees teacher comments marked as visible_to_student."""
    report_id = _get_report_id(teacher_client)
    # Create a visible comment
    teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Student+visible+comment&visible_to_student=true",
    )

    # Student login
    resp = client.post("/api/v1/auth/login", json={
        "username": "student_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    feedback_resp = client.get("/api/v1/students/me/teacher-feedback")
    assert feedback_resp.status_code == 200
    items = feedback_resp.json()["items"]
    assert len(items) >= 1
    # At least one item has our comment
    comments = [i["comment"] for i in items]
    assert "Student visible comment" in comments


def test_student_cannot_see_hidden_feedback(client, teacher_client):
    """Student does NOT see comments with visible_to_student=false."""
    report_id = _get_report_id(teacher_client)
    teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Hidden+comment&visible_to_student=false",
    )

    resp = client.post("/api/v1/auth/login", json={
        "username": "student_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    feedback_resp = client.get("/api/v1/students/me/teacher-feedback")
    items = feedback_resp.json()["items"]
    comments = [i["comment"] for i in items]
    assert "Hidden comment" not in comments


def test_student_mark_feedback_read(client, teacher_client):
    """Student marks feedback as read and gets read_at timestamp."""
    report_id = _get_report_id(teacher_client)
    create_resp = teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Read+test&visible_to_student=true",
    )
    comment_id = create_resp.json()["data"]["id"]

    resp = client.post("/api/v1/auth/login", json={
        "username": "student_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    read_resp = client.post(f"/api/v1/students/me/teacher-feedback/{comment_id}/read")
    assert read_resp.status_code == 200
    assert read_resp.json()["ok"] is True
    assert read_resp.json()["read_at"] is not None


def test_feedback_item_has_correct_fields(client, teacher_client):
    """Feedback items include teacher_name, comment, priority, created_at."""
    report_id = _get_report_id(teacher_client)
    teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Field+test&priority=high&visible_to_student=true",
    )

    resp = client.post("/api/v1/auth/login", json={
        "username": "student_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    feedback_resp = client.get("/api/v1/students/me/teacher-feedback")
    items = feedback_resp.json()["items"]
    field_test = [i for i in items if i["comment"] == "Field test"]
    assert len(field_test) >= 1
    item = field_test[0]
    assert "teacher_name" in item
    assert item["priority"] == "high"
    assert "created_at" in item
