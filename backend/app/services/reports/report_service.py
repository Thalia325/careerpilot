from __future__ import annotations

import logging
import re
from ast import literal_eval
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.llm.providers import BaseLLMProvider
from app.models import AnalysisRun, CareerReport, GrowthTask, JobProfile, PathRecommendation, ProfileVersion, ReportVersion, Student, StudentProfile, UploadedFile
from app.services.matching.recommendation import _resume_relevance
from app.services.matching.matching_service import MatchingService
from app.services.paths.career_path_service import CareerPathService
from app.services.reports.exporters import export_markdown_to_docx, export_markdown_to_pdf

logger = logging.getLogger(__name__)


class ReportService:
    REQUIRED_SECTIONS = [
        "student_summary", "resume_summary", "capability_profile", "target_job_analysis",
        "matching_analysis", "gap_analysis", "career_path", "short_term_plan",
        "mid_term_plan", "evaluation_cycle", "teacher_comments",
    ]

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

    UNAVAILABLE_VALUES = {
        "",
        "无",
        "暂无",
        "未知",
        "未填写",
        "不详",
        "经历",
        "生",
        "负责人",
        "模型",
        "N/A",
        "none",
        "null",
    }

    def _clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value).strip()
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        text = text.strip(" ，,；;。")
        if text in self.UNAVAILABLE_VALUES:
            return ""
        if "由于信息不足" in text or "无法详细" in text or "无法列举" in text:
            return ""
        return text

    def _parse_object_string(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        text = value.strip()
        if not (text.startswith("{") and text.endswith("}")):
            return value
        try:
            return literal_eval(text)
        except Exception:
            return value

    def _clean_list(self, values: Any, *, limit: int = 8, object_keys: list[str] | None = None) -> list[str]:
        if not isinstance(values, list):
            values = [values] if values else []
        cleaned: list[str] = []
        for item in values:
            item = self._parse_object_string(item)
            if isinstance(item, dict):
                parts = []
                for key in object_keys or ["name", "description", "role", "actual_achievements", "responsibilities"]:
                    part = self._clean_text(item.get(key))
                    if part:
                        parts.append(part)
                text = "；".join(dict.fromkeys(parts))
            elif isinstance(item, (list, tuple)):
                text = " → ".join(self._clean_text(part) for part in item if self._clean_text(part))
            else:
                text = self._clean_text(item)
            if text and text not in cleaned:
                cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return cleaned

    def _line(self, label: str, value: Any) -> str:
        text = self._clean_text(value)
        return f"- {label}：{text}\n" if text else ""

    def _list_lines(self, items: list[str]) -> str:
        return "".join(f"- {item}\n" for item in items if self._clean_text(item))

    def _normalize_report_content(self, content: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(content or {})

        resume = dict(normalized.get("resume_summary") or {})
        resume["skills"] = self._clean_list(resume.get("skills"), limit=12)
        resume["projects"] = self._clean_list(
            resume.get("projects"),
            limit=5,
            object_keys=["name", "description", "role", "actual_achievements"],
        )
        resume["internships"] = self._clean_list(
            resume.get("internships"),
            limit=5,
            object_keys=["company", "position", "duration", "responsibilities", "gained_skills"],
        )
        resume["certificates"] = self._clean_list(resume.get("certificates"), limit=6)
        normalized["resume_summary"] = resume

        profile = dict(normalized.get("capability_profile") or {})
        profile["skills"] = self._clean_list(profile.get("skills"), limit=12)
        profile["certificates"] = self._clean_list(profile.get("certificates"), limit=6)
        profile["projects"] = self._clean_list(
            profile.get("projects"),
            limit=5,
            object_keys=["name", "description", "role", "actual_achievements"],
        )
        profile["internships"] = self._clean_list(
            profile.get("internships"),
            limit=5,
            object_keys=["company", "position", "duration", "responsibilities", "gained_skills"],
        )
        normalized["capability_profile"] = profile

        target = dict(normalized.get("target_job_analysis") or {})
        target["skill_requirements"] = self._clean_list(target.get("skill_requirements"), limit=12)
        target["certificate_requirements"] = self._clean_list(target.get("certificate_requirements"), limit=6)
        target["matched_skills"] = self._clean_list(target.get("matched_skills"), limit=10)
        target["missing_skills"] = self._clean_list(target.get("missing_skills"), limit=10)
        normalized["target_job_analysis"] = target

        matching = dict(normalized.get("matching_analysis") or {})
        matching["strengths"] = self._clean_list(matching.get("strengths"), limit=8)
        normalized["matching_analysis"] = matching

        gap = dict(normalized.get("gap_analysis") or {})
        gap["suggestions"] = self._clean_list(gap.get("suggestions"), limit=8)
        normalized["gap_analysis"] = gap

        for key in ["short_term_plan", "mid_term_plan"]:
            plan = dict(normalized.get(key) or {})
            plan["items"] = self._clean_list(plan.get("items"), limit=8)
            normalized[key] = plan

        return normalized

    def _build_standard_markdown(self, content: dict[str, Any]) -> str:
        content = self._normalize_report_content(content)
        student = content.get("student_summary") or {}
        resume = content.get("resume_summary") or {}
        profile = content.get("capability_profile") or {}
        target = content.get("target_job_analysis") or {}
        matching = content.get("matching_analysis") or {}
        gap = content.get("gap_analysis") or {}
        career = content.get("career_path") or {}
        short_plan = content.get("short_term_plan") or {}
        mid_plan = content.get("mid_term_plan") or {}
        evaluation = content.get("evaluation_cycle") or {}

        sections: list[str] = ["# CareerPilot 职业发展报告\n\n"]

        basic = (
            self._line("姓名", student.get("name"))
            + self._line("专业", student.get("major"))
            + self._line("年级", student.get("grade"))
            + self._line("简历意向岗位", student.get("intent_job"))
            + self._line("意向城市", student.get("intent_city"))
        )
        sections.append(f"## 一、学生基本情况\n{basic}\n")

        resume_lines = ""
        if resume.get("skills"):
            resume_lines += f"- 技能：{'、'.join(resume['skills'])}\n"
        if resume.get("projects"):
            resume_lines += "### 项目经历\n" + self._list_lines(resume["projects"])
        if resume.get("internships"):
            resume_lines += "### 实习经历\n" + self._list_lines(resume["internships"])
        if resume.get("certificates"):
            resume_lines += f"- 证书：{'、'.join(resume['certificates'])}\n"
        sections.append(f"## 二、简历解析摘要\n{resume_lines}\n")

        capability = ""
        if profile.get("skills"):
            capability += f"- 能力标签：{'、'.join(profile['skills'])}\n"
        scores = profile.get("capability_scores") if isinstance(profile.get("capability_scores"), dict) else {}
        if scores:
            score_labels = {
                "innovation": "创新能力",
                "learning": "学习能力",
                "resilience": "抗压能力",
                "communication": "沟通能力",
                "internship": "实践能力",
            }
            score_text = [
                f"{label} {float(scores[key]):.0f} 分"
                for key, label in score_labels.items()
                if key in scores and isinstance(scores.get(key), (int, float))
            ]
            if score_text:
                capability += f"- 维度评分：{'；'.join(score_text)}\n"
        if isinstance(profile.get("completeness_score"), (int, float)):
            capability += f"- 画像完整度：{profile['completeness_score']:.0f}%\n"
        sections.append(f"## 三、能力画像\n{capability}\n")

        target_lines = (
            self._line("目标岗位", target.get("job_title"))
            + self._line("岗位摘要", target.get("summary"))
        )
        if target.get("skill_requirements"):
            target_lines += f"- 技能要求：{'、'.join(target['skill_requirements'])}\n"
        if target.get("matched_skills"):
            target_lines += f"- 已匹配技能：{'、'.join(target['matched_skills'])}\n"
        if target.get("missing_skills"):
            target_lines += f"- 待补齐技能：{'、'.join(target['missing_skills'])}\n"
        if target.get("certificate_requirements"):
            target_lines += f"- 证书要求：{'、'.join(target['certificate_requirements'])}\n"
        sections.append(f"## 四、目标岗位分析\n{target_lines}\n")

        match_lines = ""
        if isinstance(matching.get("total_score"), (int, float)):
            match_lines += f"- 综合匹配得分：{matching['total_score']:.1f} 分\n"
        if matching.get("strengths"):
            match_lines += f"- 当前契合点：{'、'.join(matching['strengths'])}\n"
        dimensions = matching.get("dimensions") if isinstance(matching.get("dimensions"), list) else []
        if dimensions:
            match_lines += "### 维度评分\n"
            for dim in dimensions:
                if not isinstance(dim, dict):
                    continue
                name = self._clean_text(dim.get("dimension"))
                score = dim.get("score")
                reasoning = self._clean_text(dim.get("reasoning"))
                if name and isinstance(score, (int, float)):
                    suffix = f"：{reasoning}" if reasoning else ""
                    match_lines += f"- {name}：{score:.1f} 分{suffix}\n"
        sections.append(f"## 五、人岗匹配分析\n{match_lines}\n")

        gap_lines = ""
        skill_gaps = [self._clean_text(item.get("name")) for item in gap.get("skill_gaps", []) if isinstance(item, dict)]
        skill_gaps = [item for item in skill_gaps if item]
        if skill_gaps:
            gap_lines += f"- 主要技能差距：{'、'.join(skill_gaps)}\n"
        if gap.get("suggestions"):
            gap_lines += "### 提升建议\n" + self._list_lines(gap["suggestions"])
        sections.append(f"## 六、差距分析\n{gap_lines}\n")

        path_lines = ""
        primary_path = self._clean_list(career.get("primary_path"), limit=6)
        if primary_path:
            path_lines += f"- 主路径：{' → '.join(primary_path)}\n"
        alt_paths = career.get("alternate_paths") if isinstance(career.get("alternate_paths"), list) else []
        cleaned_alt = []
        for path in alt_paths:
            if isinstance(path, list):
                item = " → ".join(self._clean_list(path, limit=5))
                if item and item not in cleaned_alt:
                    cleaned_alt.append(item)
            if len(cleaned_alt) >= 3:
                break
        if cleaned_alt:
            path_lines += "### 备选路径\n" + self._list_lines(cleaned_alt)
        rationale = self._clean_text(career.get("rationale"))
        if rationale:
            path_lines += f"- 路径依据：{rationale}\n"
        sections.append(f"## 七、职业路径规划\n{path_lines}\n")

        sections.append(f"## 八、短期行动计划\n{self._list_lines(short_plan.get('items') or [])}\n")
        sections.append(f"## 九、中期行动计划\n{self._list_lines(mid_plan.get('items') or [])}\n")

        eval_lines = ""
        metrics = evaluation.get("metrics") if isinstance(evaluation.get("metrics"), list) else []
        for metric in metrics:
            if not isinstance(metric, dict):
                continue
            phase = self._clean_text(metric.get("phase"))
            name = self._clean_text(metric.get("metric"))
            target = self._clean_text(metric.get("target"))
            method = self._clean_text(metric.get("evaluation_method"))
            pieces = [piece for piece in [name, f"目标：{target}" if target else "", f"方式：{method}" if method else ""] if piece]
            if phase and pieces:
                eval_lines += f"- {phase}：{'；'.join(pieces)}\n"
        sections.append(f"## 十、评估周期\n{eval_lines}\n")

        sections.append("## 十一、教师建议\n教师点评由教师端补充，不在自动报告中编造。\n")

        return "\n".join(sections).strip() + "\n"

    def _has_meaningful_data(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(self._clean_text(value))
        if isinstance(value, (int, float, bool)):
            return True
        if isinstance(value, list):
            return any(self._has_meaningful_data(item) for item in value)
        if isinstance(value, dict):
            return any(self._has_meaningful_data(item) for item in value.values())
        return bool(value)

    def _standardize_report(self, db: Session, report: CareerReport) -> CareerReport:
        if not report.content_json or report.status in {"edited", "polished"}:
            return report

        normalized_content = self._normalize_report_content(report.content_json)
        normalized_markdown = self._build_standard_markdown(normalized_content)
        if report.content_json != normalized_content or report.markdown_content != normalized_markdown:
            report.content_json = normalized_content
            report.markdown_content = normalized_markdown
            db.commit()
            db.refresh(report)
        return report

    def _check_evidence_sufficiency(self, latest_ocr: dict, match_result: dict) -> list[str]:
        """Return list of missing evidence descriptions; empty means sufficient."""
        missing: list[str] = []
        if not match_result or not match_result.get("dimensions"):
            missing.append("匹配结果维度数据为空，无法生成评分分析")
        # OCR missing is a warning but doesn't block report generation
        return missing

    async def generate_report(
        self,
        db: Session,
        student_id: int,
        job_code: str,
        analysis_run_id: int | None = None,
        profile_version_id: int | None = None,
        match_result_id: int | None = None,
    ) -> dict:
        student = db.get(Student, student_id)
        student_profile = db.scalar(select(StudentProfile).where(StudentProfile.student_id == student_id))
        job_profile = db.scalar(select(JobProfile).where(JobProfile.job_code == job_code))
        if not student or not student_profile or not job_profile:
            raise ValueError("生成报告前请先准备学生画像与岗位画像")
        latest_ocr = self._latest_resume_ocr(db, student.user_id, job_profile, student_profile.source_summary)
        student_name = self._student_name_from_ocr(student, latest_ocr)

        # Resolve context IDs from analysis_run if not explicitly provided
        if analysis_run_id and not (profile_version_id or match_result_id):
            run = db.get(AnalysisRun, analysis_run_id)
            if run:
                if not profile_version_id:
                    profile_version_id = run.profile_version_id
                if not match_result_id:
                    match_result_id = run.match_result_id

        # If analysis_run_id is provided, look for a report bound to that specific run
        # to support multiple reports per student+job (different analysis runs)
        if analysis_run_id:
            report = db.scalar(
                select(CareerReport)
                .where(CareerReport.student_id == student_id)
                .where(CareerReport.target_job_code == job_code)
                .where(CareerReport.analysis_run_id == analysis_run_id)
            )
        else:
            report = db.scalar(
                select(CareerReport)
                .where(CareerReport.student_id == student_id)
                .where(CareerReport.target_job_code == job_code)
                .where(CareerReport.analysis_run_id == None)
            )
        if (
            report
            and report.content_json
            and report.markdown_content
            and report.updated_at
            and student_profile.updated_at
            and report.updated_at >= student_profile.updated_at
            and self._report_matches_current_resume(report, student_name, latest_ocr)
            and "学生基本情况" in report.markdown_content
        ):
            return {
                "report_id": report.id,
                "student_id": student_id,
                "job_code": job_code,
                "content": report.content_json,
                "markdown_content": report.markdown_content,
                "status": report.status,
                "path_recommendation_id": report.path_recommendation_id,
                "profile_version_id": report.profile_version_id,
                "match_result_id": report.match_result_id,
                "analysis_run_id": report.analysis_run_id,
            }
        match_result = self.matching_service.analyze_match(db, student_id, job_code)
        actual_match_result_id = match_result_id or match_result.get("match_result_id") if isinstance(match_result, dict) else match_result_id
        path_result = await self.career_path_service.plan_path(
            db, student_id, job_code,
            profile_version_id=profile_version_id,
            match_result_id=actual_match_result_id,
            analysis_run_id=analysis_run_id,
        )

        # Evidence sufficiency check — return insufficient_data before calling LLM
        evidence_gaps = self._check_evidence_sufficiency(latest_ocr, match_result)
        if evidence_gaps:
            insufficient_content = {
                "student_summary": {},
                "resume_summary": {},
                "capability_profile": {},
                "target_job_analysis": {},
                "matching_analysis": {},
                "gap_analysis": {},
                "career_path": {},
                "short_term_plan": {},
                "mid_term_plan": {},
                "evaluation_cycle": {},
                "teacher_comments": {"status": "insufficient_data"},
            }
            insufficient_md = (
                "# CareerPilot 职业发展报告\n\n"
                "> **资料不足，无法生成完整报告**\n\n"
                "以下关键证据缺失，请补充后重试：\n"
            )
            for gap in evidence_gaps:
                insufficient_md += f"- {gap}\n"
            insufficient_md += (
                "\n建议：请先上传简历并完成 OCR 解析，确保匹配分析数据可用。"
            )
            # Persist insufficient_data status so frontend can react
            if not report:
                report = CareerReport(student_id=student_id, target_job_code=job_code)
                db.add(report)
                db.flush()
            report.content_json = insufficient_content
            report.markdown_content = insufficient_md
            report.status = "insufficient_data"
            db.commit()
            return {
                "report_id": report.id,
                "student_id": student_id,
                "job_code": job_code,
                "content": report.content_json,
                "markdown_content": report.markdown_content,
                "status": report.status,
                "path_recommendation_id": report.path_recommendation_id,
                "profile_version_id": report.profile_version_id,
                "match_result_id": report.match_result_id,
                "analysis_run_id": report.analysis_run_id,
            }

        # Look up the PathRecommendation that plan_path just created/updated
        path_rec = db.scalar(
            select(PathRecommendation)
            .where(PathRecommendation.student_id == student_id)
            .where(PathRecommendation.target_job_code == job_code)
        )

        # Get profile version snapshot for grade info
        student_grade = student.grade or ""
        if profile_version_id:
            pv = db.get(ProfileVersion, profile_version_id)
            if pv and pv.snapshot_json:
                snapshot = pv.snapshot_json if isinstance(pv.snapshot_json, dict) else {}
                student_grade = snapshot.get("grade", student_grade)

        llm_result = await self.llm_provider.generate_report(
            {
                "student_name": student_name,
                "student_major": self._student_major_from_ocr(student, student_profile, latest_ocr),
                "student_grade": student_grade,
                "resume_intent": self._resume_intent_from_ocr(latest_ocr),
                "resume_evidence": self._resume_evidence_from_ocr(latest_ocr),
                "student_profile": {
                    "skills": student_profile.skills_json,
                    "certificates": student_profile.certificates_json,
                    "capability_scores": student_profile.capability_scores,
                    "completeness_score": student_profile.completeness_score,
                    "competitiveness_score": student_profile.competitiveness_score,
                    "projects": student_profile.projects_json,
                    "internships": student_profile.internships_json,
                },
                "job_profile": {
                    "job_code": job_profile.job_code,
                    "title": job_profile.title,
                    "summary": job_profile.summary,
                    "skill_requirements": job_profile.skill_requirements,
                    "certificate_requirements": job_profile.certificate_requirements,
                },
                "job_title": job_profile.title,
                "match_result": match_result,
                "path_result": path_result,
            }
        )
        # Use the same run-scoped lookup for the post-LLM write
        if analysis_run_id:
            report = db.scalar(
                select(CareerReport)
                .where(CareerReport.student_id == student_id)
                .where(CareerReport.target_job_code == job_code)
                .where(CareerReport.analysis_run_id == analysis_run_id)
            )
        else:
            report = db.scalar(
                select(CareerReport)
                .where(CareerReport.student_id == student_id)
                .where(CareerReport.target_job_code == job_code)
                .where(CareerReport.analysis_run_id == None)
            )
        if not report:
            report = CareerReport(student_id=student_id, target_job_code=job_code)
            db.add(report)
            db.flush()
        if path_rec:
            report.path_recommendation_id = path_rec.id
        report.profile_version_id = profile_version_id
        report.match_result_id = actual_match_result_id
        report.analysis_run_id = analysis_run_id
        normalized_content = self._normalize_report_content(llm_result["content"])
        report.content_json = normalized_content
        report.markdown_content = self._build_standard_markdown(normalized_content)
        report.status = "generated"

        # If analysis_run_id provided, update AnalysisRun.report_id
        if analysis_run_id:
            run = db.get(AnalysisRun, analysis_run_id)
            if run:
                run.report_id = report.id

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
        self._sync_growth_tasks(db, report.id, student_id, report.content_json)
        db.commit()
        return {
            "report_id": report.id,
            "student_id": student_id,
            "job_code": job_code,
            "content": report.content_json,
            "markdown_content": report.markdown_content,
            "status": report.status,
            "path_recommendation_id": report.path_recommendation_id,
            "profile_version_id": report.profile_version_id,
            "match_result_id": report.match_result_id,
            "analysis_run_id": report.analysis_run_id,
        }

    def _latest_resume_ocr(self, db: Session, owner_id: int, job_profile: JobProfile | None = None, source_summary: str = "") -> dict:
        uploads = list(db.scalars(
            select(UploadedFile)
            .where(UploadedFile.owner_id == owner_id)
            .where(UploadedFile.file_type == "resume")
            .order_by(UploadedFile.created_at.desc(), UploadedFile.id.desc())
            .limit(8)
        ).all())
        if not uploads:
            return {}
        if source_summary:
            source_names = {item.strip() for item in source_summary.split("；") if item.strip()}
            sourced_uploads = [upload for upload in uploads if upload.file_name in source_names]
            if sourced_uploads:
                uploads = sourced_uploads
        if job_profile:
            ranked = []
            for uploaded in uploads:
                ocr = (uploaded.meta_json or {}).get("ocr_result") or (uploaded.meta_json or {}).get("ocr")
                if isinstance(ocr, dict):
                    ranked.append((_resume_relevance(ocr, job_profile), ocr))
            ranked.sort(key=lambda item: item[0], reverse=True)
            if ranked and ranked[0][0] > 0:
                return ranked[0][1]

        uploaded = uploads[0]
        if not uploaded.meta_json:
            return {}
        ocr = uploaded.meta_json.get("ocr_result") or uploaded.meta_json.get("ocr")
        return ocr if isinstance(ocr, dict) else {}

    def _report_matches_current_resume(self, report: CareerReport, student_name: str, ocr: dict) -> bool:
        raw_text = self._ocr_raw_text(ocr)
        if raw_text and student_name and student_name not in report.markdown_content:
            return False
        intent_job = self._resume_intent_from_ocr(ocr).get("job")
        if intent_job and intent_job not in report.markdown_content and report.target_job_code == "J-FE-001":
            return False
        return True

    def _ocr_structured(self, ocr: dict) -> dict:
        structured = ocr.get("structured_json") if isinstance(ocr, dict) else {}
        return structured if isinstance(structured, dict) else {}

    def _ocr_raw_text(self, ocr: dict) -> str:
        raw_text = ocr.get("raw_text") if isinstance(ocr, dict) else ""
        return raw_text if isinstance(raw_text, str) else ""

    def _student_name_from_ocr(self, student: Student, ocr: dict) -> str:
        structured = self._ocr_structured(ocr)
        structured_name = str(structured.get("name") or "").strip()
        if structured_name and structured_name != "未知学生":
            return structured_name

        for line in self._ocr_raw_text(ocr).splitlines():
            candidate = line.strip()
            if re.fullmatch(r"[\u4e00-\u9fa5·]{2,8}", candidate):
                return candidate

        if hasattr(student, "user") and student.user and student.user.full_name:
            return student.user.full_name
        return f"学生{student.id}"

    def _student_major_from_ocr(self, student: Student, student_profile: StudentProfile, ocr: dict) -> str:
        structured = self._ocr_structured(ocr)
        major = str(structured.get("major") or "").strip()
        if major:
            return major
        if student_profile.source_summary:
            return student_profile.source_summary
        return student.major

    def _resume_intent_from_ocr(self, ocr: dict) -> dict:
        raw_text = self._ocr_raw_text(ocr)
        intent: dict[str, str] = {}
        patterns = {
            "job": r"意向岗位[:：\s]*([^\n]+)",
            "city": r"意向城市[:：\s]*([^\n]+)",
            "salary": r"期望薪资[:：\s]*([^\n]+)",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, raw_text)
            if match:
                value = re.split(r"\s{2,}|意向城市|期望薪资|求职类型", match.group(1).strip())[0].strip(" ：:")
                if value:
                    intent[key] = value
        return intent

    def _resume_evidence_from_ocr(self, ocr: dict) -> dict:
        structured = self._ocr_structured(ocr)
        return {
            "name": structured.get("name"),
            "major": structured.get("major"),
            "skills": structured.get("skills") or [],
            "projects": structured.get("projects") or [],
            "internships": structured.get("internships") or [],
            "raw_excerpt": self._ocr_raw_text(ocr)[:1200],
        }

    def _sync_growth_tasks(self, db: Session, report_id: int, student_id: int, content: dict) -> None:
        short_term = content.get("short_term_plan", {}).get("items", [])
        mid_term = content.get("mid_term_plan", {}).get("items", [])
        for item in short_term:
            db.add(
                GrowthTask(
                    student_id=student_id,
                    report_id=report_id,
                    title=item if isinstance(item, str) else str(item),
                    phase="short_term",
                    metric="阶段技能覆盖率提升",
                    status="pending",
                )
            )
        for item in mid_term:
            db.add(
                GrowthTask(
                    student_id=student_id,
                    report_id=report_id,
                    title=item if isinstance(item, str) else str(item),
                    phase="mid_term",
                    metric="项目/实习成果达成",
                    status="pending",
                )
            )

    def get_report(self, db: Session, report_id: int) -> CareerReport:
        report = db.get(CareerReport, report_id)
        if not report:
            raise ValueError("报告不存在")
        return self._standardize_report(db, report)

    def save_report(self, db: Session, report_id: int, markdown_content: str) -> None:
        report = self.get_report(db, report_id)
        report.markdown_content = markdown_content
        report.status = "edited"
        version_count = len(list(db.scalars(select(ReportVersion).where(ReportVersion.report_id == report.id)).all()))
        db.add(
            ReportVersion(
                report_id=report.id,
                version_no=version_count + 1,
                content_json=report.content_json,
                markdown_content=markdown_content,
                editor_notes="手动保存",
            )
        )
        db.commit()

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
            "path_recommendation_id": report.path_recommendation_id,
            "profile_version_id": report.profile_version_id,
            "match_result_id": report.match_result_id,
            "analysis_run_id": report.analysis_run_id,
        }

    def check_completeness(self, db: Session, report_id: int) -> dict:
        try:
            report = self.get_report(db, report_id)
            missing = []
            for section in self.REQUIRED_SECTIONS:
                section_data = report.content_json.get(section)
                if not self._has_meaningful_data(section_data):
                    missing.append(section)
            suggestions = []
            if "matching_analysis" in missing:
                suggestions.append("补充人岗匹配分析。")
            if "career_path" in missing:
                suggestions.append("补充职业路径规划。")
            if "short_term_plan" in missing or "mid_term_plan" in missing:
                suggestions.append("补充短期、中期行动计划。")
            if "evaluation_cycle" in missing:
                suggestions.append("补充评估周期与指标。")
            if "teacher_comments" in missing:
                suggestions.append("教师建议区域待补充（可由教师点评后生成）。")
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
