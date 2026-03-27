from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import EvidenceItem


class ManualStudentInput(BaseModel):
    target_job: Optional[str] = None
    self_introduction: str = ""
    skills: list[str] = Field(default_factory=list)
    certificates: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    internships: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)
    grades: dict[str, float] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)


class OCRParseRequest(BaseModel):
    uploaded_file_id: Optional[int] = None
    raw_text: Optional[str] = None
    document_type: str = "resume"


class OCRParseResponse(BaseModel):
    raw_text: str
    layout_blocks: list[dict[str, Any]]
    structured_json: dict[str, Any]


class StudentProfileGenerateRequest(BaseModel):
    student_id: int
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
