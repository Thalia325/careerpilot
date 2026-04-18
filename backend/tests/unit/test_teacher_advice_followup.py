"""Tests for teacher advice and follow-up backend (US-017)."""
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


def _get_student_demo_report_id(client) -> tuple[int, int]:
    """Get a report for a seed student bound to teacher_demo.

    Returns (report_id, student_id) for a seed student that has a report.
    """
    # Login as teacher
    resp = client.post("/api/v1/auth/login", json={
        "username": "teacher_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    # Find a seed student with a report
    resp = client.get("/api/v1/teacher/students/reports")
    data = resp.json()["data"]
    for s in data:
        if s["report_status"] != "未开始":
            list_resp = client.get(f"/api/v1/teacher/students/{s['student_id']}/reports")
            reports = list_resp.json()["data"]
            if reports:
                return reports[0]["report_id"], s["student_id"]
    pytest.skip("No reports found for bound students")


# --- Create advice with follow-up fields ---


def test_create_advice_with_followup_fields(teacher_client):
    """POST creates advice with follow_up_status and next_follow_up_date."""
    report_id = _get_report_id(teacher_client)
    resp = teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments"
        f"?comment_text=Good+progress&visible_to_student=true"
        f"&follow_up_status=pending&next_follow_up_date=2026-05-15",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["comment"] == "Good progress"
    assert data["visible_to_student"] is True
    assert data["follow_up_status"] == "pending"
    assert data["next_follow_up_date"] is not None
    assert "2026-05-15" in data["next_follow_up_date"]


def test_create_advice_without_followup_fields(teacher_client):
    """POST creates advice without follow-up fields (backward compatible)."""
    report_id = _get_report_id(teacher_client)
    resp = teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Simple+comment",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["comment"] == "Simple comment"
    assert data["follow_up_status"] is None
    assert data["next_follow_up_date"] is None


def test_create_advice_invalid_followup_status(teacher_client):
    """POST returns 400 for invalid follow_up_status."""
    report_id = _get_report_id(teacher_client)
    resp = teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments"
        f"?comment_text=Test&follow_up_status=invalid_status",
    )
    assert resp.status_code == 400


def test_create_advice_all_valid_followup_statuses(teacher_client):
    """POST accepts all valid follow_up_status values."""
    report_id = _get_report_id(teacher_client)
    valid = ["pending", "in_progress", "completed", "overdue", "read", "communicated", "review"]
    for s in valid:
        resp = teacher_client.post(
            f"/api/v1/teacher/reports/{report_id}/comments"
            f"?comment_text=Status+{s}&follow_up_status={s}",
        )
        assert resp.status_code == 200, f"follow_up_status={s} should be accepted"
        assert resp.json()["data"]["follow_up_status"] == s


# --- Update advice follow-up state ---


def test_update_advice_followup_status(teacher_client):
    """PUT updates follow_up_status on existing advice."""
    report_id = _get_report_id(teacher_client)
    create_resp = teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments"
        f"?comment_text=Original&follow_up_status=pending",
    )
    comment_id = create_resp.json()["data"]["id"]

    resp = teacher_client.put(
        f"/api/v1/teacher/comments/{comment_id}?follow_up_status=in_progress",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["follow_up_status"] == "in_progress"


def test_update_advice_followup_date(teacher_client):
    """PUT updates next_follow_up_date on existing advice."""
    report_id = _get_report_id(teacher_client)
    create_resp = teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Date+test",
    )
    comment_id = create_resp.json()["data"]["id"]

    resp = teacher_client.put(
        f"/api/v1/teacher/comments/{comment_id}?next_follow_up_date=2026-06-01",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["next_follow_up_date"] is not None
    assert "2026-06-01" in data["next_follow_up_date"]


def test_update_advice_invalid_followup_status(teacher_client):
    """PUT returns 400 for invalid follow_up_status."""
    report_id = _get_report_id(teacher_client)
    create_resp = teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Test",
    )
    comment_id = create_resp.json()["data"]["id"]

    resp = teacher_client.put(
        f"/api/v1/teacher/comments/{comment_id}?follow_up_status=bad_status",
    )
    assert resp.status_code == 400


def test_update_advice_followup_status_transition(teacher_client):
    """PUT can transition follow_up_status from pending to completed."""
    report_id = _get_report_id(teacher_client)
    create_resp = teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments"
        f"?comment_text=Transition+test&follow_up_status=pending&next_follow_up_date=2026-07-01",
    )
    comment_id = create_resp.json()["data"]["id"]
    assert create_resp.json()["data"]["follow_up_status"] == "pending"

    resp = teacher_client.put(
        f"/api/v1/teacher/comments/{comment_id}?follow_up_status=completed",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["follow_up_status"] == "completed"
    assert data["next_follow_up_date"] is not None  # date unchanged


# --- List comments include follow-up fields ---


def test_list_comments_includes_followup_fields(teacher_client):
    """GET comments includes follow_up_status and next_follow_up_date."""
    report_id = _get_report_id(teacher_client)
    teacher_client.post(
        f"/api/v1/teacher/reports/{report_id}/comments"
        f"?comment_text=List+test&follow_up_status=review&next_follow_up_date=2026-08-01",
    )

    resp = teacher_client.get(f"/api/v1/teacher/reports/{report_id}/comments")
    assert resp.status_code == 200
    items = resp.json()["data"]
    found = [i for i in items if i["comment"] == "List test"]
    assert len(found) >= 1
    item = found[0]
    assert item["follow_up_status"] == "review"
    assert item["next_follow_up_date"] is not None
    assert "2026-08-01" in item["next_follow_up_date"]


# --- Student-facing queries filter hidden advice ---


def test_student_views_visible_advice_with_followup(client):
    """Student sees visible advice with follow_up_status and next_follow_up_date."""
    report_id, student_id = _get_student_demo_report_id(client)

    # Already logged in as teacher from _get_student_demo_report_id
    create_resp = client.post(
        f"/api/v1/teacher/reports/{report_id}/comments"
        f"?comment_text=Visible+advice&visible_to_student=true"
        f"&follow_up_status=communicated&next_follow_up_date=2026-09-01",
    )
    assert create_resp.status_code == 200, f"Create failed: {create_resp.status_code} {create_resp.text}"

    # Find the seed student's username (format: demo_student_NNN)
    from sqlalchemy import select
    from app.db.session import SessionLocal
    from app.models import User, Student
    db = SessionLocal()
    try:
        student = db.scalar(select(Student).where(Student.id == student_id))
        user = db.scalar(select(User).where(User.id == student.user_id)) if student else None
        student_username = user.username if user else None
    finally:
        db.close()

    assert student_username, f"Could not find username for student_id={student_id}"

    # Login as the seed student
    resp = client.post("/api/v1/auth/login", json={
        "username": student_username,
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    feedback_resp = client.get("/api/v1/students/me/teacher-feedback")
    assert feedback_resp.status_code == 200, f"Feedback failed: {feedback_resp.status_code} {feedback_resp.text}"
    items = feedback_resp.json()["items"]
    found = [i for i in items if i["comment"] == "Visible advice"]
    assert len(found) >= 1, f"No visible advice found. Items: {[i['comment'] for i in items]}"
    item = found[0]
    assert item["follow_up_status"] == "communicated"
    assert item["next_follow_up_date"] is not None
    assert "2026-09-01" in item["next_follow_up_date"]


def test_student_cannot_see_hidden_advice(client):
    """Student does NOT see advice with visible_to_student=false."""
    report_id, student_id = _get_student_demo_report_id(client)

    # Already logged in as teacher from _get_student_demo_report_id
    client.post(
        f"/api/v1/teacher/reports/{report_id}/comments"
        f"?comment_text=Hidden+advice&visible_to_student=false&follow_up_status=pending",
    )

    # Find the seed student's username
    from sqlalchemy import select
    from app.db.session import SessionLocal
    from app.models import User, Student
    db = SessionLocal()
    try:
        student = db.scalar(select(Student).where(Student.id == student_id))
        user = db.scalar(select(User).where(User.id == student.user_id)) if student else None
        student_username = user.username if user else None
    finally:
        db.close()

    assert student_username, f"Could not find username for student_id={student_id}"

    # Login as the seed student
    resp = client.post("/api/v1/auth/login", json={
        "username": student_username,
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    feedback_resp = client.get("/api/v1/students/me/teacher-feedback")
    items = feedback_resp.json()["items"]
    comments = [i["comment"] for i in items]
    assert "Hidden advice" not in comments


# --- Authorization: teacher can only create/update for bound students ---


def test_create_advice_unbound_student_rejected(client):
    """Teacher cannot create advice for a student not in their class."""
    # Register a new teacher (no bound students)
    client.post("/api/v1/auth/register", json={
        "username": "teacher_advice_test",
        "password": "test123456",
        "role": "teacher",
        "full_name": "Test Teacher",
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "teacher_advice_test",
        "password": "test123456",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    # Get a report via teacher_demo
    resp = client.post("/api/v1/auth/login", json={
        "username": "teacher_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    report_id = _get_report_id(client)

    # Switch back to unbound teacher
    resp = client.post("/api/v1/auth/login", json={
        "username": "teacher_advice_test",
        "password": "test123456",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    resp = client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Unauthorized",
    )
    assert resp.status_code == 403


def test_update_advice_unbound_student_rejected(client):
    """Teacher cannot update advice for a student not in their class."""
    # teacher_demo creates a comment
    resp = client.post("/api/v1/auth/login", json={
        "username": "teacher_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    report_id = _get_report_id(client)
    create_resp = client.post(
        f"/api/v1/teacher/reports/{report_id}/comments?comment_text=Bound+comment",
    )
    comment_id = create_resp.json()["data"]["id"]

    # Register a new teacher (no bound students)
    client.post("/api/v1/auth/register", json={
        "username": "teacher_advice_test2",
        "password": "test123456",
        "role": "teacher",
        "full_name": "Test Teacher 2",
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "teacher_advice_test2",
        "password": "test123456",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    resp = client.put(
        f"/api/v1/teacher/comments/{comment_id}?follow_up_status=completed",
    )
    assert resp.status_code == 403
