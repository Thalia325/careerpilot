from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.models import User
from app.schemas.agent import AgentExecuteRequest, AgentExecuteResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/execute", response_model=AgentExecuteResponse)
async def execute_agent_workflow(
    payload: AgentExecuteRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> AgentExecuteResponse:
    # Verify user has access
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    result = await container.controller_agent.execute(db, payload.workflow, payload.payload)
    return AgentExecuteResponse(workflow=payload.workflow, state=result)
