from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import EvidenceItem


class ManualStudentInput(BaseModel):
    target_job: Optional[str] = Field(None, max_length=200)
    self_introduction: str = Field("", max_length=2000)
    skills: list[str] = Field(default_factory=list)
    certificates: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    internships: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)
    grades: dict[str, float] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)


class OCRParseRequest(BaseModel):
    uploaded_file_id: Optional[int] = Field(None, gt=0)
    raw_text: Optional[str] = Field(None, max_length=50000)
    document_type: str = Field("resume", min_length=1, max_length=50)


class OCRParseResponse(BaseModel):
    raw_text: str
    layout_blocks: list[dict[str, Any]]
    structured_json: dict[str, Any]


class StudentProfileGenerateRequest(BaseModel):
    student_id: int = Field(..., gt=0)
    uploaded_file_ids: list[int] = Field(default_factory=list)
    manual_input: Optional[ManualStudentInput] = None


class StudentProfileOut(BaseModel):
    student_id: int
    source_summary: str
    skills: list[str]
    certificates: list[str]
    capability_scores: dict[str, Any]
    completeness_score: float
    competitiveness_score: float
    willingness: dict[str, Any]
    evidence: list[EvidenceItem]
