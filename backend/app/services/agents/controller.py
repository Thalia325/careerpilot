from __future__ import annotations

from dataclasses import asdict

from sqlalchemy.orm import Session

from app.services.agents.job_profile_agent import JobProfileAgent
from app.services.agents.report_agent import ReportGenerationAgent
from app.services.agents.resume_agent import ResumeParsingAgent
from app.services.agents.tracking_agent import TrackingAgent


class MainControllerAgent:
    def __init__(
        self,
        resume_agent: ResumeParsingAgent,
        job_profile_agent: JobProfileAgent,
        tracking_agent: TrackingAgent,
        report_agent: ReportGenerationAgent,
    ) -> None:
        self.resume_agent = resume_agent
        self.job_profile_agent = job_profile_agent
        self.tracking_agent = tracking_agent
        self.report_agent = report_agent

    async def execute(self, db: Session, workflow: str, payload: dict) -> dict:
        if workflow == "parse_resume":
            state = await self.resume_agent.run(db, payload["uploaded_file_id"], payload.get("document_type", "resume"))
        elif workflow == "build_job_profiles":
            state = await self.job_profile_agent.run(db, payload["job_codes"])
        elif workflow == "generate_report":
            state = await self.report_agent.run(db, payload["student_id"], payload["job_code"])
        elif workflow == "tracking":
            state = self.tracking_agent.run(db)
        else:
            raise ValueError(f"未知工作流: {workflow}")
        return asdict(state)

