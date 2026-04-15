from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models import AnalysisRun, Student, UploadedFile, User

router = APIRouter()

VALID_STEPS = ("uploaded", "parsed", "profiled", "matched", "reported")


class AnalysisStartRequest(BaseModel):
    student_id: int
    job_code: str = ""
    file_ids: list[int] = []
    resume_file_id: int | None = None


class AnalysisStartResponse(BaseModel):
    run_id: int
    status: str
    current_step: str
    step_results: dict[str, Any]
    uploaded_file_ids: list[int]
    resume_file_id: int | None
    target_job_code: str | None


class AnalysisStepUpdateRequest(BaseModel):
    error_detail: str = ""


class AnalysisStateResponse(BaseModel):
    run_id: int
    status: str
    current_step: str
    failed_step: str
    error_detail: str
    step_results: dict[str, Any]
    uploaded_file_ids: list[int]
    resume_file_id: int | None
    profile_version_id: int | None
    target_job_code: str | None
    match_result_id: int | None
    path_recommendation_id: int | None
    report_id: int | None


class AnalysisContextUpdateRequest(BaseModel):
    profile_version_id: int | None = None
    target_job_code: str | None = None
    match_result_id: int | None = None
    path_recommendation_id: int | None = None
    report_id: int | None = None


def _run_to_state(run: AnalysisRun) -> AnalysisStateResponse:
    return AnalysisStateResponse(
        run_id=run.id,
        status=run.status,
        current_step=run.current_step,
        failed_step=run.failed_step,
        error_detail=run.error_detail,
        step_results=run.step_results,
        uploaded_file_ids=run.uploaded_file_ids or [],
        resume_file_id=run.resume_file_id,
        profile_version_id=run.profile_version_id,
        target_job_code=run.target_job_code,
        match_result_id=run.match_result_id,
        path_recommendation_id=run.path_recommendation_id,
        report_id=run.report_id,
    )


def _resolve_resume_file_id(
    db: Session, file_ids: list[int], explicit_resume_id: int | None
) -> int | None:
    """Resolve the resume file from file_ids. Use explicit if given, else find first resume-type file."""
    if explicit_resume_id:
        return explicit_resume_id
    if not file_ids:
        return None
    for fid in file_ids:
        f = db.get(UploadedFile, fid)
        if f and f.file_type == "resume":
            return fid
    return None


@router.post("/start", response_model=AnalysisStartResponse)
def start_analysis(
    payload: AnalysisStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> AnalysisStartResponse:
    if current_user.role not in ("student", "admin", "teacher"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    resume_file_id = _resolve_resume_file_id(db, payload.file_ids, payload.resume_file_id)

    run = AnalysisRun(
        student_id=payload.student_id,
        status="pending",
        current_step="",
        step_results={},
        uploaded_file_ids=payload.file_ids,
        resume_file_id=resume_file_id,
        target_job_code=payload.job_code or None,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return AnalysisStartResponse(
        run_id=run.id,
        status=run.status,
        current_step=run.current_step,
        step_results=run.step_results,
        uploaded_file_ids=run.uploaded_file_ids or [],
        resume_file_id=run.resume_file_id,
        target_job_code=run.target_job_code,
    )


@router.get("/latest", response_model=AnalysisStateResponse)
def get_latest_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> AnalysisStateResponse:
    student = db.scalar(select(Student).where(Student.user_id == current_user.id))
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="学生信息不存在")

    run = db.scalar(
        select(AnalysisRun)
        .where(AnalysisRun.student_id == student.id)
        .order_by(AnalysisRun.id.desc())
        .limit(1)
    )
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="无分析记录")

    return _run_to_state(run)


@router.get("/{run_id}", response_model=AnalysisStateResponse)
def get_analysis_state(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> AnalysisStateResponse:
    run = db.scalar(select(AnalysisRun).where(AnalysisRun.id == run_id))
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分析记录不存在")

    return _run_to_state(run)


@router.patch("/{run_id}/context", response_model=AnalysisStateResponse)
def update_analysis_context(
    run_id: int,
    payload: AnalysisContextUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> AnalysisStateResponse:
    if current_user.role not in ("student", "admin", "teacher"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    run = db.scalar(select(AnalysisRun).where(AnalysisRun.id == run_id))
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分析记录不存在")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(run, field, value)

    db.commit()
    db.refresh(run)
    return _run_to_state(run)


@router.post("/{run_id}/step/{step_key}/running", response_model=AnalysisStateResponse)
def mark_step_running(
    run_id: int,
    step_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> AnalysisStateResponse:
    if step_key not in VALID_STEPS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"无效步骤: {step_key}")

    run = db.scalar(select(AnalysisRun).where(AnalysisRun.id == run_id))
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分析记录不存在")

    run.status = "running"
    run.current_step = step_key
    run.failed_step = ""
    run.error_detail = ""
    db.commit()
    db.refresh(run)

    return _run_to_state(run)


@router.post("/{run_id}/step/{step_key}/complete", response_model=AnalysisStateResponse)
def mark_step_complete(
    run_id: int,
    step_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> AnalysisStateResponse:
    if step_key not in VALID_STEPS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"无效步骤: {step_key}")

    run = db.scalar(select(AnalysisRun).where(AnalysisRun.id == run_id))
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分析记录不存在")

    results = dict(run.step_results) if run.step_results else {}
    results[step_key] = True
    run.step_results = results
    run.current_step = step_key
    db.commit()
    db.refresh(run)

    return _run_to_state(run)


@router.post("/{run_id}/step/{step_key}/fail", response_model=AnalysisStateResponse)
def mark_step_failed(
    run_id: int,
    step_key: str,
    payload: AnalysisStepUpdateRequest = AnalysisStepUpdateRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> AnalysisStateResponse:
    if step_key not in VALID_STEPS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"无效步骤: {step_key}")

    run = db.scalar(select(AnalysisRun).where(AnalysisRun.id == run_id))
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分析记录不存在")

    run.status = "failed"
    run.current_step = step_key
    run.failed_step = step_key
    run.error_detail = payload.error_detail or "未知错误"
    db.commit()
    db.refresh(run)

    return _run_to_state(run)


@router.post("/{run_id}/complete", response_model=AnalysisStateResponse)
def mark_analysis_complete(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> AnalysisStateResponse:
    run = db.scalar(select(AnalysisRun).where(AnalysisRun.id == run_id))
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分析记录不存在")

    run.status = "completed"
    run.current_step = "reported"
    db.commit()
    db.refresh(run)

    return _run_to_state(run)


@router.post("/{run_id}/reset", response_model=AnalysisStateResponse)
def reset_analysis(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> AnalysisStateResponse:
    run = db.scalar(select(AnalysisRun).where(AnalysisRun.id == run_id))
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分析记录不存在")

    run.status = "pending"
    run.current_step = ""
    run.failed_step = ""
    run.error_detail = ""
    run.step_results = {}
    db.commit()
    db.refresh(run)

    return _run_to_state(run)
