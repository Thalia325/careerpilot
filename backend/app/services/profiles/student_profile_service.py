from __future__ import annotations

import logging
import re
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.integrations.llm.providers import BaseLLMProvider
from app.models import Student, StudentProfile, StudentProfileEvidence, ProfileVersion, UploadedFile
from app.schemas.profile import ManualStudentInput
from app.services.ingestion.file_ingestion import FileIngestionService

logger = logging.getLogger(__name__)


def _ocr_needs_refresh(ocr: dict | None) -> bool:
    if not ocr:
        return True
    text = str(ocr.get("raw_text") or "").lstrip()
    if not text:
        return False
    head = text[:2000]
    structured = ocr.get("structured_json") or {}
    return (
        head.startswith("%PDF")
        or head.startswith("PK")
        or "\x00" in head
        or head.count("\ufffd") > 10
        or (
            not structured.get("skills")
            and bool(re.search(r"(?i)p\s*y\s*t\s*h\s*o\s*n|j\s*a\s*v\s*a|s\s*q\s*l|e\s*x\s*c\s*e\s*l|数\s*据\s*分\s*析", head))
        )
    )


class StudentProfileService:
    def __init__(self, llm_provider: BaseLLMProvider, file_service: FileIngestionService) -> None:
        self.llm_provider = llm_provider
        self.file_service = file_service

    async def generate_profile(
        self,
        db: Session,
        student_id: int,
        uploaded_file_ids: list[int],
        manual_input: Optional[ManualStudentInput],
        mode: str = "current_resume",
    ) -> dict:
        student = db.get(Student, student_id)
        if not student:
            raise ValueError("学生不存在")

        if not uploaded_file_ids and not manual_input:
            raise ValueError("uploaded_file_ids 和 manual_input 不能同时为空")

        merged = {
            "major": "",  # 初始为空，优先使用OCR解析的专业
            "skills": [],
            "certificates": [],
            "projects": [],
            "internships": [],
            "self_introduction": manual_input.self_introduction if manual_input else "",
            "preferences": manual_input.preferences if manual_input else {},
            "source_summary": "",
        }
        evidence_items: list[dict] = []
        file_summaries: list[dict] = []
        uploaded_files = [db.get(UploadedFile, fid) for fid in uploaded_file_ids]
        uploaded_files = [f for f in uploaded_files if f]

        # Apply mode filtering: only use explicitly provided files
        if uploaded_files and mode == "current_resume":
            resume_files = [f for f in uploaded_files if f.file_type == "resume"]
            if resume_files:
                latest_resume = sorted(resume_files, key=lambda f: (f.created_at, f.id), reverse=True)[0]
                uploaded_files = [latest_resume]
            else:
                # No resume-type files: use only the first file as "current"
                uploaded_files = [uploaded_files[0]]
        # mode == "merged_materials": use all provided files

        processed_any_file = False
        file_errors: list[str] = []

        for uploaded in uploaded_files:
            try:
                ocr = uploaded.meta_json.get("ocr") if uploaded.meta_json else None
                if _ocr_needs_refresh(ocr):
                    document_type = "resume" if uploaded.file_type == "resume" else uploaded.file_type
                    ocr = await self.file_service.parse_uploaded_file(db, uploaded.id, document_type)
                structured = ocr["structured_json"]
                processed_any_file = True
                # 优先使用OCR解析的专业信息，覆盖学生基本信息中的专业
                if structured.get("major"):
                    merged["major"] = structured.get("major")
                    evidence_items.append({
                        "source": uploaded.file_name,
                        "excerpt": f"OCR 解析专业：{structured.get('major')}",
                        "confidence": 0.95
                    })
                merged["skills"].extend(structured.get("skills", []))
                merged["certificates"].extend(structured.get("certificates", []))
                merged["projects"].extend(structured.get("projects", []))
                merged["internships"].extend(structured.get("internships", []))
                if structured.get("target_job"):
                    student.career_goal = structured.get("target_job")
                    merged["preferences"]["target_job"] = structured.get("target_job")
                    evidence_items.append({
                        "source": uploaded.file_name,
                        "excerpt": f"OCR 解析意向岗位：{structured.get('target_job')}",
                        "confidence": 0.9,
                    })
                merged["source_summary"] += f"{uploaded.file_name}；"
                file_summaries.append({
                    "file_id": uploaded.id,
                    "file_name": uploaded.file_name,
                    "file_type": uploaded.file_type,
                    "summary": f"{uploaded.file_name}（{uploaded.file_type}），"
                               f"提取技能 {len(structured.get('skills', []))} 项，"
                               f"项目 {len(structured.get('projects', []))} 个，"
                               f"实习 {len(structured.get('internships', []))} 段",
                })
                for skill in structured.get("skills", []):
                    evidence_items.append({"source": uploaded.file_name, "excerpt": f"OCR 提取技能：{skill}", "confidence": 0.9})
            except Exception as e:
                logger.error("Failed to process uploaded file %s: %s", uploaded.id, str(e))
                file_errors.append(f"{uploaded.file_name}: {str(e)}")
                continue

        if uploaded_files and not processed_any_file and not manual_input:
            detail = "；".join(file_errors) if file_errors else "未能从上传材料中提取有效内容"
            raise ValueError(f"上传材料解析失败：{detail}")

        # 如果OCR没有解析到专业信息，才使用学生基本信息中的专业
        if not merged["major"] and student.major:
            merged["major"] = student.major
            evidence_items.append({
                "source": "学生基本信息",
                "excerpt": f"学生基本信息专业：{student.major}",
                "confidence": 0.7
            })

        if manual_input:
            merged["skills"].extend(manual_input.skills)
            merged["certificates"].extend(manual_input.certificates)
            merged["projects"].extend(manual_input.projects)
            merged["internships"].extend(manual_input.internships)
            merged["source_summary"] += "手动录入；"
            if manual_input.target_job:
                student.career_goal = manual_input.target_job
        merged["skills"] = sorted(set(merged["skills"]))
        merged["certificates"] = sorted(set(merged["certificates"]))

        # 传递给LLM的数据中，明确标注专业来源
        llm_payload = {
            **merged,
            "major_source": "OCR解析" if merged["major"] else "学生基本信息",
        }
        llm_result = await self.llm_provider.generate_student_profile(llm_payload)
        profile = db.scalar(select(StudentProfile).where(StudentProfile.student_id == student_id))
        if not profile:
            profile = StudentProfile(student_id=student_id)
            db.add(profile)
            db.flush()
        profile.source_summary = llm_result["source_summary"]
        profile.skills_json = llm_result["skills"]
        profile.certificates_json = llm_result["certificates"]
        profile.projects_json = llm_result.get("projects", [])
        profile.internships_json = llm_result.get("internships", [])
        profile.capability_scores = llm_result["capability_scores"]
        profile.completeness_score = llm_result["completeness_score"]
        profile.competitiveness_score = llm_result["competitiveness_score"]
        profile.willingness_json = llm_result["willingness"]
        profile.evidence_summary = {"sources": merged["source_summary"]}
        db.execute(delete(StudentProfileEvidence).where(StudentProfileEvidence.student_profile_id == profile.id))
        combined_evidence = evidence_items + llm_result["evidence"]
        for evidence in combined_evidence:
            db.add(
                StudentProfileEvidence(
                    student_profile_id=profile.id,
                    evidence_type="profile",
                    source=evidence["source"],
                    excerpt=evidence["excerpt"],
                    confidence=evidence["confidence"],
                )
            )
        db.commit()

        existing = db.scalar(
            select(ProfileVersion)
            .where(ProfileVersion.student_id == student_id)
            .order_by(ProfileVersion.version_no.desc())
            .limit(1)
        )
        next_version = (existing.version_no + 1) if existing else 1

        snapshot = {
            "source_summary": profile.source_summary,
            "skills": profile.skills_json,
            "certificates": profile.certificates_json,
            "projects": profile.projects_json,
            "internships": profile.internships_json,
            "capability_scores": profile.capability_scores,
            "completeness_score": profile.completeness_score,
            "competitiveness_score": profile.competitiveness_score,
            "willingness": profile.willingness_json,
            "uploaded_file_ids": uploaded_file_ids,
            "mode": mode,
        }
        pv = ProfileVersion(
            student_id=student_id,
            version_no=next_version,
            source_files=merged["source_summary"],
            uploaded_file_ids=uploaded_file_ids,
            file_summaries_json=file_summaries,
            snapshot_json=snapshot,
            evidence_snapshot_json=combined_evidence,
        )
        db.add(pv)
        db.commit()
        db.refresh(pv)

        return {
            "student_id": student_id,
            "source_summary": profile.source_summary,
            "skills": profile.skills_json,
            "certificates": profile.certificates_json,
            "projects": profile.projects_json,
            "internships": profile.internships_json,
            "capability_scores": profile.capability_scores,
            "completeness_score": profile.completeness_score,
            "competitiveness_score": profile.competitiveness_score,
            "willingness": profile.willingness_json,
            "evidence": combined_evidence,
            "profile_version_id": pv.id,
        }

    def get_profile(self, db: Session, student_id: int) -> Optional[dict]:
        profile = db.scalar(select(StudentProfile).where(StudentProfile.student_id == student_id))
        if not profile:
            return None
        evidence = list(
            db.scalars(select(StudentProfileEvidence).where(StudentProfileEvidence.student_profile_id == profile.id)).all()
        )
        return {
            "student_id": profile.student_id,
            "source_summary": profile.source_summary,
            "skills": profile.skills_json,
            "certificates": profile.certificates_json,
            "projects": profile.projects_json,
            "internships": profile.internships_json,
            "capability_scores": profile.capability_scores,
            "completeness_score": profile.completeness_score,
            "competitiveness_score": profile.competitiveness_score,
            "willingness": profile.willingness_json,
            "evidence": [{"source": item.source, "excerpt": item.excerpt, "confidence": item.confidence} for item in evidence],
        }
