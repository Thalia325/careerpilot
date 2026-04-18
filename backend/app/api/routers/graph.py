from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_container, get_current_user
from app.core.errors import require_role
from app.models import User
from app.schemas.job import GraphQueryResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.get("/jobs/{job_code}", response_model=GraphQueryResponse)
async def query_job_graph(
    job_code: str,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> GraphQueryResponse:
    # Verify user has access
    require_role(current_user.role, "student", "admin", "teacher")

    result = await container.graph_query_service.query_job(job_code)
    return GraphQueryResponse(**result)

