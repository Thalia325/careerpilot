from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class SchedulerJobCreateRequest(BaseModel):
    job_name: str
    cron_expr: str
    job_type: str
    payload: dict[str, Any]


class SchedulerJobOut(BaseModel):
    id: Optional[int] = None
    job_name: str
    cron_expr: str
    status: str
    job_type: str
    payload: dict[str, Any]
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None


class SchedulerRunResponse(BaseModel):
    executed_jobs: list[str]
    generated_records: list[dict[str, Any]]
