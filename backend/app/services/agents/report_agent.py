from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.agents.base import BaseAgent, WorkflowState
from app.services.reports.report_service import ReportService


class ReportGenerationAgent(BaseAgent):
    name = "report_agent"

    def __init__(self, report_service: ReportService) -> None:
        self.report_service = report_service

    async def run(self, db: Session, student_id: int, job_code: str) -> WorkflowState:
        state = WorkflowState(workflow="generate_report")
        self.add_step(state, "开始汇总画像、匹配结果与路径推荐")
        result = await self.report_service.generate_report(db, student_id, job_code)
        self.add_step(state, "职业发展报告已生成")
        state.result = result
        return state

