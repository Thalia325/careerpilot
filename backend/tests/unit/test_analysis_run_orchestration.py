"""US-005: Analysis run orchestration tests.

Verify the analysis pipeline runs under a single tracked run with:
- Ordered step progression (uploaded → parsed → profiled → matched → pathed → reported)
- Successful run with step-level status output
- Failed run with failed stage and error message
- Run isolation (artifacts from one run don't leak into another)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import create_access_token
from app.models import AnalysisRun, Student, User
from app.services.auth_service import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STEPS = ("uploaded", "parsed", "profiled", "matched", "pathed", "reported")


def _make_student(db: Session, username: str) -> tuple[User, Student, dict]:
    user = User(
        username=username,
        password_hash=hash_password("test123"),
        role="student",
        full_name=username,
        email=f"{username}@test.local",
    )
    db.add(user)
    db.flush()
    student = Student(user_id=user.id, major="软件工程", grade="大三")
    db.add(student)
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    return user, student, headers


def _start_run(client: TestClient, student_id: int, headers: dict, **kwargs) -> dict:
    payload = {"student_id": student_id, "job_code": "SE-001", **kwargs}
    resp = client.post("/api/v1/analysis/start", json=payload, headers=headers)
    assert resp.status_code == 200, f"Start failed: {resp.json()}"
    return resp.json()


def _mark_running(client: TestClient, run_id: int, step: str, headers: dict) -> dict:
    resp = client.post(f"/api/v1/analysis/{run_id}/step/{step}/running", headers=headers)
    assert resp.status_code == 200
    return resp.json()


def _mark_complete(client: TestClient, run_id: int, step: str, headers: dict) -> dict:
    resp = client.post(f"/api/v1/analysis/{run_id}/step/{step}/complete", headers=headers)
    assert resp.status_code == 200
    return resp.json()


def _mark_failed(client: TestClient, run_id: int, step: str, headers: dict, error: str = "OCR 解析失败") -> dict:
    resp = client.post(
        f"/api/v1/analysis/{run_id}/step/{step}/fail",
        json={"error_detail": error},
        headers=headers,
    )
    assert resp.status_code == 200
    return resp.json()


def _get_state(client: TestClient, run_id: int, headers: dict) -> dict:
    resp = client.get(f"/api/v1/analysis/{run_id}", headers=headers)
    assert resp.status_code == 200
    return resp.json()


# ---------------------------------------------------------------------------
# Tests: Successful full run
# ---------------------------------------------------------------------------


class TestSuccessfulRun:
    """Verify a full analysis run progresses through all steps to completion."""

    def test_full_successful_run(self, client: TestClient, db_session: Session):
        """Start a run, complete each step in order, mark analysis complete."""
        _, student, headers = _make_student(db_session, "stu_run_ok")
        run = _start_run(client, student.id, headers)

        run_id = run["run_id"]
        assert run["status"] == "pending"
        assert run["ordered_steps"] == list(STEPS)

        # Progress through all steps: running → complete for each
        for step in STEPS:
            state = _mark_running(client, run_id, step, headers)
            assert state["status"] == "running"
            assert state["current_step"] == step

            state = _mark_complete(client, run_id, step, headers)
            assert state["step_results"][step] is True
            assert state["current_step"] == step

        # Mark analysis complete
        state = _mark_complete(client, run_id, "reported", headers)
        # Verify all steps are marked complete
        for step in STEPS:
            assert state["step_results"].get(step) is True, f"Step {step} not marked complete"

    def test_successful_run_context_binding(self, client: TestClient, db_session: Session):
        """Run tracks context fields for downstream artifacts."""
        _, student, headers = _make_student(db_session, "stu_run_ctx")
        run = _start_run(client, student.id, headers, job_code="SE-002")
        run_id = run["run_id"]

        # Simulate binding downstream results via context update
        resp = client.patch(
            f"/api/v1/analysis/{run_id}/context",
            json={
                "profile_version_id": 10,
                "match_result_id": 20,
                "path_recommendation_id": 30,
                "report_id": 40,
            },
            headers=headers,
        )
        assert resp.status_code == 200
        state = resp.json()
        assert state["profile_version_id"] == 10
        assert state["match_result_id"] == 20
        assert state["path_recommendation_id"] == 30
        assert state["report_id"] == 40
        assert state["target_job_code"] == "SE-002"

    def test_ordered_steps_in_all_responses(self, client: TestClient, db_session: Session):
        """Every response includes the ordered_steps list."""
        _, student, headers = _make_student(db_session, "stu_run_steps")
        run = _start_run(client, student.id, headers)
        run_id = run["run_id"]

        # start response
        assert run["ordered_steps"] == list(STEPS)

        # state response
        state = _get_state(client, run_id, headers)
        assert state["ordered_steps"] == list(STEPS)

        # step update response
        state = _mark_running(client, run_id, "uploaded", headers)
        assert state["ordered_steps"] == list(STEPS)

        state = _mark_complete(client, run_id, "uploaded", headers)
        assert state["ordered_steps"] == list(STEPS)


# ---------------------------------------------------------------------------
# Tests: Failed run
# ---------------------------------------------------------------------------


class TestFailedRun:
    """Verify a failed step records the stage and error message."""

    def test_failed_step_records_stage_and_error(self, client: TestClient, db_session: Session):
        """Failing the 'parsed' step records failed_step and error_detail."""
        _, student, headers = _make_student(db_session, "stu_run_fail")
        run = _start_run(client, student.id, headers)
        run_id = run["run_id"]

        # Complete first step, then fail the second
        _mark_complete(client, run_id, "uploaded", headers)
        _mark_running(client, run_id, "parsed", headers)

        error_msg = "OCR 解析超时，请检查文件格式"
        state = _mark_failed(client, run_id, "parsed", headers, error=error_msg)

        assert state["status"] == "failed"
        assert state["failed_step"] == "parsed"
        assert state["error_detail"] == error_msg
        assert state["current_step"] == "parsed"

    def test_failed_step_preserves_completed_steps(self, client: TestClient, db_session: Session):
        """Completed steps remain recorded even after a subsequent failure."""
        _, student, headers = _make_student(db_session, "stu_run_fail2")
        run = _start_run(client, student.id, headers)
        run_id = run["run_id"]

        _mark_complete(client, run_id, "uploaded", headers)
        _mark_complete(client, run_id, "parsed", headers)
        _mark_complete(client, run_id, "profiled", headers)
        _mark_running(client, run_id, "matched", headers)
        _mark_failed(client, run_id, "matched", headers, error="匹配服务不可用")

        state = _get_state(client, run_id, headers)
        assert state["step_results"]["uploaded"] is True
        assert state["step_results"]["parsed"] is True
        assert state["step_results"]["profiled"] is True
        assert state["status"] == "failed"
        assert state["failed_step"] == "matched"

    def test_reset_after_failure_clears_error(self, client: TestClient, db_session: Session):
        """Resetting a failed run clears failed_step and error_detail."""
        _, student, headers = _make_student(db_session, "stu_run_reset")
        run = _start_run(client, student.id, headers)
        run_id = run["run_id"]

        _mark_failed(client, run_id, "uploaded", headers, error="上传失败")
        assert _get_state(client, run_id, headers)["status"] == "failed"

        # Reset
        resp = client.post(f"/api/v1/analysis/{run_id}/reset", headers=headers)
        assert resp.status_code == 200
        state = resp.json()
        assert state["status"] == "pending"
        assert state["failed_step"] == ""
        assert state["error_detail"] == ""
        assert state["step_results"] == {}


# ---------------------------------------------------------------------------
# Tests: Run isolation
# ---------------------------------------------------------------------------


class TestRunIsolation:
    """Verify result queries return only artifacts from the same run."""

    def test_two_runs_return_different_artifacts(self, client: TestClient, db_session: Session):
        """Two runs for the same student have independent context."""
        _, student, headers = _make_student(db_session, "stu_run_iso")
        run_a = _start_run(client, student.id, headers, job_code="A-001")
        run_b = _start_run(client, student.id, headers, job_code="B-001")

        # Bind different artifacts to each run
        client.patch(
            f"/api/v1/analysis/{run_a['run_id']}/context",
            json={"report_id": 100, "match_result_id": 200},
            headers=headers,
        )
        client.patch(
            f"/api/v1/analysis/{run_b['run_id']}/context",
            json={"report_id": 300, "match_result_id": 400},
            headers=headers,
        )

        state_a = _get_state(client, run_a["run_id"], headers)
        state_b = _get_state(client, run_b["run_id"], headers)

        assert state_a["report_id"] == 100
        assert state_a["match_result_id"] == 200
        assert state_a["target_job_code"] == "A-001"

        assert state_b["report_id"] == 300
        assert state_b["match_result_id"] == 400
        assert state_b["target_job_code"] == "B-001"

    def test_invalid_step_rejected(self, client: TestClient, db_session: Session):
        """An invalid step key returns 400."""
        _, student, headers = _make_student(db_session, "stu_run_badstep")
        run = _start_run(client, student.id, headers)

        resp = client.post(
            f"/api/v1/analysis/{run['run_id']}/step/invalid_step/running",
            headers=headers,
        )
        assert resp.status_code == 400
