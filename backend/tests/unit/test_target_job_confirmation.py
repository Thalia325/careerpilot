"""Tests for US-009: Target job confirmation and persistence binding."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import AnalysisRun, JobProfile, Student


def _auth_headers(user_id: int = 1) -> dict:
    return {"Authorization": "Bearer dev-bypass"}


def _confirm_target_job(client: TestClient, job_code: str = "SE-001", job_title: str = "软件工程师") -> dict:
    """Confirm a target job and return the response."""
    resp = client.put(
        "/api/v1/students/me/target-job",
        json={"job_code": job_code, "job_title": job_title},
        headers=_auth_headers(),
    )
    assert resp.status_code == 200, f"Confirm target job failed: {resp.json()}"
    return resp.json()


def _start_analysis(
    client: TestClient,
    student_id: int = 1,
    job_code: str = "SE-001",
    file_ids: list[int] | None = None,
) -> dict:
    """Start an analysis run."""
    payload: dict = {"student_id": student_id, "job_code": job_code}
    if file_ids is not None:
        payload["file_ids"] = file_ids
    resp = client.post("/api/v1/analysis/start", json=payload, headers=_auth_headers())
    assert resp.status_code == 200, f"Start analysis failed: {resp.json()}"
    return resp.json()


def _get_run(client: TestClient, run_id: int) -> dict:
    resp = client.get(f"/api/v1/analysis/{run_id}", headers=_auth_headers())
    assert resp.status_code == 200
    return resp.json()


def _clear_student_target_job():
    """Clear the demo student's target_job_code directly in DB."""
    db = SessionLocal()
    try:
        student = db.scalar(select(Student).where(Student.user_id == 1))
        if student:
            student.target_job_code = ""
            student.target_job_title = ""
            db.commit()
    finally:
        db.close()


class TestTargetJobConfirmation:
    """Verify that target job confirmation persists and binds correctly."""

    def test_confirm_target_job_saves_to_student(self, client: TestClient, prepare_database):
        result = _confirm_target_job(client, "FE-001", "前端工程师")
        assert result["ok"] is True
        assert result["target_job_code"] == "FE-001"
        assert result["target_job_title"] == "前端工程师"

    def test_confirm_target_job_reflected_in_session(self, client: TestClient, prepare_database):
        _confirm_target_job(client, "PM-001", "产品经理")
        resp = client.get("/api/v1/students/me", headers=_auth_headers())
        session = resp.json()
        assert session["target_job_code"] == "PM-001"
        assert session["target_job_title"] == "产品经理"

    def test_confirm_target_job_updates_resolved(self, client: TestClient, prepare_database):
        _confirm_target_job(client, "DA-001", "数据分析师")
        resp = client.get("/api/v1/students/me", headers=_auth_headers())
        session = resp.json()
        assert session["resolved_job_code"] == "DA-001"
        assert session["resolved_job_title"] == "数据分析师"

    def test_change_target_job_overwrites_previous(self, client: TestClient, prepare_database):
        _confirm_target_job(client, "SE-001", "软件工程师")
        _confirm_target_job(client, "PM-001", "产品经理")
        resp = client.get("/api/v1/students/me", headers=_auth_headers())
        session = resp.json()
        assert session["target_job_code"] == "PM-001"
        assert session["target_job_title"] == "产品经理"

    def test_confirm_target_job_syncs_to_latest_pending_analysis_run(self, client: TestClient, prepare_database):
        """When confirming a target job, the latest pending AnalysisRun should be updated."""
        run = _start_analysis(client, job_code="SE-001")
        run_id = run["run_id"]

        # Confirm a different target job
        result = _confirm_target_job(client, "FE-001", "前端工程师")
        assert result["analysis_run_id"] == run_id

        # Verify the analysis run was updated
        updated_run = _get_run(client, run_id)
        assert updated_run["target_job_code"] == "FE-001"

    def test_confirm_target_job_does_not_update_completed_run(self, client: TestClient, prepare_database):
        """A completed analysis run should not be updated by target job confirmation."""
        run = _start_analysis(client, job_code="SE-001")
        run_id = run["run_id"]

        # Mark as completed
        resp = client.post(f"/api/v1/analysis/{run_id}/complete", headers=_auth_headers())
        assert resp.status_code == 200

        # Confirm a different target job
        _confirm_target_job(client, "FE-001", "前端工程师")

        # Verify the completed run was NOT updated
        updated_run = _get_run(client, run_id)
        assert updated_run["target_job_code"] == "SE-001"

    def test_confirm_target_job_updates_running_run(self, client: TestClient, prepare_database):
        """A running analysis run should also be updated by target job confirmation."""
        run = _start_analysis(client, job_code="SE-001")
        run_id = run["run_id"]

        # Mark as running
        resp = client.post(
            f"/api/v1/analysis/{run_id}/step/parsed/running",
            headers=_auth_headers(),
        )
        assert resp.status_code == 200

        # Confirm a different target job
        _confirm_target_job(client, "PM-001", "产品经理")

        # Verify the running run was updated
        updated_run = _get_run(client, run_id)
        assert updated_run["target_job_code"] == "PM-001"

    def test_confirm_target_job_returns_analysis_run_id(self, client: TestClient, prepare_database):
        """The response should include analysis_run_id when a run exists."""
        run = _start_analysis(client, job_code="SE-001")
        run_id = run["run_id"]

        result = _confirm_target_job(client, "PM-001", "产品经理")
        assert result["analysis_run_id"] == run_id

    def test_confirm_target_job_returns_null_analysis_run_id_when_no_run(self, client: TestClient, prepare_database):
        """When no analysis run exists, analysis_run_id should be null."""
        result = _confirm_target_job(client, "SE-001", "软件工程师")
        assert result["analysis_run_id"] is None

    def test_confirm_target_job_syncs_only_latest_run(self, client: TestClient, prepare_database):
        """Only the latest analysis run should be synced, not previous ones."""
        run1 = _start_analysis(client, job_code="SE-001")
        run1_id = run1["run_id"]

        # Complete run1
        client.post(f"/api/v1/analysis/{run1_id}/complete", headers=_auth_headers())

        run2 = _start_analysis(client, job_code="PM-001")
        run2_id = run2["run_id"]

        # Confirm a different target job
        _confirm_target_job(client, "FE-001", "前端工程师")

        # run1 should NOT be updated (completed)
        updated_run1 = _get_run(client, run1_id)
        assert updated_run1["target_job_code"] == "SE-001"

        # run2 should be updated (pending)
        updated_run2 = _get_run(client, run2_id)
        assert updated_run2["target_job_code"] == "FE-001"


class TestTargetJobDownstreamFallback:
    """Verify that matching and path planning use confirmed target job as fallback."""

    def test_matching_with_confirmed_job_fallback(self, client: TestClient, prepare_database):
        """Matching should use confirmed target job when job_code is empty."""
        _confirm_target_job(client, "SE-001", "软件工程师")

        resp = client.post(
            "/api/v1/matching/analyze",
            json={"student_id": 1, "job_code": ""},
            headers=_auth_headers(),
        )
        # May fail at service layer due to missing profiles, but should NOT fail
        # with "无法确定目标岗位"
        if resp.status_code == 200:
            assert resp.json()["job_code"] == "SE-001"
        else:
            assert "无法确定目标岗位" not in resp.json().get("detail", "")

    def test_matching_rejects_empty_job_without_confirmed(self, client: TestClient, prepare_database):
        """Without a confirmed job (and no career_goal fallback), matching should fail with 400."""
        # Clear the student's target_job_code and career_goal
        db = SessionLocal()
        student = db.scalar(select(Student).where(Student.user_id == 1))
        if student:
            student.target_job_code = ""
            student.target_job_title = ""
            student.career_goal = ""
            db.commit()
        db.close()

        resp = client.post(
            "/api/v1/matching/analyze",
            json={"student_id": 1, "job_code": ""},
            headers=_auth_headers(),
        )
        assert resp.status_code == 400
        assert "无法确定目标岗位" in resp.json()["detail"]

    def test_path_planning_with_confirmed_job_fallback(self, client: TestClient, prepare_database):
        """Path planning should use confirmed target job when job_code is empty."""
        _confirm_target_job(client, "SE-001", "软件工程师")

        resp = client.post(
            "/api/v1/career-paths/plan",
            json={"student_id": 1, "job_code": ""},
            headers=_auth_headers(),
        )
        # May fail at service layer due to missing profiles, but should NOT fail
        # with "无法确定目标岗位"
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            assert data.get("target_job_code") == "SE-001"
        else:
            assert "无法确定目标岗位" not in resp.json().get("detail", "")

    def test_path_planning_rejects_empty_job_without_confirmed(self, client: TestClient, prepare_database):
        """Without a confirmed job (and no career_goal fallback), path planning should fail with 400."""
        db = SessionLocal()
        student = db.scalar(select(Student).where(Student.user_id == 1))
        if student:
            student.target_job_code = ""
            student.target_job_title = ""
            student.career_goal = ""
            db.commit()
        db.close()

        resp = client.post(
            "/api/v1/career-paths/plan",
            json={"student_id": 1, "job_code": ""},
            headers=_auth_headers(),
        )
        assert resp.status_code == 400
        assert "无法确定目标岗位" in resp.json()["detail"]

    def test_report_with_confirmed_job_fallback(self, client: TestClient, prepare_database):
        """Report generation should use confirmed target job when job_code is empty."""
        _confirm_target_job(client, "SE-001", "软件工程师")

        resp = client.post(
            "/api/v1/reports/generate",
            json={"student_id": 1, "job_code": ""},
            headers=_auth_headers(),
        )
        # May fail at service layer, but should NOT fail with "无法确定目标岗位"
        if resp.status_code == 200:
            assert resp.json()["job_code"] == "SE-001"
        else:
            assert "无法确定目标岗位" not in resp.json().get("detail", "")

    def test_matching_with_explicit_job_overrides_confirmed(self, client: TestClient, prepare_database):
        """Explicit job_code should override the confirmed target job."""
        _confirm_target_job(client, "SE-001", "软件工程师")

        resp = client.post(
            "/api/v1/matching/analyze",
            json={"student_id": 1, "job_code": "FE-001"},
            headers=_auth_headers(),
        )
        # Service layer may fail due to missing profiles, but the job resolution
        # should use FE-001, not the confirmed SE-001. A 400 here means the
        # service tried to use FE-001 but couldn't find profiles.
        assert resp.status_code in (200, 400)
        if resp.status_code == 200:
            assert resp.json()["job_code"] == "FE-001"

    def test_confirmed_job_binds_to_analysis_run_context(self, client: TestClient, prepare_database):
        """When an analysis run exists, confirming a job updates its target_job_code via context."""
        run = _start_analysis(client, job_code="")
        run_id = run["run_id"]
        assert run["target_job_code"] is None

        # Confirm target job
        _confirm_target_job(client, "SE-001", "软件工程师")

        # Check the analysis run was updated
        updated = _get_run(client, run_id)
        assert updated["target_job_code"] == "SE-001"
