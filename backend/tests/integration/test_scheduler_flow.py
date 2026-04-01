from datetime import datetime, timedelta

from sqlalchemy import select

from app.models import SchedulerJob


def test_scheduler_trigger_followup_records(client, db_session):
    create_response = client.post(
        "/api/v1/scheduler/jobs",
        json={
            "job_name": "integration_due_job",
            "cron_expr": "0 9 * * 1",
            "job_type": "reminder",
            "payload": {"student_id": 1, "target_job": "前端开发工程师"}
        },
    )
    assert create_response.status_code == 200
    job = db_session.scalar(select(SchedulerJob).where(SchedulerJob.job_name == "integration_due_job"))
    job.next_run_at = datetime.utcnow() - timedelta(minutes=5)
    db_session.commit()

    run_response = client.post("/api/v1/scheduler/run-due")
    assert run_response.status_code == 200
    data = run_response.json()
    assert "integration_due_job" in data["executed_jobs"]
    assert data["generated_records"]

