from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_db_session
from app.schemas.common import APIResponse
from app.schemas.job import JobImportRequest, JobProfileGenerationRequest
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/import", response_model=APIResponse)
async def import_jobs(
    payload: JobImportRequest,
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    imported = await container.job_import_service.import_rows(db, [row.model_dump() for row in payload.rows])
    return APIResponse(data={"count": len(imported), "job_codes": [item.job_code for item in imported]})


@router.get("", response_model=APIResponse)
def list_jobs(
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    items = container.job_import_service.list_job_profiles(db)
    return APIResponse(
        data=[
            {
                "job_code": item.job_code,
                "title": item.title,
                "skills": item.skill_requirements,
                "weights": item.dimension_weights,
            }
            for item in items
        ]
    )


@router.post("/profiles/generate", response_model=APIResponse)
async def generate_job_profiles(
    payload: JobProfileGenerationRequest,
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    job_codes = payload.job_codes or []
    profiles = await container.job_import_service.generate_profiles(db, job_codes or None)
    return APIResponse(data={"count": len(profiles), "job_codes": [item.job_code for item in profiles]})


@router.get("/profiles/templates", response_model=APIResponse)
def list_templates(
    keyword: Optional[str] = None,
    container: ServiceContainer = Depends(get_container),
) -> APIResponse:
    return APIResponse(data=container.job_import_service.search_templates(keyword))
