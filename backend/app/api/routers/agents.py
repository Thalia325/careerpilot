from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_db_session
from app.schemas.agent import AgentExecuteRequest, AgentExecuteResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/execute", response_model=AgentExecuteResponse)
async def execute_agent_workflow(
    payload: AgentExecuteRequest,
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> AgentExecuteResponse:
    result = await container.controller_agent.execute(db, payload.workflow, payload.payload)
    return AgentExecuteResponse(workflow=payload.workflow, state=result)
