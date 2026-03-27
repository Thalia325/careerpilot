from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.graph.providers import MockGraphProvider, Neo4jGraphProvider
from app.integrations.llm.providers import ErnieLLMProvider, MockLLMProvider
from app.integrations.ocr.providers import MockOCRProvider, PaddleOCRProvider
from app.integrations.ragflow.providers import MockRAGProvider, RAGFlowProvider
from app.integrations.storage.providers import LocalStorageProvider, MinIOStorageProvider
from app.models import JobProfile
from app.services.agents.controller import MainControllerAgent
from app.services.agents.job_profile_agent import JobProfileAgent
from app.services.agents.report_agent import ReportGenerationAgent
from app.services.agents.resume_agent import ResumeParsingAgent
from app.services.agents.tracking_agent import TrackingAgent
from app.services.auth_service import ensure_demo_users
from app.services.ingestion.file_ingestion import FileIngestionService
from app.services.ingestion.job_import_service import JobImportService
from app.services.matching.matching_service import MatchingService
from app.services.paths.career_path_service import CareerPathService
from app.services.paths.graph_query_service import GraphQueryService
from app.services.reference import load_job_graph_seed
from app.services.reports.report_service import ReportService
from app.services.scheduler.scheduler_service import SchedulerService


@dataclass
class ServiceContainer:
    file_service: FileIngestionService
    job_import_service: JobImportService
    student_profile_service: object
    matching_service: MatchingService
    graph_query_service: GraphQueryService
    career_path_service: CareerPathService
    report_service: ReportService
    scheduler_service: SchedulerService
    controller_agent: MainControllerAgent


def _create_llm_provider(settings):
    return (
        MockLLMProvider()
        if settings.llm_provider == "mock"
        else ErnieLLMProvider(
            api_key=settings.ernie_api_key,
            secret_key=settings.ernie_secret_key,
            base_url=settings.ernie_base_url,
            model=settings.ernie_model,
        )
    )


def _create_ocr_provider(settings):
    return MockOCRProvider() if settings.ocr_provider == "mock" else PaddleOCRProvider(settings.paddle_ocr_service_url)


def _create_rag_provider(settings):
    return MockRAGProvider() if settings.ragflow_provider == "mock" else RAGFlowProvider(settings.ragflow_base_url, settings.ragflow_api_key)


def _create_graph_provider(settings):
    return MockGraphProvider() if settings.graph_provider == "mock" else Neo4jGraphProvider(settings.neo4j_uri, settings.neo4j_username, settings.neo4j_password)


def _create_storage_provider(settings):
    return (
        LocalStorageProvider(settings.local_storage_path)
        if settings.storage_provider == "local"
        else MinIOStorageProvider(
            settings.minio_endpoint,
            settings.minio_access_key,
            settings.minio_secret_key,
            settings.minio_bucket,
            settings.minio_secure,
        )
    )


def create_service_container() -> ServiceContainer:
    settings = get_settings()
    llm_provider = _create_llm_provider(settings)
    ocr_provider = _create_ocr_provider(settings)
    rag_provider = _create_rag_provider(settings)
    graph_provider = _create_graph_provider(settings)
    storage_provider = _create_storage_provider(settings)

    file_service = FileIngestionService(storage_provider, ocr_provider)
    job_import_service = JobImportService(llm_provider, rag_provider, graph_provider)
    from app.services.profiles.student_profile_service import StudentProfileService

    student_profile_service = StudentProfileService(llm_provider, file_service)
    matching_service = MatchingService()
    graph_query_service = GraphQueryService(graph_provider)
    career_path_service = CareerPathService(graph_query_service)
    report_service = ReportService(llm_provider, matching_service, career_path_service)
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
        graph_query_service=graph_query_service,
        career_path_service=career_path_service,
        report_service=report_service,
        scheduler_service=scheduler_service,
        controller_agent=controller_agent,
    )


async def initialize_demo_data(db: Session, container: ServiceContainer) -> None:
    ensure_demo_users(db)
    await container.job_import_service.graph_provider.load_seed(load_job_graph_seed())
    has_profiles = db.scalar(select(JobProfile.id).limit(1))
    if not has_profiles:
        await container.job_import_service.seed_templates(db)
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
