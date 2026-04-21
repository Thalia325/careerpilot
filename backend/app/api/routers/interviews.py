from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ensure_student_owns_resource, get_container, get_current_user, get_db_session
from app.api.routers.students import resolve_target_job
from app.core.errors import require_role
from app.models import Student, User
from app.schemas.interview import (
    MockInterviewEvaluateRequest,
    MockInterviewEvaluateResponse,
    MockInterviewGenerateResponse,
    MockInterviewRequest,
)
from app.services.bootstrap import ServiceContainer

router = APIRouter()


def _resolve_job_code(db: Session, current_user: User, student_id: int, job_code: str) -> str:
    if job_code:
        return job_code
    student = db.scalar(select(Student).where(Student.id == student_id))
    if not student and current_user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == current_user.id))
    if student:
        resolved_code, _ = resolve_target_job(db, student)
        if resolved_code:
            return resolved_code
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法确定目标岗位，请先选择目标岗位。")


@router.post("/mock/generate", response_model=MockInterviewGenerateResponse)
def generate_mock_interview(
    payload: MockInterviewRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> MockInterviewGenerateResponse:
    require_role(current_user.role, "student", "admin", "teacher")
    ensure_student_owns_resource(current_user, db, payload.student_id)

    job_code = _resolve_job_code(db, current_user, payload.student_id, payload.job_code)
    try:
        result = container.mock_interview_service.generate_questions(
            db,
            payload.student_id,
            job_code,
            profile_version_id=payload.profile_version_id,
            analysis_run_id=payload.analysis_run_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return MockInterviewGenerateResponse(**result)


@router.post("/mock/evaluate", response_model=MockInterviewEvaluateResponse)
def evaluate_mock_interview(
    payload: MockInterviewEvaluateRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> MockInterviewEvaluateResponse:
    require_role(current_user.role, "student", "admin", "teacher")
    ensure_student_owns_resource(current_user, db, payload.student_id)

    job_code = _resolve_job_code(db, current_user, payload.student_id, payload.job_code)
    try:
        result = container.mock_interview_service.evaluate_answers(
            db,
            payload.student_id,
            job_code,
            [item.model_dump() for item in payload.answers],
            profile_version_id=payload.profile_version_id,
            analysis_run_id=payload.analysis_run_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return MockInterviewEvaluateResponse(**result)
