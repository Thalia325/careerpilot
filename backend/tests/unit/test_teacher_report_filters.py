"""Tests for teacher report list filtering (US-020)."""
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


def test_report_list_has_new_fields(teacher_client):
    """Report list items include last_analysis_time and followup_status."""
    resp = teacher_client.get("/api/v1/teacher/students/reports")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) > 0
    for item in data:
        assert "last_analysis_time" in item
        assert "followup_status" in item
        assert "major" in item
        assert "grade" in item


def test_filter_by_major(teacher_client):
    """Filtering by major returns only matching students."""
    resp_all = teacher_client.get("/api/v1/teacher/students/reports")
    all_data = resp_all.json()["data"]
    if not all_data:
        pytest.skip("No student data")
    majors = list({s["major"] for s in all_data if s["major"]})
    if not majors:
        pytest.skip("No major data")
    target_major = majors[0]

    resp = teacher_client.get(f"/api/v1/teacher/students/reports?major={target_major}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) > 0
    for item in data:
        assert item["major"] == target_major


def test_filter_by_grade(teacher_client):
    """Filtering by grade returns only matching students."""
    resp_all = teacher_client.get("/api/v1/teacher/students/reports")
    all_data = resp_all.json()["data"]
    grades = list({s["grade"] for s in all_data if s["grade"]})
    if not grades:
        pytest.skip("No grade data")
    target_grade = grades[0]

    resp = teacher_client.get(f"/api/v1/teacher/students/reports?grade={target_grade}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) > 0
    for item in data:
        assert item["grade"] == target_grade


def test_filter_by_report_status(teacher_client):
    """Filtering by report_status returns only matching students."""
    resp_all = teacher_client.get("/api/v1/teacher/students/reports")
    all_data = resp_all.json()["data"]
    statuses = list({s["report_status"] for s in all_data if s["report_status"]})
    if not statuses:
        pytest.skip("No report status data")
    target_status = statuses[0]

    resp = teacher_client.get(f"/api/v1/teacher/students/reports?report_status={target_status}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    for item in data:
        assert item["report_status"] == target_status


def test_filter_by_score_range(teacher_client):
    """Filtering by score_min and score_max returns only students in range."""
    # Use score range that avoids exact boundary matches from seed data
    resp = teacher_client.get("/api/v1/teacher/students/reports?score_min=65&score_max=75")
    assert resp.status_code == 200
    data = resp.json()["data"]
    for item in data:
        assert 65 <= item["match_score"] <= 75


def test_filter_by_target_job(teacher_client):
    """Filtering by target_job returns only matching students."""
    resp_all = teacher_client.get("/api/v1/teacher/students/reports")
    all_data = resp_all.json()["data"]
    jobs = list({s["target_job"] for s in all_data if s["target_job"]})
    if not jobs:
        pytest.skip("No target job data")
    target_job = jobs[0]

    resp = teacher_client.get(f"/api/v1/teacher/students/reports?target_job={target_job}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    for item in data:
        assert item["target_job"] == target_job or item["career_goal"] == target_job


def test_combined_filters(teacher_client):
    """Multiple filters applied together narrow results correctly."""
    resp_all = teacher_client.get("/api/v1/teacher/students/reports")
    all_data = resp_all.json()["data"]
    majors = list({s["major"] for s in all_data if s["major"]})
    if not majors:
        pytest.skip("No major data")

    resp = teacher_client.get(f"/api/v1/teacher/students/reports?major={majors[0]}&score_min=60&score_max=90")
    assert resp.status_code == 200
    data = resp.json()["data"]
    for item in data:
        assert item["major"] == majors[0]
        assert 60 <= item["match_score"] < 90


def test_no_filters_returns_all(teacher_client):
    """Without filters, all students are returned."""
    resp = teacher_client.get("/api/v1/teacher/students/reports")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 30  # seed data creates 35 students


def test_followup_status_values(teacher_client):
    """Followup status is one of expected values."""
    resp = teacher_client.get("/api/v1/teacher/students/reports")
    data = resp.json()["data"]
    valid_statuses = {"无", "待跟进", "跟进中", "已完成", "已逾期"}
    for item in data:
        assert item["followup_status"] in valid_statuses


def test_match_distribution_has_five_ranges(teacher_client):
    """Match distribution returns exactly 5 score ranges."""
    resp = teacher_client.get("/api/v1/teacher/stats/match-distribution")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 5
    labels = [d["name"] for d in data]
    assert "90分以上" in labels
    assert "80-89分" in labels
    assert "70-79分" in labels
    assert "60-69分" in labels
    assert "60分以下" in labels
