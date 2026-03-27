from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_db_session
from app.schemas.scheduler import SchedulerJobCreateRequest, SchedulerJobOut, SchedulerRunResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.get("/jobs", response_model=list[SchedulerJobOut])
def list_scheduler_jobs(
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> list[SchedulerJobOut]:
    return [SchedulerJobOut(**item) for item in container.scheduler_service.list_jobs(db)]


@router.post("/jobs", response_model=SchedulerJobOut)
def create_scheduler_job(
    payload: SchedulerJobCreateRequest,
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> SchedulerJobOut:
    job = container.scheduler_service.create_job(
        db,
        job_name=payload.job_name,
        cron_expr=payload.cron_expr,
        job_type=payload.job_type,
        payload=payload.payload,
    )
    return SchedulerJobOut(**job)


@router.post("/run-due", response_model=SchedulerRunResponse)
def run_due_jobs(
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> SchedulerRunResponse:
    return SchedulerRunResponse(**container.scheduler_service.run_due_jobs(db))

