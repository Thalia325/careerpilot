from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.llm.providers import BaseLLMProvider
from app.models import CareerReport, GrowthTask, JobProfile, ReportVersion, Student, StudentProfile
from app.services.matching.matching_service import MatchingService
from app.services.paths.career_path_service import CareerPathService
from app.services.reports.exporters import export_markdown_to_docx, export_markdown_to_pdf

logger = logging.getLogger(__name__)


class ReportService:
    REQUIRED_SECTIONS = ["overview", "matching_analysis", "goals", "action_plan", "evidence"]

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        matching_service: MatchingService,
        career_path_service: CareerPathService,
    ) -> None:
        self.llm_provider = llm_provider
        self.matching_service = matching_service
        self.career_path_service = career_path_service
        self.settings = get_settings()

    async def generate_report(self, db: Session, student_id: int, job_code: str) -> dict:
        student = db.get(Student, student_id)
        student_profile = db.scalar(select(StudentProfile).where(StudentProfile.student_id == student_id))
        job_profile = db.scalar(select(JobProfile).where(JobProfile.job_code == job_code))
        if not student or not student_profile or not job_profile:
            raise ValueError("生成报告前请先准备学生画像与岗位画像")
        match_result = self.matching_service.analyze_match(db, student_id, job_code)
        path_result = await self.career_path_service.plan_path(db, student_id, job_code)
        llm_result = await self.llm_provider.generate_report(
            {
                "student_name": student.user.full_name if hasattr(student, "user") else f"学生{student_id}",
                "student_profile": {
                    "skills": student_profile.skills_json,
                    "certificates": student_profile.certificates_json,
                    "capability_scores": student_profile.capability_scores,
                    "completeness_score": student_profile.completeness_score,
                },
                "job_profile": {
                    "job_code": job_profile.job_code,
                    "title": job_profile.title,
                    "summary": job_profile.summary,
                    "skill_requirements": job_profile.skill_requirements,
                },
                "job_title": job_profile.title,
                "match_result": match_result,
                "path_result": path_result,
            }
        )
        report = db.scalar(
            select(CareerReport)
            .where(CareerReport.student_id == student_id)
            .where(CareerReport.target_job_code == job_code)
        )
        if not report:
            report = CareerReport(student_id=student_id, target_job_code=job_code)
            db.add(report)
            db.flush()
        report.content_json = llm_result["content"]
        report.markdown_content = llm_result["markdown_content"]
        report.status = "generated"
        version_count = len(list(db.scalars(select(ReportVersion).where(ReportVersion.report_id == report.id)).all()))
        db.add(
            ReportVersion(
                report_id=report.id,
                version_no=version_count + 1,
                content_json=report.content_json,
                markdown_content=report.markdown_content,
                editor_notes="系统自动生成",
            )
        )
        self._sync_growth_tasks(db, report.id, student_id, report.content_json["action_plan"])
        db.commit()
        return {
            "report_id": report.id,
            "student_id": student_id,
            "job_code": job_code,
            "content": report.content_json,
            "markdown_content": report.markdown_content,
            "status": report.status,
        }

    def _sync_growth_tasks(self, db: Session, report_id: int, student_id: int, action_plan: dict) -> None:
        for item in action_plan.get("short_term", []):
            db.add(
                GrowthTask(
                    student_id=student_id,
                    report_id=report_id,
                    title=item,
                    phase="short_term",
                    metric="阶段技能覆盖率提升",
                    status="pending",
                )
            )
        for item in action_plan.get("mid_term", []):
            db.add(
                GrowthTask(
                    student_id=student_id,
                    report_id=report_id,
                    title=item,
                    phase="mid_term",
                    metric="项目/实习成果达成",
                    status="pending",
                )
            )

    def get_report(self, db: Session, report_id: int) -> CareerReport:
        report = db.get(CareerReport, report_id)
        if not report:
            raise ValueError("报告不存在")
        return report

    async def polish_report(self, db: Session, report_id: int, markdown_content: str) -> dict:
        report = self.get_report(db, report_id)
        polished = await self.llm_provider.polish_markdown(markdown_content)
        report.markdown_content = polished
        report.status = "polished"
        version_count = len(list(db.scalars(select(ReportVersion).where(ReportVersion.report_id == report.id)).all()))
        db.add(
            ReportVersion(
                report_id=report.id,
                version_no=version_count + 1,
                content_json=report.content_json,
                markdown_content=polished,
                editor_notes="智能润色",
            )
        )
        db.commit()
        return {
            "report_id": report.id,
            "student_id": report.student_id,
            "job_code": report.target_job_code,
            "content": report.content_json,
            "markdown_content": polished,
            "status": report.status,
        }

    def check_completeness(self, db: Session, report_id: int) -> dict:
        try:
            report = self.get_report(db, report_id)
            missing = [section for section in self.REQUIRED_SECTIONS if section not in report.content_json]
            suggestions = []
            if "matching_analysis" in missing:
                suggestions.append("补充职业探索与岗位匹配分析。")
            if "goals" in missing:
                suggestions.append("补充职业目标和路径规划。")
            if "action_plan" in missing:
                suggestions.append("补充短期、中期行动计划与评估指标。")
            if "evidence" in missing:
                suggestions.append("补充岗位画像、学生画像、路径推荐依据。")
            return {
                "report_id": report_id,
                "is_complete": len(missing) == 0,
                "missing_sections": missing,
                "suggestions": suggestions or ["报告结构完整，可直接导出。"],
            }
        except ValueError as e:
            logger.error(f"ValueError while checking report completeness for {report_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to check completeness for report {report_id}: {str(e)}")
            raise ValueError(f"Failed to check report completeness: {str(e)}") from e

    def export_report(self, db: Session, report_id: int, export_format: str) -> dict:
        try:
            report = self.get_report(db, report_id)
            suffix = "pdf" if export_format == "pdf" else "docx"
            file_name = f"career_report_{report_id}.{suffix}"
            output_path = self.settings.export_path / file_name
            if export_format == "pdf":
                export_markdown_to_pdf(report.markdown_content, output_path)
            else:
                export_markdown_to_docx(report.markdown_content, output_path)
            return {"format": export_format, "path": str(output_path), "file_name": file_name}
        except ValueError as e:
            logger.error(f"ValueError while exporting report {report_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to export report {report_id} as {export_format}: {str(e)}")
            raise ValueError(f"Failed to export report: {str(e)}") from e

