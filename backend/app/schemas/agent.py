from typing import Any

from pydantic import BaseModel


class AgentExecuteRequest(BaseModel):
    workflow: str
    payload: dict[str, Any]


class AgentExecuteResponse(BaseModel):
    workflow: str
    state: dict[str, Any]

