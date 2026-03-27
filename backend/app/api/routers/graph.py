from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.schemas.job import GraphQueryResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.get("/jobs/{job_code}", response_model=GraphQueryResponse)
async def query_job_graph(job_code: str, container: ServiceContainer = Depends(get_container)) -> GraphQueryResponse:
    result = await container.graph_query_service.query_job(job_code)
    return GraphQueryResponse(**result)

