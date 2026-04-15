"""Tests for US-004: Analysis run context skeleton with binding fields."""

import pytest
from fastapi.testclient import TestClient


def _auth_headers(user_id: int = 1) -> dict:
    return {"Authorization": "Bearer dev-bypass"}


def _upload_file(
    client: TestClient,
    filename: str = "resume.pdf",
    file_type: str = "resume",
    owner_id: int = 1,
) -> int:
    """Upload a file and return its ID."""
    resp = client.post(
        "/api/v1/files/upload",
        files=[("upload", (filename, b"%PDF-1.4 test content", "application/pdf"))],
        data={"owner_id": str(owner_id), "file_type": file_type},
        headers=_auth_headers(owner_id),
    )
    assert resp.status_code == 200, f"Upload failed: {resp.json()}"
    return resp.json()["data"]["id"]


def _start_analysis(
    client: TestClient,
    student_id: int = 1,
    job_code: str = "SE-001",
    file_ids: list[int] | None = None,
    resume_file_id: int | None = None,
) -> dict:
    """Start an analysis run and return the response JSON."""
    payload: dict = {"student_id": student_id, "job_code": job_code}
    if file_ids is not None:
        payload["file_ids"] = file_ids
    if resume_file_id is not None:
        payload["resume_file_id"] = resume_file_id
    resp = client.post("/api/v1/analysis/start", json=payload, headers=_auth_headers())
    assert resp.status_code == 200, f"Start analysis failed: {resp.json()}"
    return resp.json()


def _get_run(client: TestClient, run_id: int) -> dict:
    resp = client.get(f"/api/v1/analysis/{run_id}", headers=_auth_headers())
    assert resp.status_code == 200
    return resp.json()


def _update_context(client: TestClient, run_id: int, **kwargs) -> dict:
    resp = client.patch(f"/api/v1/analysis/{run_id}/context", json=kwargs, headers=_auth_headers())
    assert resp.status_code == 200, f"Context update failed: {resp.json()}"
    return resp.json()


class TestAnalysisRunContextFields:
    """Verify that analysis runs store and return context binding fields."""

    def test_start_stores_uploaded_file_ids(self, client: TestClient, prepare_database):
        file_id = _upload_file(client)
        data = _start_analysis(client, file_ids=[file_id])
        assert data["uploaded_file_ids"] == [file_id]

    def test_start_stores_target_job_code(self, client: TestClient, prepare_database):
        data = _start_analysis(client, job_code="SE-002")
        assert data["target_job_code"] == "SE-002"

    def test_start_with_empty_files(self, client: TestClient, prepare_database):
        data = _start_analysis(client, file_ids=[])
        assert data["uploaded_file_ids"] == []
        assert data["resume_file_id"] is None

    def test_auto_resolve_resume_file_id_from_file_ids(self, client: TestClient, prepare_database):
        """When file_ids include a resume-type file, resume_file_id is auto-resolved."""
        resume_id = _upload_file(client, "resume.pdf", "resume")
        cert_id = _upload_file(client, "cert.pdf", "certificate")
        data = _start_analysis(client, file_ids=[resume_id, cert_id])
        assert data["resume_file_id"] == resume_id

    def test_explicit_resume_file_id_overrides_auto(self, client: TestClient, prepare_database):
        """Explicit resume_file_id takes precedence over auto-resolution."""
        resume_id = _upload_file(client, "resume.pdf", "resume")
        cert_id = _upload_file(client, "cert.pdf", "certificate")
        data = _start_analysis(client, file_ids=[resume_id, cert_id], resume_file_id=cert_id)
        assert data["resume_file_id"] == cert_id

    def test_no_resume_file_when_no_resume_type(self, client: TestClient, prepare_database):
        """If no file has type 'resume', resume_file_id stays None."""
        cert_id = _upload_file(client, "cert.pdf", "certificate")
        data = _start_analysis(client, file_ids=[cert_id])
        assert data["resume_file_id"] is None

    def test_get_run_returns_all_context_fields(self, client: TestClient, prepare_database):
        file_id = _upload_file(client)
        start = _start_analysis(client, file_ids=[file_id], job_code="SE-001")
        run = _get_run(client, start["run_id"])
        # Verify all context fields are present in the response
        assert "uploaded_file_ids" in run
        assert "resume_file_id" in run
        assert "profile_version_id" in run
        assert "target_job_code" in run
        assert "match_result_id" in run
        assert "path_recommendation_id" in run
        assert "report_id" in run


class TestAnalysisRunContextUpdate:
    """Verify PATCH /{run_id}/context links downstream resources."""

    def test_update_profile_version_id(self, client: TestClient, prepare_database):
        start = _start_analysis(client)
        run_id = start["run_id"]
        updated = _update_context(client, run_id, profile_version_id=42)
        assert updated["profile_version_id"] == 42

    def test_update_target_job_code(self, client: TestClient, prepare_database):
        start = _start_analysis(client, job_code="OLD-001")
        run_id = start["run_id"]
        updated = _update_context(client, run_id, target_job_code="NEW-001")
        assert updated["target_job_code"] == "NEW-001"

    def test_update_match_result_id(self, client: TestClient, prepare_database):
        start = _start_analysis(client)
        updated = _update_context(client, start["run_id"], match_result_id=99)
        assert updated["match_result_id"] == 99

    def test_update_path_recommendation_id(self, client: TestClient, prepare_database):
        start = _start_analysis(client)
        updated = _update_context(client, start["run_id"], path_recommendation_id=55)
        assert updated["path_recommendation_id"] == 55

    def test_update_report_id(self, client: TestClient, prepare_database):
        start = _start_analysis(client)
        updated = _update_context(client, start["run_id"], report_id=77)
        assert updated["report_id"] == 77

    def test_partial_update_preserves_other_fields(self, client: TestClient, prepare_database):
        """Updating one field should not clear others."""
        start = _start_analysis(client, job_code="SE-001")
        run_id = start["run_id"]
        _update_context(client, run_id, profile_version_id=10)
        updated = _update_context(client, run_id, match_result_id=20)
        assert updated["profile_version_id"] == 10
        assert updated["match_result_id"] == 20
        assert updated["target_job_code"] == "SE-001"

    def test_update_nonexistent_run_returns_404(self, client: TestClient, prepare_database):
        resp = client.patch(
            "/api/v1/analysis/9999/context",
            json={"profile_version_id": 1},
            headers=_auth_headers(),
        )
        assert resp.status_code == 404


class TestAnalysisRunIsolation:
    """Verify each analysis run is independent with its own context."""

    def test_each_run_gets_unique_id(self, client: TestClient, prepare_database):
        run_a = _start_analysis(client, job_code="A")
        run_b = _start_analysis(client, job_code="B")
        assert run_a["run_id"] != run_b["run_id"]

    def test_context_does_not_leak_between_runs(self, client: TestClient, prepare_database):
        """Two runs for the same student with different file_ids stay isolated."""
        file_a = _upload_file(client, "resume_a.pdf", "resume")
        file_b = _upload_file(client, "resume_b.pdf", "resume")

        run_a = _start_analysis(client, file_ids=[file_a], job_code="SE-001")
        run_b = _start_analysis(client, file_ids=[file_b], job_code="SE-002")

        # Update context for run A only
        _update_context(client, run_a["run_id"], profile_version_id=100)

        state_a = _get_run(client, run_a["run_id"])
        state_b = _get_run(client, run_b["run_id"])

        assert state_a["uploaded_file_ids"] == [file_a]
        assert state_b["uploaded_file_ids"] == [file_b]
        assert state_a["profile_version_id"] == 100
        assert state_b["profile_version_id"] is None
        assert state_a["target_job_code"] == "SE-001"
        assert state_b["target_job_code"] == "SE-002"

    def test_explicit_run_id_overrides_latest(self, client: TestClient, prepare_database):
        """Fetching by explicit run_id returns the correct run, not just the latest."""
        file_1 = _upload_file(client, "old.pdf", "resume")
        file_2 = _upload_file(client, "new.pdf", "resume")

        run_old = _start_analysis(client, file_ids=[file_1], job_code="OLD")
        run_new = _start_analysis(client, file_ids=[file_2], job_code="NEW")

        # Fetch the older run by explicit ID
        state_old = _get_run(client, run_old["run_id"])
        assert state_old["target_job_code"] == "OLD"
        assert state_old["uploaded_file_ids"] == [file_1]
        # Not the latest run's data
        assert state_old["target_job_code"] != "NEW"
