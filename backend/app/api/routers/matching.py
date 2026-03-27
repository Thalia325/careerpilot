from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_db_session
from app.schemas.matching import MatchingRequest, MatchingResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/analyze", response_model=MatchingResponse)
def analyze_matching(
    payload: MatchingRequest,
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> MatchingResponse:
    result = container.matching_service.analyze_match(db, payload.student_id, payload.job_code)
    return MatchingResponse(**result)

