from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20), index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), default="")


class Student(TimestampMixin, Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    major: Mapped[str] = mapped_column(String(100), default="")
    grade: Mapped[str] = mapped_column(String(20), default="")
    career_goal: Mapped[str] = mapped_column(String(200), default="")
    target_job_code: Mapped[str] = mapped_column(String(80), default="")
    target_job_title: Mapped[str] = mapped_column(String(120), default="")
    learning_preferences: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    user: Mapped["User"] = relationship()


class Teacher(TimestampMixin, Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    department: Mapped[str] = mapped_column(String(100), default="")
    title: Mapped[str] = mapped_column(String(100), default="")
    user: Mapped["User"] = relationship()


class UploadedFile(TimestampMixin, Base):
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(Integer, index=True)
    file_type: Mapped[str] = mapped_column(String(40), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100), default="")
    storage_key: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(255), default="")
    meta_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Resume(TimestampMixin, Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("uploaded_files.id"), unique=True)
    parsed_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    student: Mapped["Student"] = relationship()
    file: Mapped["UploadedFile"] = relationship()


class Certificate(TimestampMixin, Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    file_id: Mapped[Optional[int]] = mapped_column(ForeignKey("uploaded_files.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120))
    issuer: Mapped[str] = mapped_column(String(120), default="")
    level: Mapped[str] = mapped_column(String(60), default="")
    parsed_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Transcript(TimestampMixin, Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("uploaded_files.id"), unique=True)
    gpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    parsed_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    industry: Mapped[str] = mapped_column(String(120), default="")
    size: Mapped[str] = mapped_column(String(60), default="")
    ownership_type: Mapped[str] = mapped_column(String(60), default="")
    description: Mapped[str] = mapped_column(Text, default="")


class JobPosting(TimestampMixin, Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(120), index=True)
    location: Mapped[str] = mapped_column(String(120), default="")
    salary_range: Mapped[str] = mapped_column(String(50), default="")
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), nullable=True)
    company_name: Mapped[str] = mapped_column(String(200), default="")
    industry: Mapped[str] = mapped_column(String(120), default="")
    company_size: Mapped[str] = mapped_column(String(60), default="")
    ownership_type: Mapped[str] = mapped_column(String(60), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    company_intro: Mapped[str] = mapped_column(Text, default="")
    normalized_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class JobProfile(TimestampMixin, Base):
    __tablename__ = "job_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_posting_id: Mapped[Optional[int]] = mapped_column(ForeignKey("job_postings.id"), nullable=True)
    job_code: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(Text, default="")
    skill_requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    certificate_requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    innovation_requirements: Mapped[str] = mapped_column(Text, default="")
    learning_requirements: Mapped[str] = mapped_column(Text, default="")
    resilience_requirements: Mapped[str] = mapped_column(Text, default="")
    communication_requirements: Mapped[str] = mapped_column(Text, default="")
    internship_requirements: Mapped[str] = mapped_column(Text, default="")
    capability_scores: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    dimension_weights: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    explanation_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Skill(TimestampMixin, Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(80), default="")
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)


class CertificateRequired(TimestampMixin, Base):
    __tablename__ = "certificates_required"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    certificate_name: Mapped[str] = mapped_column(String(120))
    reason: Mapped[str] = mapped_column(Text, default="")


class StudentProfile(TimestampMixin, Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), unique=True, index=True)
    source_summary: Mapped[str] = mapped_column(Text, default="")
    skills_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    certificates_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    projects_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    internships_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    capability_scores: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0)
    competitiveness_score: Mapped[float] = mapped_column(Float, default=0.0)
    willingness_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    evidence_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class StudentProfileEvidence(TimestampMixin, Base):
    __tablename__ = "student_profile_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_profile_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(60))
    source: Mapped[str] = mapped_column(String(120), default="")
    excerpt: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)


class MatchResult(TimestampMixin, Base):
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_profile_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    job_profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str] = mapped_column(Text, default="")
    strengths_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    gaps_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    suggestions_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Binding fields — link match result to student, job, profile version and analysis run
    student_id: Mapped[Optional[int]] = mapped_column(ForeignKey("students.id"), nullable=True, index=True)
    target_job_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    profile_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("profile_versions.id"), nullable=True)
    analysis_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)


class MatchDimensionScore(TimestampMixin, Base):
    __tablename__ = "match_dimension_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_result_id: Mapped[int] = mapped_column(ForeignKey("match_results.id"), index=True)
    dimension: Mapped[str] = mapped_column(String(40), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    weight: Mapped[float] = mapped_column(Float, default=0.0)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class CareerPath(TimestampMixin, Base):
    __tablename__ = "career_paths"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_job_code: Mapped[str] = mapped_column(String(80), index=True)
    primary_path_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    alternate_paths_json: Mapped[list[list[str]]] = mapped_column(JSON, default=list)
    rationale: Mapped[str] = mapped_column(Text, default="")


class PathRecommendation(TimestampMixin, Base):
    __tablename__ = "path_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    target_job_code: Mapped[str] = mapped_column(String(80), index=True)
    primary_path_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    alternate_paths_json: Mapped[list[list[str]]] = mapped_column(JSON, default=list)
    vertical_graph_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    transition_graph_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    gaps_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    recommendations_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    # Enriched content fields
    current_ability_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    certificate_recommendations_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    learning_resources_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    evaluation_metrics_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    # Context binding fields
    profile_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("profile_versions.id"), nullable=True)
    match_result_id: Mapped[Optional[int]] = mapped_column(ForeignKey("match_results.id"), nullable=True)
    analysis_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)


class GrowthTask(TimestampMixin, Base):
    __tablename__ = "growth_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    report_id: Mapped[Optional[int]] = mapped_column(ForeignKey("career_reports.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    phase: Mapped[str] = mapped_column(String(20))
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    metric: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(40), default="pending")


class FollowupRecord(TimestampMixin, Base):
    __tablename__ = "followup_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("growth_tasks.id"), nullable=True)
    record_type: Mapped[str] = mapped_column(String(60))
    content: Mapped[str] = mapped_column(Text, default="")
    meta_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class CareerReport(TimestampMixin, Base):
    __tablename__ = "career_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    target_job_code: Mapped[str] = mapped_column(String(80), index=True)
    path_recommendation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("path_recommendations.id"), nullable=True)
    # Context binding fields — link report to profile version, match result, and analysis run
    profile_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("profile_versions.id"), nullable=True)
    match_result_id: Mapped[Optional[int]] = mapped_column(ForeignKey("match_results.id"), nullable=True)
    analysis_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)
    content_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    markdown_content: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="draft")


class ReportVersion(TimestampMixin, Base):
    __tablename__ = "report_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("career_reports.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    content_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    markdown_content: Mapped[str] = mapped_column(Text, default="")
    editor_notes: Mapped[str] = mapped_column(Text, default="")


class SystemConfig(TimestampMixin, Base):
    __tablename__ = "system_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    config_key: Mapped[str] = mapped_column(String(100), unique=True)
    config_value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class KnowledgeDocument(TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_type: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str] = mapped_column(String(255), default="")
    embedding_status: Mapped[str] = mapped_column(String(40), default="pending")


class SchedulerJob(TimestampMixin, Base):
    __tablename__ = "scheduler_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_name: Mapped[str] = mapped_column(String(120), unique=True)
    cron_expr: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default="active")
    job_type: Mapped[str] = mapped_column(String(60), default="followup")
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class UserApiKey(TimestampMixin, Base):
    __tablename__ = "user_api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    encrypted_api_key: Mapped[str] = mapped_column(Text)
    encrypted_secret_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_mode: Mapped[str] = mapped_column(String(20), default="qianfan")


class ChatMessageRecord(TimestampMixin, Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    has_context: Mapped[bool] = mapped_column(Boolean, default=False)
    analysis_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)
    profile_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("profile_versions.id"), nullable=True)


class ProfileVersion(TimestampMixin, Base):
    __tablename__ = "profile_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    source_files: Mapped[str] = mapped_column(Text, default="")
    uploaded_file_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    file_summaries_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    evidence_snapshot_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    analysis_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)


class AnalysisRun(TimestampMixin, Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, completed, failed
    current_step: Mapped[str] = mapped_column(String(40), default="")  # uploaded, parsed, profiled, matched, reported
    failed_step: Mapped[str] = mapped_column(String(40), default="")
    error_detail: Mapped[str] = mapped_column(Text, default="")
    step_results: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # step_results stores completion info: {"uploaded": true, "parsed": true, ...}

    # Context binding fields — each analysis run explicitly tracks its input and output resources
    uploaded_file_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    resume_file_id: Mapped[Optional[int]] = mapped_column(ForeignKey("uploaded_files.id"), nullable=True)
    profile_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("profile_versions.id"), nullable=True)
    target_job_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    match_result_id: Mapped[Optional[int]] = mapped_column(ForeignKey("match_results.id"), nullable=True)
    path_recommendation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("path_recommendations.id"), nullable=True)
    report_id: Mapped[Optional[int]] = mapped_column(ForeignKey("career_reports.id"), nullable=True)


class HistoryTitle(TimestampMixin, Base):
    __tablename__ = "history_titles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    record_type: Mapped[str] = mapped_column(String(40))
    ref_id: Mapped[int] = mapped_column(Integer)
    custom_title: Mapped[str] = mapped_column(String(200), default="")


class TeacherComment(TimestampMixin, Base):
    __tablename__ = "teacher_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("career_reports.id"), index=True)
    analysis_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)
    comment: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    visible_to_student: Mapped[bool] = mapped_column(Boolean, default=True)
    student_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    follow_up_status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, default=None)
    next_follow_up_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)


class TeacherStudentLink(TimestampMixin, Base):
    __tablename__ = "teacher_student_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    group_name: Mapped[str] = mapped_column(String(100), default="")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(60), default="manual")  # manual, invite_code, batch_import
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, inactive
