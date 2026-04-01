from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.agents.base import BaseAgent, WorkflowState
from app.services.ingestion.job_import_service import JobImportService


class JobProfileAgent(BaseAgent):
    name = "job_profiler"

    def __init__(self, job_import_service: JobImportService) -> None:
        self.job_import_service = job_import_service

    async def run(self, db: Session, job_codes: list[str]) -> WorkflowState:
        state = WorkflowState(workflow="build_job_profiles")
        self.add_step(state, "开始生成岗位画像并同步知识库/图谱")
        profiles = await self.job_import_service.generate_profiles(db, job_codes)
        self.add_step(state, f"已生成 {len(profiles)} 个岗位画像")
        state.result = {"job_codes": [item.job_code for item in profiles]}
        return state

