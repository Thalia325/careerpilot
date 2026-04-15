from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import ExportedFile


class ReportGenerateRequest(BaseModel):
    student_id: int = Field(..., gt=0)
    job_code: str = Field("", max_length=100)
    analysis_run_id: int | None = None
    profile_version_id: int | None = None
    match_result_id: int | None = None


class ReportContent(BaseModel):
    student_summary: dict[str, Any]
    resume_summary: dict[str, Any]
    capability_profile: dict[str, Any]
    target_job_analysis: dict[str, Any]
    matching_analysis: dict[str, Any]
    gap_analysis: dict[str, Any]
    career_path: dict[str, Any]
    short_term_plan: dict[str, Any]
    mid_term_plan: dict[str, Any]
    evaluation_cycle: dict[str, Any]
    teacher_comments: dict[str, Any]


class ReportResponse(BaseModel):
    report_id: int
    student_id: int
    job_code: str
    content: ReportContent
    markdown_content: str
    status: str
    path_recommendation_id: int | None = None
    profile_version_id: int | None = None
    match_result_id: int | None = None
    analysis_run_id: int | None = None
    source_files_deleted: bool = False


class ReportPolishRequest(BaseModel):
    report_id: int = Field(..., gt=0)
    markdown_content: str = Field(..., min_length=1, max_length=50000)


class ReportSaveRequest(BaseModel):
    report_id: int = Field(..., gt=0)
    markdown_content: str = Field(..., min_length=1, max_length=50000)


class ReportCheckRequest(BaseModel):
    report_id: int = Field(..., gt=0)


class ReportCheckResponse(BaseModel):
    report_id: int
    is_complete: bool
    missing_sections: list[str]
    suggestions: list[str]


class ReportExportRequest(BaseModel):
    report_id: int = Field(..., gt=0)
    format: Literal["pdf", "docx"] = "pdf"


class ReportExportResponse(BaseModel):
    report_id: int
    exported: ExportedFile

