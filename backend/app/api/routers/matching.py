from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ensure_student_owns_resource, get_container, get_current_user, get_db_session
from app.api.routers.students import resolve_target_job
from app.core.errors import raise_resource_forbidden, require_role
from app.models import MatchDimensionScore, MatchResult, Student, User
from app.schemas.matching import MatchingRequest, MatchingResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/analyze", response_model=MatchingResponse)
def analyze_matching(
    payload: MatchingRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> MatchingResponse:
    # Verify user has access
    require_role(current_user.role, "student", "admin", "teacher")

    ensure_student_owns_resource(current_user, db, payload.student_id)

    job_code = payload.job_code
    if not job_code:
        student = db.scalar(select(Student).where(Student.user_id == current_user.id))
        if student:
            job_code, _ = resolve_target_job(db, student)
    if not job_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法确定目标岗位，请先选择或确认一个目标岗位")

    try:
        result = container.matching_service.analyze_match(
            db,
            payload.student_id,
            job_code,
            profile_version_id=payload.profile_version_id,
            analysis_run_id=payload.analysis_run_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return MatchingResponse(**result)


@router.get("/{match_id}", response_model=MatchingResponse)
def get_match_result(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> MatchingResponse:
    """获取指定的匹配结果历史记录"""
    match_result = db.scalar(
        select(MatchResult).where(MatchResult.id == match_id)
    )
    if not match_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="匹配记录不存在")

    # Permission check: student can only see own results
    if current_user.role == "student":
        if not match_result.student_id:
            raise_resource_forbidden()
        student = db.get(Student, match_result.student_id)
        if not student or student.user_id != current_user.id:
            raise_resource_forbidden()

    require_role(current_user.role, "student", "admin", "teacher")

    # Load dimension scores from MatchDimensionScore table
    dim_rows = db.scalars(
        select(MatchDimensionScore).where(MatchDimensionScore.match_result_id == match_result.id)
    ).all()
    dimensions = [
        {
            "dimension": d.dimension,
            "score": d.score,
            "weight": d.weight,
            "reasoning": d.reasoning or "",
            "evidence": d.evidence_json or {},
        }
        for d in dim_rows
    ]

    return MatchingResponse(
        student_id=match_result.student_id or 0,
        job_code=match_result.target_job_code or "",
        total_score=match_result.total_score,
        weights={},
        dimensions=dimensions,
        strengths=match_result.strengths_json or [],
        gap_items=match_result.gaps_json or [],
        suggestions=match_result.suggestions_json or [],
        summary=match_result.summary or "",
    )
