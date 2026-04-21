from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.graph.providers import BaseGraphProvider
from app.integrations.llm.providers import BaseLLMProvider
from app.integrations.ragflow.providers import BaseRAGProvider
from app.models import (
    AnalysisRun,
    CareerReport,
    CertificateRequired,
    Company,
    GrowthTask,
    JobPosting,
    JobProfile,
    KnowledgeDocument,
    MatchDimensionScore,
    MatchResult,
    PathRecommendation,
    ReportVersion,
)
from app.services.reference import find_best_template, get_job_dataset_metadata, load_job_profile_templates

logger = logging.getLogger(__name__)


class JobImportService:
    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        rag_provider: BaseRAGProvider,
        graph_provider: BaseGraphProvider,
    ) -> None:
        self.llm_provider = llm_provider
        self.rag_provider = rag_provider
        self.graph_provider = graph_provider

    @staticmethod
    def _clean_text(value: Any) -> str:
        return str(value or "").strip()

    @staticmethod
    def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": JobImportService._clean_text(row.get("title")),
            "location": JobImportService._clean_text(row.get("location")),
            "salary_range": JobImportService._clean_text(row.get("salary_range")),
            "company_name": JobImportService._clean_text(row.get("company_name")),
            "industry": JobImportService._clean_text(row.get("industry")),
            "company_size": JobImportService._clean_text(row.get("company_size")),
            "ownership_type": JobImportService._clean_text(row.get("ownership_type")),
            "job_code": JobImportService._clean_text(row.get("job_code")),
            "description": JobImportService._clean_text(row.get("description")),
            "company_intro": JobImportService._clean_text(row.get("company_intro")),
        }

    def _upsert_company(self, db: Session, row: dict[str, Any]) -> Company:
        company_name = row["company_name"] or "未知企业"
        company = db.scalar(select(Company).where(Company.name == company_name))
        if company:
            return company

        company = Company(
            name=company_name,
            industry=row["industry"],
            size=row["company_size"],
            ownership_type=row["ownership_type"],
            description=row["company_intro"],
        )
        db.add(company)
        db.flush()
        return company

    @staticmethod
    def _aggregate_text(values: list[str], limit: int = 5) -> str:
        result: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if text and text not in result:
                result.append(text)
            if len(result) >= limit:
                break
        return "\n".join(result)

    def _build_profile_payload(self, postings: list[JobPosting]) -> dict[str, Any]:
        representative = postings[0]
        descriptions = [posting.description for posting in postings if posting.description]
        industries = [posting.industry for posting in postings if posting.industry]
        company_names = [posting.company_name for posting in postings if posting.company_name]
        return {
            "job_code": representative.job_code,
            "title": representative.title,
            "description": self._aggregate_text(descriptions, limit=6) or representative.description,
            "company_name": " / ".join(company_names[:3]),
            "industry": "、".join(dict.fromkeys(industries))[:120],
            "posting_count": len(postings),
        }

    def _write_profile(
        self,
        db: Session,
        profile: JobProfile,
        profile_data: dict[str, Any],
    ) -> None:
        profile.title = profile_data["title"]
        profile.summary = profile_data["summary"]
        profile.skill_requirements = profile_data["skill_requirements"]
        profile.certificate_requirements = profile_data["certificate_requirements"]
        profile.innovation_requirements = profile_data["innovation_requirements"]
        profile.learning_requirements = profile_data["learning_requirements"]
        profile.resilience_requirements = profile_data["resilience_requirements"]
        profile.communication_requirements = profile_data["communication_requirements"]
        profile.internship_requirements = profile_data["internship_requirements"]
        profile.capability_scores = profile_data["capability_scores"]
        profile.dimension_weights = profile_data["dimension_weights"]
        profile.explanation_json = profile_data["explanation_json"]

        db.query(CertificateRequired).filter(CertificateRequired.job_profile_id == profile.id).delete()
        for certificate in profile.certificate_requirements:
            db.add(
                CertificateRequired(
                    job_profile_id=profile.id,
                    certificate_name=certificate,
                    reason=profile.explanation_json.get("证书要求", ""),
                )
            )

        db.query(KnowledgeDocument).filter(
            KnowledgeDocument.doc_type == "job_profile",
            KnowledgeDocument.source_ref == profile.job_code,
        ).delete()
        db.add(
            KnowledgeDocument(
                doc_type="job_profile",
                title=profile.title,
                content=f"{profile.summary}\n技能：{', '.join(profile.skill_requirements)}",
                source_ref=profile.job_code,
                embedding_status="indexed",
            )
        )

    async def _index_profile(self, profile: JobProfile, industry: str) -> None:
        content = f"{profile.summary}\n技能：{', '.join(profile.skill_requirements)}"
        await self.rag_provider.index_document(
            profile.title,
            content,
            {"job_code": profile.job_code, "industry": industry},
        )
        await self.graph_provider.upsert_job_profile(
            {
                "job_code": profile.job_code,
                "title": profile.title,
                "summary": profile.summary,
                "skill_requirements": profile.skill_requirements,
            }
        )

    async def import_rows(
        self,
        db: Session,
        rows: list[dict[str, Any]],
        generate_profiles: bool = True,
    ) -> list[JobPosting]:
        imported: list[JobPosting] = []
        for raw in rows:
            try:
                row = self.normalize_row(raw)
                if not row["title"] or not row["job_code"]:
                    continue

                company = self._upsert_company(db, row)
                posting = db.scalar(select(JobPosting).where(JobPosting.job_code == row["job_code"]))
                if not posting:
                    posting = JobPosting(job_code=row["job_code"])
                    db.add(posting)

                posting.title = row["title"]
                posting.location = row["location"]
                posting.salary_range = row["salary_range"]
                posting.company_id = company.id
                posting.company_name = company.name
                posting.industry = row["industry"]
                posting.company_size = row["company_size"]
                posting.ownership_type = row["ownership_type"]
                posting.description = row["description"]
                posting.company_intro = row["company_intro"]
                posting.normalized_json = row

                db.flush()
                db.commit()
                imported.append(posting)
            except Exception as exc:
                db.rollback()
                logger.error("Failed to import row with job_code %s: %s", raw.get("job_code", "unknown"), exc)
                continue

        if generate_profiles:
            await self.generate_profiles(db, [item.job_code for item in imported])
        return imported

    async def generate_profiles(self, db: Session, job_codes: Optional[list[str]] = None) -> list[JobProfile]:
        query = select(JobPosting)
        if job_codes:
            query = query.where(JobPosting.job_code.in_(job_codes))
        postings = list(db.scalars(query).all())
        generated: list[JobProfile] = []
        for posting in postings:
            try:
                payload = {
                    "job_code": posting.job_code,
                    "title": posting.title,
                    "description": posting.description,
                    "company_name": posting.company_name,
                    "industry": posting.industry,
                }
                profile_data = await self.llm_provider.generate_job_profile(payload)
                profile = db.scalar(select(JobProfile).where(JobProfile.job_code == posting.job_code))
                if not profile:
                    profile = JobProfile(job_code=posting.job_code, job_posting_id=posting.id, title=posting.title)
                    db.add(profile)
                    db.flush()
                self._write_profile(db, profile, profile_data)
                await self._index_profile(profile, posting.industry)
                generated.append(profile)
            except Exception as exc:
                logger.error("Failed to generate profile for job_code %s: %s", posting.job_code, exc)
                db.rollback()
                continue
        db.commit()
        return generated

    async def generate_aggregated_profiles(self, db: Session, titles: Optional[list[str]] = None) -> list[JobProfile]:
        postings = list(db.scalars(select(JobPosting).order_by(JobPosting.title, JobPosting.id)).all())
        postings_by_title: dict[str, list[JobPosting]] = {}
        for posting in postings:
            if not posting.title:
                continue
            if titles and posting.title not in titles:
                continue
            postings_by_title.setdefault(posting.title, []).append(posting)

        generated: list[JobProfile] = []
        total_titles = len(postings_by_title)
        for index, (title, grouped_postings) in enumerate(postings_by_title.items(), start=1):
            logger.info(
                "Refreshing aggregated job profile [%s/%s]: %s (%s postings)",
                index,
                total_titles,
                title,
                len(grouped_postings),
            )
            try:
                payload = self._build_profile_payload(grouped_postings)
                representative = grouped_postings[0]
                profile_data = await self.llm_provider.generate_job_profile(payload)
                profile = db.scalar(select(JobProfile).where(JobProfile.title == title))
                if not profile:
                    profile = JobProfile(
                        job_code=representative.job_code,
                        job_posting_id=representative.id,
                        title=title,
                    )
                    db.add(profile)
                    db.flush()
                self._write_profile(db, profile, profile_data)
                await self._index_profile(profile, representative.industry)
                db.commit()
                generated.append(profile)
                logger.info("Refreshed aggregated job profile [%s/%s]: %s", index, total_titles, title)
            except Exception as exc:
                logger.error("Failed to generate aggregated profile for %s: %s", title, exc)
                db.rollback()
                continue
        return generated

    def clear_job_dataset(self, db: Session) -> None:
        for model in (
            MatchDimensionScore,
            GrowthTask,
            ReportVersion,
            CareerReport,
            PathRecommendation,
            MatchResult,
            AnalysisRun,
            CertificateRequired,
            KnowledgeDocument,
            JobProfile,
            JobPosting,
            Company,
        ):
            db.query(model).delete()
        db.commit()

    async def reimport_dataset(
        self,
        db: Session,
        rows: list[dict[str, Any]],
        *,
        clear_existing: bool = True,
    ) -> dict[str, int]:
        if clear_existing:
            self.clear_job_dataset(db)
        imported = await self.import_rows(db, rows, generate_profiles=False)
        profiles = await self.generate_aggregated_profiles(db)
        unique_postings = len({item.job_code for item in imported})
        return {
            "row_count": len(rows),
            "posting_count": unique_postings,
            "profile_count": len(profiles),
        }

    async def seed_templates(self, db: Session) -> None:
        templates = load_job_profile_templates()
        rows = []
        for index, template in enumerate(templates, start=1):
            rows.append(
                {
                    "title": template["title"],
                    "location": "西安",
                    "salary_range": f"{8 + index}-{12 + index}K",
                    "company_name": f"演示企业{index}",
                    "industry": "信息化服务",
                    "company_size": "500-999人",
                    "ownership_type": "民营",
                    "job_code": template["job_code"],
                    "description": f"{template['summary']} 核心能力包括：{', '.join(template['skills'])}",
                    "company_intro": "CareerPilot 演示企业，用于本地调试与流程展示。",
                }
            )
        await self.import_rows(db, rows, generate_profiles=True)

    def list_job_profiles(self, db: Session) -> list[JobProfile]:
        return list(db.scalars(select(JobProfile).order_by(JobProfile.title)).all())

    def search_templates(self, keyword: Optional[str] = None) -> list[dict]:
        templates = load_job_profile_templates()
        if not keyword:
            return templates
        return [item for item in templates if keyword.lower() in item["title"].lower()]

    def infer_template(self, title: str) -> dict:
        return find_best_template(title)

    def build_local_knowledge_base_export(self, db: Session) -> dict[str, Any]:
        posting_rows = list(db.scalars(select(JobPosting).order_by(JobPosting.title, JobPosting.id)).all())
        profiles = list(db.scalars(select(JobProfile).order_by(JobProfile.title, JobProfile.id)).all())
        documents = list(
            db.scalars(
                select(KnowledgeDocument)
                .where(KnowledgeDocument.doc_type == "job_profile")
                .order_by(KnowledgeDocument.title, KnowledgeDocument.id)
            ).all()
        )
        posting_count_by_title: dict[str, int] = {}
        for posting in posting_rows:
            posting_count_by_title[posting.title] = posting_count_by_title.get(posting.title, 0) + 1

        document_by_ref = {item.source_ref: item for item in documents}
        settings = get_settings()
        dataset_metadata = get_job_dataset_metadata(settings.job_dataset_path or None)

        return {
            "meta": {
                "project": settings.project_name,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "dataset": dataset_metadata,
                "submission_note": "A13 本地知识库导出，包含筛选后的岗位数据、聚合岗位画像与知识库文档。",
            },
            "filtered_job_postings": [
                {
                    "job_code": item.job_code,
                    "title": item.title,
                    "location": item.location,
                    "salary_range": item.salary_range,
                    "company_name": item.company_name,
                    "industry": item.industry,
                    "company_size": item.company_size,
                    "ownership_type": item.ownership_type,
                    "description": item.description,
                    "company_intro": item.company_intro,
                    "normalized_json": item.normalized_json,
                }
                for item in posting_rows
            ],
            "job_profiles": [
                {
                    "job_code": item.job_code,
                    "title": item.title,
                    "summary": item.summary,
                    "skill_requirements": item.skill_requirements,
                    "certificate_requirements": item.certificate_requirements,
                    "innovation_requirements": item.innovation_requirements,
                    "learning_requirements": item.learning_requirements,
                    "resilience_requirements": item.resilience_requirements,
                    "communication_requirements": item.communication_requirements,
                    "internship_requirements": item.internship_requirements,
                    "capability_scores": item.capability_scores,
                    "dimension_weights": item.dimension_weights,
                    "explanation_json": item.explanation_json,
                    "posting_count": posting_count_by_title.get(item.title, 0),
                    "embedding_status": document_by_ref.get(item.job_code).embedding_status if document_by_ref.get(item.job_code) else "pending",
                }
                for item in profiles
            ],
            "knowledge_documents": [
                {
                    "doc_type": item.doc_type,
                    "title": item.title,
                    "content": item.content,
                    "source_ref": item.source_ref,
                    "embedding_status": item.embedding_status,
                }
                for item in documents
            ],
        }

    def export_local_knowledge_base(self, db: Session, output_path: str | Path | None = None) -> dict[str, Any]:
        settings = get_settings()
        export_dir = settings.export_path / "knowledge_base"
        export_dir.mkdir(parents=True, exist_ok=True)
        target_path = Path(output_path) if output_path else export_dir / "a13_local_knowledge_base.json"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        payload = self.build_local_knowledge_base_export(db)
        target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "path": str(target_path),
            "posting_count": len(payload["filtered_job_postings"]),
            "profile_count": len(payload["job_profiles"]),
            "document_count": len(payload["knowledge_documents"]),
        }
