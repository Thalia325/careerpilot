from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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
    gaps_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    suggestions_json: Mapped[list[str]] = mapped_column(JSON, default=list)


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
    gaps_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    recommendations_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)


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
