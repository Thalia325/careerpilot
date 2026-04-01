from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.agents.base import BaseAgent, WorkflowState
from app.services.ingestion.file_ingestion import FileIngestionService


class ResumeParsingAgent(BaseAgent):
    name = "resume_parser"

    def __init__(self, file_service: FileIngestionService) -> None:
        self.file_service = file_service

    async def run(self, db: Session, uploaded_file_id: int, document_type: str) -> WorkflowState:
        state = WorkflowState(workflow="parse_resume")
        self.add_step(state, "开始调用 OCR 解析材料")
        result = await self.file_service.parse_uploaded_file(db, uploaded_file_id, document_type)
        self.add_step(state, "已输出结构化 JSON")
        state.result = result
        return state

