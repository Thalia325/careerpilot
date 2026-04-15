from pydantic import BaseModel, Field

from app.schemas.common import DimensionWeight


class MatchingRequest(BaseModel):
    student_id: int = Field(..., gt=0)
    job_code: str = Field(default="", max_length=100)
    profile_version_id: int | None = None
    analysis_run_id: int | None = None


class DimensionScore(BaseModel):
    dimension: str
    score: float
    weight: float
    reasoning: str
    evidence: dict


class MatchingResponse(BaseModel):
    student_id: int
    job_code: str
    match_result_id: int | None = None
    total_score: float
    weights: DimensionWeight
    dimensions: list[DimensionScore]
    strengths: list[str]
    gap_items: list[dict]
    suggestions: list[str]
    summary: str

