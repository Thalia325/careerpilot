from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.graph.providers import MockGraphProvider, Neo4jGraphProvider
from app.integrations.llm.providers import ErnieLLMProvider, MockLLMProvider
from app.integrations.ocr.providers import MockOCRProvider, PaddleOCRProvider
from app.integrations.ragflow.providers import MockRAGProvider, RAGFlowProvider
from app.integrations.storage.providers import LocalStorageProvider, MinIOStorageProvider
from app.models import JobPosting, JobProfile
from app.services.agents.controller import MainControllerAgent
from app.services.agents.job_profile_agent import JobProfileAgent
from app.services.agents.report_agent import ReportGenerationAgent
from app.services.agents.resume_agent import ResumeParsingAgent
from app.services.agents.tracking_agent import TrackingAgent
from app.services.auth_service import ensure_demo_users
from app.services.ingestion.file_ingestion import FileIngestionService
from app.services.ingestion.job_import_service import JobImportService
from app.services.interviews.mock_interview_service import MockInterviewService
from app.services.matching.matching_service import MatchingService
from app.services.paths.career_path_service import CareerPathService
from app.services.paths.graph_query_service import GraphQueryService
from app.services.profiles.student_profile_service import StudentProfileService
from app.services.reference import (
    load_job_graph_seed,
    load_job_postings_dataset,
    resolve_job_dataset_path,
)
from app.services.reports.report_service import ReportService
from app.services.scheduler.scheduler_service import SchedulerService
from app.services.seed_demo_students import seed_demo_students


@dataclass
class ServiceContainer:
    file_service: FileIngestionService
    job_import_service: JobImportService
    student_profile_service: StudentProfileService
    matching_service: MatchingService
    mock_interview_service: MockInterviewService
    graph_query_service: GraphQueryService
    career_path_service: CareerPathService
    report_service: ReportService
    scheduler_service: SchedulerService
    controller_agent: MainControllerAgent


def _validate_ai_settings(settings) -> None:
    if not settings.strict_ai_providers:
        return
    if settings.llm_provider != "ernie":
        raise RuntimeError("STRICT_AI_PROVIDERS enabled: LLM_PROVIDER must be 'ernie'")
    if settings.ocr_provider != "paddle":
        raise RuntimeError("STRICT_AI_PROVIDERS enabled: OCR_PROVIDER must be 'paddle'")
    if not settings.ernie_access_token:
        raise RuntimeError("STRICT_AI_PROVIDERS enabled: ERNIE credentials are missing")
    if not settings.paddle_ocr_service_url:
        raise RuntimeError("STRICT_AI_PROVIDERS enabled: PADDLE_OCR_SERVICE_URL is missing")
    if not settings.resolved_paddle_ocr_api_key:
        raise RuntimeError("STRICT_AI_PROVIDERS enabled: PADDLE_OCR_API_KEY is missing")


def _create_llm_provider(settings):
    if settings.llm_provider == "mock":
        return MockLLMProvider()
    return ErnieLLMProvider(
        access_token=settings.ernie_access_token,
        base_url=settings.ernie_aistudio_base_url,
        model=settings.ernie_model,
        allow_job_profile_mock_fallback=(
            settings.job_profile_mock_fallback_enabled and not settings.strict_ai_providers
        ),
    )


def _create_ocr_provider(settings):
    if settings.ocr_provider == "mock":
        return MockOCRProvider()
    return PaddleOCRProvider(
        settings.paddle_ocr_service_url,
        settings.resolved_paddle_ocr_api_key,
        timeout_seconds=settings.paddle_ocr_timeout_seconds,
        max_retries=settings.paddle_ocr_max_retries,
        retry_base_delay_seconds=settings.paddle_ocr_retry_base_delay_seconds,
    )


def _create_rag_provider(settings):
    if settings.ragflow_provider == "mock":
        return MockRAGProvider()
    return RAGFlowProvider(settings.ragflow_base_url, settings.ragflow_api_key)


def _create_graph_provider(settings):
    if settings.graph_provider == "mock":
        return MockGraphProvider()
    return Neo4jGraphProvider(settings.neo4j_uri, settings.neo4j_username, settings.neo4j_password)


def _create_storage_provider(settings):
    if settings.storage_provider == "local":
        return LocalStorageProvider(settings.local_storage_path)
    return MinIOStorageProvider(
        settings.minio_endpoint,
        settings.minio_access_key,
        settings.minio_secret_key,
        settings.minio_bucket,
        settings.minio_secure,
    )


def create_service_container() -> ServiceContainer:
    settings = get_settings()
    _validate_ai_settings(settings)
    llm_provider = _create_llm_provider(settings)
    ocr_provider = _create_ocr_provider(settings)
    rag_provider = _create_rag_provider(settings)
    graph_provider = _create_graph_provider(settings)
    storage_provider = _create_storage_provider(settings)

    file_service = FileIngestionService(storage_provider, ocr_provider)
    job_import_service = JobImportService(llm_provider, rag_provider, graph_provider)

    student_profile_service = StudentProfileService(llm_provider, file_service)
    matching_service = MatchingService()
    mock_interview_service = MockInterviewService(matching_service)
    graph_query_service = GraphQueryService(graph_provider)
    career_path_service = CareerPathService(graph_query_service)
    report_service = ReportService(llm_provider, matching_service, career_path_service, file_service)
    scheduler_service = SchedulerService(settings.scheduler_timezone)

    resume_agent = ResumeParsingAgent(file_service)
    job_profile_agent = JobProfileAgent(job_import_service)
    tracking_agent = TrackingAgent(scheduler_service)
    report_agent = ReportGenerationAgent(report_service)
    controller_agent = MainControllerAgent(resume_agent, job_profile_agent, tracking_agent, report_agent)
    return ServiceContainer(
        file_service=file_service,
        job_import_service=job_import_service,
        student_profile_service=student_profile_service,
        matching_service=matching_service,
        mock_interview_service=mock_interview_service,
        graph_query_service=graph_query_service,
        career_path_service=career_path_service,
        report_service=report_service,
        scheduler_service=scheduler_service,
        controller_agent=controller_agent,
    )


def get_user_llm_provider(db, user_id: int):
    settings = get_settings()
    _validate_ai_settings(settings)
    if settings.llm_provider == "mock":
        return MockLLMProvider()
    return ErnieLLMProvider(
        access_token=settings.ernie_access_token,
        base_url=settings.ernie_aistudio_base_url,
        model=settings.ernie_model,
        allow_job_profile_mock_fallback=(
            settings.job_profile_mock_fallback_enabled and not settings.strict_ai_providers
        ),
    )


async def initialize_demo_data(db: Session, container: ServiceContainer) -> None:
    settings = get_settings()
    ensure_demo_users(db)
    seed_demo_students(db)
    await container.job_import_service.graph_provider.load_seed(load_job_graph_seed())

    dataset_path = resolve_job_dataset_path()
    should_import_dataset = dataset_path.exists() and (
        bool(settings.job_dataset_path) or dataset_path.name != "sample_jobs.csv"
    )
    dataset_rows = load_job_postings_dataset(str(dataset_path)) if should_import_dataset else []

    existing_posting_count = db.scalar(select(func.count()).select_from(JobPosting)) or 0
    sampled_industries = [
        item
        for item in db.scalars(select(JobPosting.industry).limit(300)).all()
        if isinstance(item, str)
    ]
    has_dirty_postings = any(any(char.isdigit() for char in industry) for industry in sampled_industries)
    if dataset_rows and (existing_posting_count != len(dataset_rows) or has_dirty_postings):
        container.job_import_service.sync_postings_snapshot(db, dataset_rows)

    has_profiles = db.scalar(select(JobProfile.id).limit(1))
    if not has_profiles:
        if dataset_rows:
            await container.job_import_service.reimport_dataset(
                db,
                dataset_rows,
                clear_existing=False,
            )
        else:
            await container.job_import_service.seed_templates(db)
    elif dataset_rows:
        linked_profile_count = db.scalar(
            select(func.count(func.distinct(JobProfile.job_code)))
            .select_from(JobProfile)
            .join(JobPosting, JobPosting.job_code == JobProfile.job_code)
        ) or 0
        expected_profile_count = len({row["title"] for row in dataset_rows})
        if linked_profile_count < expected_profile_count:
            await container.job_import_service.generate_aggregated_profiles(db)

    container.job_import_service.ensure_profile_integrity(db)

    profiles = list(db.scalars(select(JobProfile).order_by(JobProfile.title)).all())
    for profile in profiles:
        await container.job_import_service.graph_provider.upsert_job_profile(
            {
                "job_code": profile.job_code,
                "title": profile.title,
                "summary": profile.summary,
                "skill_requirements": profile.skill_requirements,
            }
        )

    if not container.scheduler_service.list_jobs(db):
        container.scheduler_service.create_job(
            db,
            job_name="weekly_growth_review",
            cron_expr="0 9 * * 1",
            job_type="review",
            payload={"student_id": 1, "target_job": "前端开发工程师"},
        )
        container.scheduler_service.create_job(
            db,
            job_name="weekly_resource_push",
            cron_expr="0 10 * * 3",
            job_type="resource_push",
            payload={"student_id": 1, "target_job": "前端开发工程师"},
        )
