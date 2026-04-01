from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.models import User
from app.schemas.scheduler import SchedulerJobCreateRequest, SchedulerJobOut, SchedulerRunResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.get("/jobs", response_model=list[SchedulerJobOut])
def list_scheduler_jobs(
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> list[SchedulerJobOut]:
    # Only admin can list scheduler jobs
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以管理调度任务")

    return [SchedulerJobOut(**item) for item in container.scheduler_service.list_jobs(db)]


@router.post("/jobs", response_model=SchedulerJobOut)
def create_scheduler_job(
    payload: SchedulerJobCreateRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> SchedulerJobOut:
    # Only admin can create scheduler jobs
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以管理调度任务")

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
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> SchedulerRunResponse:
    # Only admin can run scheduler jobs
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以管理调度任务")

    return SchedulerRunResponse(**container.scheduler_service.run_due_jobs(db))

