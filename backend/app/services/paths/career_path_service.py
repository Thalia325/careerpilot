from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import JobProfile, PathRecommendation, StudentProfile
from app.services.paths.graph_query_service import GraphQueryService


class CareerPathService:
    def __init__(self, graph_query_service: GraphQueryService) -> None:
        self.graph_query_service = graph_query_service

    async def plan_path(self, db: Session, student_id: int, job_code: str) -> dict:
        student_profile = db.scalar(select(StudentProfile).where(StudentProfile.student_id == student_id))
        job_profile = db.scalar(select(JobProfile).where(JobProfile.job_code == job_code))
        if not student_profile or not job_profile:
            raise ValueError("路径规划缺少学生画像或岗位画像")
        graph = await self.graph_query_service.query_job(job_code)
        primary_path = graph["promotion_paths"][0] if graph["promotion_paths"] else [job_profile.title]
        alternate_paths = graph["transition_paths"][:2]
        gaps = [
            {"stage": "当前岗位", "missing_skills": graph["adjacent_skill_gaps"].get(path[-1], [])}
            for path in alternate_paths
        ]
        recommendations = [
            {
                "phase": "短期",
                "focus": "补齐目标岗位高频技能与证书",
                "items": job_profile.skill_requirements[:3],
            },
            {
                "phase": "中期",
                "focus": "通过实习/项目验证路径可行性",
                "items": ["实习投递", "竞赛项目", "阶段复盘"],
            },
        ]
        rationale = "基于岗位图谱的晋升链路和转岗链路，结合学生当前技能覆盖情况生成主路径与备选路径。"
        existing = db.scalar(
            select(PathRecommendation)
            .where(PathRecommendation.student_id == student_id)
            .where(PathRecommendation.target_job_code == job_code)
        )
        if not existing:
            existing = PathRecommendation(student_id=student_id, target_job_code=job_code)
            db.add(existing)
            db.flush()
        existing.primary_path_json = primary_path
        existing.alternate_paths_json = alternate_paths
        existing.gaps_json = gaps
        existing.recommendations_json = recommendations
        db.commit()
        return {
            "student_id": student_id,
            "target_job_code": job_code,
            "primary_path": primary_path,
            "alternate_paths": alternate_paths,
            "gaps": gaps,
            "recommendations": recommendations,
            "rationale": rationale,
        }

