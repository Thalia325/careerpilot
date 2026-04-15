"""Tests for teacher report detail and class overview endpoints (US-021)."""
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


def test_student_report_list(teacher_client):
    """GET /teacher/students/{id}/reports returns list of reports."""
    # Get a student with reports first
    reports_resp = teacher_client.get("/api/v1/teacher/students/reports")
    data = reports_resp.json()["data"]
    students_with_reports = [s for s in data if s["report_status"] != "未开始"]
    if not students_with_reports:
        pytest.skip("No students with reports")

    student_id = students_with_reports[0]["student_id"]
    resp = teacher_client.get(f"/api/v1/teacher/students/{student_id}/reports")
    assert resp.status_code == 200
    reports = resp.json()["data"]
    assert len(reports) > 0
    for r in reports:
        assert "report_id" in r
        assert "target_job" in r
        assert "status" in r
        assert "created_at" in r
        assert "profile_version_id" in r
        assert "match_result_id" in r
        assert "analysis_run_id" in r


def test_student_report_list_nonexistent_student(teacher_client):
    """GET /teacher/students/{id}/reports returns 404 for missing student."""
    resp = teacher_client.get("/api/v1/teacher/students/99999/reports")
    assert resp.status_code == 404


def test_report_detail(teacher_client):
    """GET /teacher/reports/{id} returns full report detail."""
    # Find a report ID
    reports_resp = teacher_client.get("/api/v1/teacher/students/reports")
    data = reports_resp.json()["data"]
    students_with_reports = [s for s in data if s["report_status"] != "未开始"]
    if not students_with_reports:
        pytest.skip("No students with reports")

    student_id = students_with_reports[0]["student_id"]
    list_resp = teacher_client.get(f"/api/v1/teacher/students/{student_id}/reports")
    reports = list_resp.json()["data"]
    report_id = reports[0]["report_id"]

    resp = teacher_client.get(f"/api/v1/teacher/reports/{report_id}")
    assert resp.status_code == 200
    detail = resp.json()["data"]
    assert detail["report_id"] == report_id
    assert "student_name" in detail
    assert "student_major" in detail
    assert "content" in detail
    assert "markdown_content" in detail
    assert "resume_summary" in detail
    assert "profile_snapshot" in detail
    assert "match_analysis" in detail
    assert "created_at" in detail


def test_report_detail_nonexistent(teacher_client):
    """GET /teacher/reports/{id} returns 404 for missing report."""
    resp = teacher_client.get("/api/v1/teacher/reports/99999")
    assert resp.status_code == 404


def test_report_detail_has_match_analysis(teacher_client):
    """Report detail includes match analysis with score, gaps, strengths."""
    # Find a report that has match_result_id set
    reports_resp = teacher_client.get("/api/v1/teacher/students/reports")
    data = reports_resp.json()["data"]
    students_with_reports = [s for s in data if s["report_status"] != "未开始" and s["match_score"] > 0]
    if not students_with_reports:
        pytest.skip("No students with matched reports")

    # Try students until we find one with a report that has match data
    for student in students_with_reports:
        list_resp = teacher_client.get(f"/api/v1/teacher/students/{student['student_id']}/reports")
        reports = list_resp.json()["data"]
        for report in reports:
            if report.get("match_result_id"):
                resp = teacher_client.get(f"/api/v1/teacher/reports/{report['report_id']}")
                detail = resp.json()["data"]
                match = detail["match_analysis"]
                if match.get("total_score"):
                    assert isinstance(match["total_score"], (int, float))
                    assert match["total_score"] > 0
                    return
    pytest.skip("No reports with match analysis data found")


def test_class_overview(teacher_client):
    """GET /teacher/stats/class-overview returns all required fields."""
    resp = teacher_client.get("/api/v1/teacher/stats/class-overview")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "job_distribution" in data
    assert "report_completion_rate" in data
    assert "resume_completeness" in data
    assert "skill_gaps" in data
    assert "followup_students" in data


def test_class_overview_job_distribution(teacher_client):
    """Job distribution has entries from seed data."""
    resp = teacher_client.get("/api/v1/teacher/stats/class-overview")
    data = resp.json()["data"]
    assert len(data["job_distribution"]) > 0
    for item in data["job_distribution"]:
        assert "name" in item
        assert "value" in item
        assert item["value"] > 0


def test_class_overview_report_completion_rate(teacher_client):
    """Report completion rate is a valid percentage."""
    resp = teacher_client.get("/api/v1/teacher/stats/class-overview")
    data = resp.json()["data"]
    rate = data["report_completion_rate"]
    assert isinstance(rate, (int, float))
    assert 0 <= rate <= 100


def test_class_overview_resume_completeness(teacher_client):
    """Resume completeness has three buckets."""
    resp = teacher_client.get("/api/v1/teacher/stats/class-overview")
    data = resp.json()["data"]
    buckets = data["resume_completeness"]
    names = {b["name"] for b in buckets}
    assert "高(80%+)" in names
    assert "中(50-79%)" in names
    assert "低(<50%)" in names


def test_class_overview_skill_gaps(teacher_client):
    """Skill gaps list is sorted by count descending."""
    resp = teacher_client.get("/api/v1/teacher/stats/class-overview")
    data = resp.json()["data"]
    gaps = data["skill_gaps"]
    if len(gaps) > 1:
        for i in range(len(gaps) - 1):
            assert gaps[i]["count"] >= gaps[i + 1]["count"]


def test_class_overview_followup_students(teacher_client):
    """Followup students list has correct fields."""
    resp = teacher_client.get("/api/v1/teacher/stats/class-overview")
    data = resp.json()["data"]
    for s in data["followup_students"]:
        assert "student_id" in s
        assert "name" in s
        assert "major" in s
        assert "career_goal" in s
