from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_db_session
from app.schemas.common import APIResponse
from app.schemas.matching import MatchingRequest
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/plan", response_model=APIResponse)
async def plan_career_path(
    payload: MatchingRequest,
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    result = await container.career_path_service.plan_path(db, payload.student_id, payload.job_code)
    return APIResponse(data=result)

