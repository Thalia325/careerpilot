from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.models import User
from app.schemas.report import (
    ReportCheckRequest,
    ReportCheckResponse,
    ReportExportRequest,
    ReportExportResponse,
    ReportGenerateRequest,
    ReportPolishRequest,
    ReportResponse,
)
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    payload: ReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> ReportResponse:
    # Verify user has access
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    result = await container.report_service.generate_report(db, payload.student_id, payload.job_code)
    return ReportResponse(**result)


@router.post("/polish", response_model=ReportResponse)
async def polish_report(
    payload: ReportPolishRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> ReportResponse:
    # Verify user has access
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    result = await container.report_service.polish_report(db, payload.report_id, payload.markdown_content)
    return ReportResponse(**result)


@router.post("/check", response_model=ReportCheckResponse)
def check_report(
    payload: ReportCheckRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> ReportCheckResponse:
    # Verify user has access
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    return ReportCheckResponse(**container.report_service.check_completeness(db, payload.report_id))


@router.post("/export", response_model=ReportExportResponse)
def export_report(
    payload: ReportExportRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> ReportExportResponse:
    # Verify user has access
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    exported = container.report_service.export_report(db, payload.report_id, payload.format)
    return ReportExportResponse(report_id=payload.report_id, exported=exported)

