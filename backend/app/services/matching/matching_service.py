from __future__ import annotations

import logging
from types import SimpleNamespace

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    AnalysisRun,
    JobPosting,
    JobProfile,
    MatchDimensionScore,
    MatchResult,
    ProfileVersion,
    Student,
    StudentProfile,
)
from app.services.matching.recommendation import (
    extract_resume_experience_context,
    score_recommended_job,
)
from app.services.reference import find_best_template, load_job_profile_templates

logger = logging.getLogger(__name__)

# The four fixed matching dimensions
FOUR_DIMENSIONS = [
    ("basic_requirements", "基础要求", "根据证书匹配、画像完整度和实习能力评估基础门槛。"),
    ("professional_skills", "职业技能", "根据核心技能覆盖率与关键技能缺口评分。"),
    ("professional_literacy", "职业素养", "根据沟通、抗压和实习表现与岗位要求的接近程度评分。"),
    ("development_potential", "发展潜力", "根据学习能力、创新能力和画像完整度评估长期成长性。"),
]


class MatchingService:
    @staticmethod
    def _profile_from_version(version: ProfileVersion, fallback: StudentProfile) -> SimpleNamespace:
        snapshot = version.snapshot_json or {}
        return SimpleNamespace(
            id=fallback.id,
            student_id=fallback.student_id,
            source_summary=str(snapshot.get("source_summary") or version.source_files or fallback.source_summary or ""),
            skills_json=snapshot.get("skills") or fallback.skills_json or [],
            certificates_json=snapshot.get("certificates") or fallback.certificates_json or [],
            projects_json=snapshot.get("projects") or fallback.projects_json or [],
            internships_json=snapshot.get("internships") or fallback.internships_json or [],
            capability_scores=snapshot.get("capability_scores") or fallback.capability_scores or {},
            completeness_score=snapshot.get("completeness_score") or fallback.completeness_score or 0,
            competitiveness_score=snapshot.get("competitiveness_score") or fallback.competitiveness_score or 0,
        )

    @staticmethod
    def _list_value(value: object) -> list:
        return value if isinstance(value, list) else []

    @staticmethod
    def _dict_value(value: object) -> dict:
        return value if isinstance(value, dict) else {}

    def _find_template(self, job_code: str, title: str) -> dict:
        for template in load_job_profile_templates():
            if template.get("job_code") == job_code:
                return template
        return find_best_template(title or job_code)

    def _ensure_job_profile(self, db: Session, job_code: str) -> JobProfile | None:
        job_profile = db.scalar(select(JobProfile).where(JobProfile.job_code == job_code))
        if job_profile:
            return job_profile

        posting = db.scalar(select(JobPosting).where(JobPosting.job_code == job_code).limit(1))
        template = self._find_template(job_code, posting.title if posting else job_code)
        if not posting and template.get("job_code") != job_code:
            return None

        title = (posting.title if posting else template.get("title")) or job_code
        profile = JobProfile(
            job_code=job_code,
            job_posting_id=posting.id if posting else None,
            title=title,
        )
        explanations = self._dict_value(template.get("explanations"))
        profile.summary = (
            (posting.description if posting else "")
            or str(template.get("summary") or "")
            or f"{title} 岗位画像由系统按相近模板补全。"
        )
        profile.skill_requirements = self._list_value(template.get("skills"))
        profile.certificate_requirements = self._list_value(template.get("certificates"))
        profile.innovation_requirements = str(explanations.get("创新能力", ""))
        profile.learning_requirements = str(explanations.get("学习能力", ""))
        profile.resilience_requirements = str(explanations.get("抗压能力", ""))
        profile.communication_requirements = str(explanations.get("沟通能力", ""))
        profile.internship_requirements = str(explanations.get("实习能力", ""))
        profile.capability_scores = self._dict_value(template.get("capabilities"))
        profile.dimension_weights = self._dict_value(template.get("dimension_weights"))
        profile.explanation_json = explanations
        db.add(profile)
        db.flush()
        logger.info("Created fallback job profile for job_code %s", job_code)
        return profile

    def analyze_match(
        self,
        db: Session,
        student_id: int,
        job_code: str,
        profile_version_id: int | None = None,
        analysis_run_id: int | None = None,
    ) -> dict:
        try:
            student_profile = db.scalar(select(StudentProfile).where(StudentProfile.student_id == student_id))
            job_profile = self._ensure_job_profile(db, job_code)
            student = db.get(Student, student_id)
            if not student or not student_profile:
                raise ValueError("学生画像不存在，请先完成上传和画像生成")
            if not job_profile:
                raise ValueError(f"岗位画像不存在：{job_code}，请先导入岗位并生成岗位画像")
            scoring_profile = student_profile
            source_summary = student_profile.source_summary
            if profile_version_id:
                profile_version = db.get(ProfileVersion, profile_version_id)
                if not profile_version or profile_version.student_id != student_id:
                    raise ValueError("画像版本不存在或不属于当前学生")
                scoring_profile = self._profile_from_version(profile_version, student_profile)
                source_summary = profile_version.source_files or scoring_profile.source_summary
            default_weights = {
                "basic_requirements": 0.2,
                "professional_skills": 0.4,
                "professional_literacy": 0.2,
                "development_potential": 0.2,
            }
            weights = {**default_weights, **(job_profile.dimension_weights or {})}
            posting = db.scalar(select(JobPosting).where(JobPosting.job_code == job_code).limit(1))
            experience = extract_resume_experience_context(db, student.user_id, job_profile, source_summary)
            scoring = score_recommended_job(scoring_profile, job_profile, experience, posting)
            scoring_dimensions = scoring["dimensions"]

            # Build exactly 4 fixed dimensions
            dimensions = []
            for dim_key, dim_name, dim_reasoning in FOUR_DIMENSIONS:
                dim_data = scoring_dimensions[dim_key]
                dimensions.append({
                    "dimension": dim_name,
                    "score": dim_data["score"],
                    "weight": weights[dim_key],
                    "reasoning": dim_reasoning,
                    "evidence": dim_data["evidence"],
                })

            total_score = scoring["score"]
            skill_evidence = scoring_dimensions["professional_skills"]["evidence"]
            basic_evidence = scoring_dimensions["basic_requirements"]["evidence"]

            gap_items = []
            for skill in skill_evidence["missing_skills"]:
                gap_items.append({"type": "skill", "name": skill, "suggestion": f"优先通过课程/项目补齐 {skill}。"})
            for certificate in basic_evidence["missing_certificates"]:
                gap_items.append({"type": "certificate", "name": certificate, "suggestion": f"可将 {certificate} 纳入中期目标。"})

            suggestions = [
                "围绕缺失技能补齐 1-2 个项目案例。",
                "将简历中的项目成果量化，增强竞争力表达。",
                "按月复盘岗位技能覆盖率并更新行动计划。",
            ]
            strengths = list(dict.fromkeys(scoring["matched_skills"] + scoring["experience_tags"][:3]))
            summary = (
                f"目标岗位为 {job_profile.title}。"
                f"当前核心技能匹配度 {scoring_dimensions['professional_skills']['score']:.1f} 分，"
                f"基础画像分 {scoring['base_score']:.1f} 分，"
                f"综合得分 {total_score:.1f} 分。"
                f"优势主要体现在 {', '.join(strengths) or '项目经历与学习潜力'}，"
                f"短板集中在 {', '.join(item['name'] for item in gap_items[:3]) or '证书与项目表达'}。"
            )

            # Find or create MatchResult
            if analysis_run_id:
                match = db.scalar(
                    select(MatchResult)
                    .where(MatchResult.student_id == student_id)
                    .where(MatchResult.target_job_code == job_code)
                    .where(MatchResult.analysis_run_id == analysis_run_id)
                )
            elif profile_version_id:
                match = db.scalar(
                    select(MatchResult)
                    .where(MatchResult.student_id == student_id)
                    .where(MatchResult.target_job_code == job_code)
                    .where(MatchResult.profile_version_id == profile_version_id)
                )
            else:
                match = db.scalar(
                    select(MatchResult)
                    .where(MatchResult.student_profile_id == student_profile.id)
                    .where(MatchResult.job_profile_id == job_profile.id)
                    .where(MatchResult.analysis_run_id == None)
                    .where(MatchResult.profile_version_id == None)
                )
            if not match:
                match = MatchResult(student_profile_id=student_profile.id, job_profile_id=job_profile.id)
                db.add(match)
                db.flush()
            match.total_score = total_score
            match.summary = summary
            match.strengths_json = strengths
            match.gaps_json = gap_items
            match.suggestions_json = suggestions
            # Binding fields
            match.student_id = student_id
            match.target_job_code = job_code
            match.profile_version_id = profile_version_id
            match.analysis_run_id = analysis_run_id

            db.execute(delete(MatchDimensionScore).where(MatchDimensionScore.match_result_id == match.id))
            for dimension in dimensions:
                db.add(
                    MatchDimensionScore(
                        match_result_id=match.id,
                        dimension=dimension["dimension"],
                        score=dimension["score"],
                        weight=dimension["weight"],
                        reasoning=dimension["reasoning"],
                        evidence_json=dimension["evidence"],
                    )
                )

            # If analysis_run_id provided, update AnalysisRun.match_result_id
            if analysis_run_id:
                run = db.get(AnalysisRun, analysis_run_id)
                if run:
                    run.match_result_id = match.id

            db.commit()
            return {
                "student_id": student_id,
                "job_code": job_code,
                "match_result_id": match.id,
                "total_score": total_score,
                "weights": weights,
                "dimensions": dimensions,
                "strengths": strengths,
                "gap_items": gap_items,
                "suggestions": suggestions,
                "summary": summary,
            }
        except ValueError as e:
            logger.error(f"ValueError in analyze_match for student {student_id}, job {job_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in analyze_match for student {student_id}, job {job_code}: {str(e)}")
            raise ValueError(f"Failed to analyze match: {str(e)}") from e
