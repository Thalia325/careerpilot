from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.graph.providers import BaseGraphProvider
from app.integrations.llm.providers import BaseLLMProvider
from app.integrations.ragflow.providers import BaseRAGProvider
from app.models import CertificateRequired, Company, JobPosting, JobProfile, KnowledgeDocument
from app.services.reference import find_best_template, load_job_profile_templates

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
    def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": row["title"].strip(),
            "location": row["location"].strip(),
            "salary_range": row["salary_range"].strip(),
            "company_name": row["company_name"].strip(),
            "industry": row["industry"].strip(),
            "company_size": row["company_size"].strip(),
            "ownership_type": row["ownership_type"].strip(),
            "job_code": row["job_code"].strip(),
            "description": row["description"].strip(),
            "company_intro": row["company_intro"].strip(),
        }

    def _upsert_company(self, db: Session, row: dict[str, Any]) -> Company:
        company = db.scalar(select(Company).where(Company.name == row["company_name"]))
        if not company:
            try:
                company = Company(
                    name=row["company_name"],
                    industry=row["industry"],
                    size=row["company_size"],
                    ownership_type=row["ownership_type"],
                    description=row["company_intro"],
                )
                db.add(company)
                db.flush()
            except Exception as e:
                logger.error(f"Failed to upsert company {row['company_name']}: {str(e)}")
                db.rollback()
                company = db.scalar(select(Company).where(Company.name == row["company_name"]))
                if not company:
                    raise ValueError(f"Failed to create company: {row['company_name']}") from e
        return company

    async def import_rows(self, db: Session, rows: list[dict[str, Any]], generate_profiles: bool = True) -> list[JobPosting]:
        imported: list[JobPosting] = []
        for raw in rows:
            try:
                row = self.normalize_row(raw)
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
                imported.append(posting)
            except Exception as e:
                logger.error(f"Failed to import row with job_code {raw.get('job_code', 'unknown')}: {str(e)}")
                continue
        db.commit()
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
                db.add(
                    KnowledgeDocument(
                        doc_type="job_profile",
                        title=profile.title,
                        content=f"{profile.summary}\n技能：{', '.join(profile.skill_requirements)}",
                        source_ref=profile.job_code,
                        embedding_status="indexed",
                    )
                )
                await self.rag_provider.index_document(
                    profile.title,
                    f"{profile.summary}\n技能：{', '.join(profile.skill_requirements)}",
                    {"job_code": profile.job_code, "industry": posting.industry},
                )
                await self.graph_provider.upsert_job_profile(
                    {
                        "job_code": profile.job_code,
                        "title": profile.title,
                        "skill_requirements": profile.skill_requirements,
                    }
                )
                generated.append(profile)
            except Exception as e:
                logger.error(f"Failed to generate profile for job_code {posting.job_code}: {str(e)}")
                continue
        db.commit()
        return generated

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
                    "company_intro": "CareerPilot 演示企业，用于比赛环境岗位知识构建。",
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
