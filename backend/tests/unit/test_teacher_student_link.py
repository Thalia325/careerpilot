"""Tests for teacher-student link CRUD (US-024)."""
import pytest


@pytest.fixture(autouse=True)
def admin_client(client):
    """Login as admin_demo user."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin_demo",
        "password": "demo123",
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_list_links_empty(admin_client):
    """GET returns list (may be empty initially)."""
    resp = admin_client.get("/api/v1/admin/teacher-student-links")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert "total" in data


def test_create_link(admin_client):
    """POST creates a new teacher-student link."""
    resp = admin_client.post(
        "/api/v1/admin/teacher-student-links?teacher_id=1&student_id=1&group_name=ClassA&source=manual",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["teacher_id"] == 1
    assert data["student_id"] == 1
    assert "id" in data


def test_create_duplicate_link_fails(admin_client):
    """POST rejects duplicate active links."""
    admin_client.post("/api/v1/admin/teacher-student-links?teacher_id=1&student_id=2")
    resp = admin_client.post("/api/v1/admin/teacher-student-links?teacher_id=1&student_id=2")
    assert resp.status_code == 400


def test_update_link(admin_client):
    """PUT updates link fields."""
    create_resp = admin_client.post(
        "/api/v1/admin/teacher-student-links?teacher_id=1&student_id=3&group_name=OldGroup",
    )
    link_id = create_resp.json()["data"]["id"]

    resp = admin_client.put(
        f"/api/v1/admin/teacher-student-links/{link_id}?group_name=NewGroup&is_primary=false",
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["updated"] is True


def test_delete_link(admin_client):
    """DELETE removes a link."""
    create_resp = admin_client.post(
        "/api/v1/admin/teacher-student-links?teacher_id=1&student_id=4",
    )
    link_id = create_resp.json()["data"]["id"]

    resp = admin_client.delete(f"/api/v1/admin/teacher-student-links/{link_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["deleted"] is True


def test_batch_import(admin_client):
    """POST batch imports multiple links."""
    resp = admin_client.post(
        "/api/v1/admin/teacher-student-links/import",
        json=[
            {"teacher_id": 1, "student_id": 5, "group_name": "Batch1"},
            {"teacher_id": 1, "student_id": 6, "group_name": "Batch1"},
        ],
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["created"] >= 0


def test_delete_nonexistent_link(admin_client):
    """DELETE returns 404 for missing link."""
    resp = admin_client.delete("/api/v1/admin/teacher-student-links/99999")
    assert resp.status_code == 404
