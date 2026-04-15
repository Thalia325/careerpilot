from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.api.routers.students import resolve_target_job
from app.models import Student, UploadedFile, User
from app.schemas.report import (
    ReportCheckRequest,
    ReportCheckResponse,
    ReportExportRequest,
    ReportExportResponse,
    ReportGenerateRequest,
    ReportPolishRequest,
    ReportResponse,
    ReportSaveRequest,
)
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> ReportResponse:
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    try:
        report = container.report_service.get_report(db, report_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告不存在")
    if not report.content_json or not report.markdown_content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告尚未生成")

    # Check if source files for this report's profile version have been deleted
    source_files_deleted = False
    if report.profile_version_id:
        from app.models import ProfileVersion
        pv = db.scalar(select(ProfileVersion).where(ProfileVersion.id == report.profile_version_id))
        if pv and pv.uploaded_file_ids:
            existing_count = db.scalar(
                select(func.count(UploadedFile.id)).where(UploadedFile.id.in_(pv.uploaded_file_ids))
            )
            if existing_count < len(pv.uploaded_file_ids):
                source_files_deleted = True

    from sqlalchemy import func
    return ReportResponse(
        report_id=report.id,
        student_id=report.student_id,
        job_code=report.target_job_code,
        content=report.content_json,
        markdown_content=report.markdown_content,
        status=report.status,
        path_recommendation_id=report.path_recommendation_id,
        profile_version_id=report.profile_version_id,
        match_result_id=report.match_result_id,
        analysis_run_id=report.analysis_run_id,
        source_files_deleted=source_files_deleted,
    )


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

    job_code = payload.job_code
    if not job_code:
        student = db.scalar(select(Student).where(Student.user_id == current_user.id))
        if student:
            job_code, _ = resolve_target_job(db, student)
    if not job_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法确定目标岗位，请先选择或确认一个目标岗位")

    try:
        result = await container.report_service.generate_report(
            db, payload.student_id, job_code,
            analysis_run_id=payload.analysis_run_id,
            profile_version_id=payload.profile_version_id,
            match_result_id=payload.match_result_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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

    try:
        exported = container.report_service.export_report(db, payload.report_id, payload.format)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ReportExportResponse(report_id=payload.report_id, exported=exported)


@router.post("/save")
def save_report(
    payload: ReportSaveRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
):
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    try:
        container.report_service.save_report(db, payload.report_id, payload.markdown_content)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告不存在，请先生成报告")

    report = container.report_service.get_report(db, payload.report_id)
    return {
        "report_id": report.id,
        "status": report.status,
        "markdown_content": report.markdown_content,
    }
