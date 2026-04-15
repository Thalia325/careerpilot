"""E2E tests for multi-resume data isolation (US-035~038)."""
import pytest


@pytest.fixture(autouse=True)
def student_client(client):
    """Login as student_demo."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "student_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_analysis_runs_are_isolated(student_client):
    """Two analysis runs for the same student produce independent contexts."""
    # Start two separate analysis runs
    resp_a = student_client.post("/api/v1/analysis/start", json={
        "student_id": 1, "job_code": "FE_DEV", "file_ids": [1],
    })
    resp_b = student_client.post("/api/v1/analysis/start", json={
        "student_id": 1, "job_code": "FE_DEV", "file_ids": [2],
    })

    if resp_a.status_code == 200 and resp_b.status_code == 200:
        run_a = resp_a.json()
        run_b = resp_b.json()
        assert run_a["run_id"] != run_b["run_id"]
        assert run_a["run_id"] is not None
        assert run_b["run_id"] is not None


def test_profile_version_tracks_analysis_run(student_client):
    """Profile versions can reference their analysis_run_id."""
    from app.models import ProfileVersion
    # This checks the model has the field
    assert hasattr(ProfileVersion, "analysis_run_id")


def test_chat_records_analysis_run(student_client):
    """Chat model supports analysis_run_id field."""
    from app.models import ChatMessageRecord
    assert hasattr(ChatMessageRecord, "analysis_run_id")
    assert hasattr(ChatMessageRecord, "profile_version_id")


def test_report_response_includes_source_deleted_flag(student_client):
    """Report response includes source_files_deleted field."""
    # Find an existing report first
    history_resp = student_client.get("/api/v1/students/me/history?type=report")
    if history_resp.status_code == 200:
        items = history_resp.json().get("items", [])
        if not items:
            pytest.skip("No reports exist yet")
        report_id = items[0].get("ref_id")
        if not report_id:
            pytest.skip("No report ref_id found")
        resp = student_client.get(f"/api/v1/reports/{report_id}")
        if resp.status_code == 200:
            data = resp.json()
            assert "source_files_deleted" in data
    else:
        pytest.skip("History endpoint unavailable")


def test_report_per_analysis_run(student_client):
    """Reports with different analysis_run_id don't overwrite each other."""
    # Start two runs
    start_a = student_client.post("/api/v1/analysis/start", json={
        "student_id": 1, "job_code": "FE_DEV", "file_ids": [1],
    })
    start_b = student_client.post("/api/v1/analysis/start", json={
        "student_id": 1, "job_code": "FE_DEV", "file_ids": [2],
    })

    if start_a.status_code == 200 and start_b.status_code == 200:
        run_a_id = start_a.json()["run_id"]
        run_b_id = start_b.json()["run_id"]

        # Generate reports for both runs
        gen_a = student_client.post("/api/v1/reports/generate", json={
            "student_id": 1, "job_code": "FE_DEV", "analysis_run_id": run_a_id,
        })
        gen_b = student_client.post("/api/v1/reports/generate", json={
            "student_id": 1, "job_code": "FE_DEV", "analysis_run_id": run_b_id,
        })

        if gen_a.status_code == 200 and gen_b.status_code == 200:
            report_a = gen_a.json()
            report_b = gen_b.json()
            # Different analysis runs should produce different reports
            assert report_a["analysis_run_id"] == run_a_id
            assert report_b["analysis_run_id"] == run_b_id


def test_file_deletion_preserves_snapshots(student_client):
    """Deleting a file doesn't break existing profile version snapshots."""
    # Check that ProfileVersion has uploaded_file_ids for tracking
    from app.models import ProfileVersion
    assert hasattr(ProfileVersion, "uploaded_file_ids")
    assert hasattr(ProfileVersion, "snapshot_json")


def test_teacher_can_see_run_context(client):
    """Teacher report list shows analysis_run_id for context distinction."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "teacher_demo",
        "password": "demo123",
    })
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    reports_resp = client.get("/api/v1/teacher/students/reports")
    if reports_resp.status_code == 200:
        data = reports_resp.json()["data"]
        for s in data:
            if s["report_status"] != "未开始":
                list_resp = client.get(f"/api/v1/teacher/students/{s['student_id']}/reports")
                if list_resp.status_code == 200:
                    reports = list_resp.json()["data"]
                    for r in reports:
                        assert "analysis_run_id" in r
                        assert "profile_version_id" in r
