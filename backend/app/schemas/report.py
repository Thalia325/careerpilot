from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import ExportedFile


class ReportGenerateRequest(BaseModel):
    student_id: int = Field(..., gt=0)
    job_code: str = Field(..., min_length=1, max_length=100)


class ReportContent(BaseModel):
    overview: str
    matching_analysis: dict[str, Any]
    goals: dict[str, Any]
    action_plan: dict[str, Any]
    evidence: dict[str, Any]


class ReportResponse(BaseModel):
    report_id: int
    student_id: int
    job_code: str
    content: ReportContent
    markdown_content: str
    status: str


class ReportPolishRequest(BaseModel):
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

