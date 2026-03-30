from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.models import JobProfile, User
from app.schemas.common import APIResponse, Pagination
from app.schemas.job import JobImportRequest, JobProfileGenerationRequest
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/import", response_model=APIResponse)
async def import_jobs(
    payload: JobImportRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    # Only admin can import jobs
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以导入职位")

    imported = await container.job_import_service.import_rows(db, [row.model_dump() for row in payload.rows])
    return APIResponse(data={"count": len(imported), "job_codes": [item.job_code for item in imported]})


@router.get("", response_model=APIResponse)
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    # Verify user has access
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    query = select(JobProfile).order_by(JobProfile.title)
    total = db.query(JobProfile).count()
    items = list(db.scalars(query.offset(skip).limit(limit)).all())
    return APIResponse(
        data={
            "items": [
                {
                    "job_code": item.job_code,
                    "title": item.title,
                    "skills": item.skill_requirements,
                    "weights": item.dimension_weights,
                }
                for item in items
            ],
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": (skip + limit) < total,
            },
        }
    )


@router.post("/profiles/generate", response_model=APIResponse)
async def generate_job_profiles(
    payload: JobProfileGenerationRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    # Only admin can generate profiles
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以生成职位画像")

    job_codes = payload.job_codes or []
    profiles = await container.job_import_service.generate_profiles(db, job_codes or None)
    return APIResponse(data={"count": len(profiles), "job_codes": [item.job_code for item in profiles]})


@router.get("/profiles/templates", response_model=APIResponse)
def list_templates(
    keyword: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> APIResponse:
    # Verify user has access
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    return APIResponse(data=container.job_import_service.search_templates(keyword))
