from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.models import User
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
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    result = container.matching_service.analyze_match(db, payload.student_id, payload.job_code)
    return MatchingResponse(**result)

