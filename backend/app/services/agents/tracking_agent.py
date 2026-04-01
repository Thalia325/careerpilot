from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.agents.base import BaseAgent, WorkflowState
from app.services.scheduler.scheduler_service import SchedulerService


class TrackingAgent(BaseAgent):
    name = "tracking_agent"

    def __init__(self, scheduler_service: SchedulerService) -> None:
        self.scheduler_service = scheduler_service

    def run(self, db: Session) -> WorkflowState:
        state = WorkflowState(workflow="tracking")
        self.add_step(state, "开始执行到期提醒和阶段复盘任务")
        result = self.scheduler_service.run_due_jobs(db)
        self.add_step(state, f"已执行 {len(result['executed_jobs'])} 个调度任务")
        state.result = result
        return state

