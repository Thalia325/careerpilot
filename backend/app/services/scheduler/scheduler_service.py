from __future__ import annotations

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FollowupRecord, SchedulerJob


class SchedulerService:
    def __init__(self, timezone: str) -> None:
        self.timezone = ZoneInfo(timezone)

    def _compute_next_run(self, cron_expr: str, from_time: Optional[datetime] = None) -> Optional[datetime]:
        from_time = from_time or datetime.now(self.timezone)
        try:
            trigger = CronTrigger.from_crontab(cron_expr, timezone=self.timezone)
            return trigger.get_next_fire_time(None, from_time)
        except Exception:
            return from_time

    def create_job(self, db: Session, job_name: str, cron_expr: str, job_type: str, payload: dict) -> dict:
        job = db.scalar(select(SchedulerJob).where(SchedulerJob.job_name == job_name))
        if not job:
            job = SchedulerJob(job_name=job_name, cron_expr=cron_expr, job_type=job_type, payload_json=payload)
            db.add(job)
            db.flush()
        job.cron_expr = cron_expr
        job.job_type = job_type
        job.payload_json = payload
        job.status = "active"
        job.next_run_at = self._compute_next_run(cron_expr)
        db.commit()
        return self.serialize(job)

    def list_jobs(self, db: Session) -> list[dict]:
        jobs = list(db.scalars(select(SchedulerJob).order_by(SchedulerJob.created_at.desc())).all())
        return [self.serialize(job) for job in jobs]

    def serialize(self, job: SchedulerJob) -> dict:
        return {
            "id": job.id,
            "job_name": job.job_name,
            "cron_expr": job.cron_expr,
            "status": job.status,
            "job_type": job.job_type,
            "payload": job.payload_json,
            "next_run_at": job.next_run_at,
            "last_run_at": job.last_run_at,
        }

    def run_due_jobs(self, db: Session) -> dict:
        now = datetime.now(self.timezone)
        jobs = list(
            db.scalars(
                select(SchedulerJob).where(SchedulerJob.enabled.is_(True)).where(SchedulerJob.status == "active")
            ).all()
        )
        executed_jobs: list[str] = []
        generated_records: list[dict] = []
        for job in jobs:
            if job.next_run_at and job.next_run_at.replace(tzinfo=self.timezone) > now:
                continue
            content = self._generate_followup_content(job)
            record = FollowupRecord(
                student_id=job.payload_json.get("student_id", 1),
                task_id=job.payload_json.get("task_id"),
                record_type=job.job_type,
                content=content,
                meta_json=job.payload_json,
            )
            db.add(record)
            executed_jobs.append(job.job_name)
            generated_records.append({"job_name": job.job_name, "content": content})
            job.last_run_at = now
            job.next_run_at = self._compute_next_run(job.cron_expr, now)
        db.commit()
        return {"executed_jobs": executed_jobs, "generated_records": generated_records}

    @staticmethod
    def _generate_followup_content(job: SchedulerJob) -> str:
        job_type = job.job_type
        target_job = job.payload_json.get("target_job", "目标岗位")
        if job_type == "resource_push":
            return f"已为 {target_job} 推送学习资源与岗位资讯。"
        if job_type == "review":
            return f"已触发 {target_job} 阶段复盘，请更新任务完成情况与画像。"
        return f"已生成 {target_job} 成长提醒，请按计划完成本阶段任务。"
