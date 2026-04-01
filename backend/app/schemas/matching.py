from pydantic import BaseModel, Field

from app.schemas.common import DimensionWeight


class MatchingRequest(BaseModel):
    student_id: int = Field(..., gt=0)
    job_code: str = Field(..., min_length=1, max_length=100)


class DimensionScore(BaseModel):
    dimension: str
    score: float
    weight: float
    reasoning: str
    evidence: dict


class MatchingResponse(BaseModel):
    student_id: int
    job_code: str
    total_score: float
    weights: DimensionWeight
    dimensions: list[DimensionScore]
    gap_items: list[dict]
    suggestions: list[str]
    summary: str

