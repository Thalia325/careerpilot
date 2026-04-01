from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.integrations.llm.providers import BaseLLMProvider
from app.models import Student, StudentProfile, StudentProfileEvidence, UploadedFile
from app.schemas.profile import ManualStudentInput
from app.services.ingestion.file_ingestion import FileIngestionService

logger = logging.getLogger(__name__)


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
    ) -> dict:
        student = db.get(Student, student_id)
        if not student:
            raise ValueError("学生不存在")
        merged = {
            "skills": [],
            "certificates": [],
            "projects": [],
            "internships": [],
            "self_introduction": manual_input.self_introduction if manual_input else "",
            "preferences": manual_input.preferences if manual_input else {},
            "source_summary": "",
        }
        evidence_items: list[dict] = []
        for uploaded_file_id in uploaded_file_ids:
            try:
                uploaded = db.get(UploadedFile, uploaded_file_id)
                if not uploaded:
                    logger.warning(f"Uploaded file {uploaded_file_id} not found, skipping")
                    continue
                ocr = uploaded.meta_json.get("ocr") if uploaded.meta_json else None
                if not ocr:
                    document_type = "resume" if uploaded.file_type == "resume" else uploaded.file_type
                    ocr = await self.file_service.parse_uploaded_file(db, uploaded_file_id, document_type)
                structured = ocr["structured_json"]
                merged["skills"].extend(structured.get("skills", []))
                merged["certificates"].extend(structured.get("certificates", []))
                merged["projects"].extend(structured.get("projects", []))
                merged["internships"].extend(structured.get("internships", []))
                merged["source_summary"] += f"{uploaded.file_name}；"
                for skill in structured.get("skills", []):
                    evidence_items.append({"source": uploaded.file_name, "excerpt": f"OCR 提取技能：{skill}", "confidence": 0.9})
            except Exception as e:
                logger.error(f"Failed to process uploaded file {uploaded_file_id}: {str(e)}")
                continue
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
        llm_result = await self.llm_provider.generate_student_profile(merged)
        profile = db.scalar(select(StudentProfile).where(StudentProfile.student_id == student_id))
        if not profile:
            profile = StudentProfile(student_id=student_id)
            db.add(profile)
            db.flush()
        profile.source_summary = llm_result["source_summary"]
        profile.skills_json = llm_result["skills"]
        profile.certificates_json = llm_result["certificates"]
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
        return {
            "student_id": student_id,
            "source_summary": profile.source_summary,
            "skills": profile.skills_json,
            "certificates": profile.certificates_json,
            "capability_scores": profile.capability_scores,
            "completeness_score": profile.completeness_score,
            "competitiveness_score": profile.competitiveness_score,
            "willingness": profile.willingness_json,
            "evidence": combined_evidence,
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
            "capability_scores": profile.capability_scores,
            "completeness_score": profile.completeness_score,
            "competitiveness_score": profile.competitiveness_score,
            "willingness": profile.willingness_json,
            "evidence": [{"source": item.source, "excerpt": item.excerpt, "confidence": item.confidence} for item in evidence],
        }
