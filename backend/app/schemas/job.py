from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import DimensionWeight


class JobPostingIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    location: str = Field(..., min_length=1, max_length=100)
    salary_range: str = Field(..., min_length=1, max_length=50)
    company_name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=100)
    company_size: str = Field(..., min_length=1, max_length=50)
    ownership_type: str = Field(..., min_length=1, max_length=50)
    job_code: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=5000)
    company_intro: str = Field(..., min_length=1, max_length=5000)


class JobImportRequest(BaseModel):
    rows: list[JobPostingIn]


class JobPostingOut(JobPostingIn):
    id: int


class JobProfileOut(BaseModel):
    id: Optional[int] = None
    job_code: str
    title: str
    summary: str
    skill_requirements: list[str]
    certificate_requirements: list[str]
    innovation_requirements: str
    learning_requirements: str
    resilience_requirements: str
    communication_requirements: str
    internship_requirements: str
    capability_scores: dict[str, Any]
    dimension_weights: DimensionWeight
    explanation_json: dict[str, Any]


class JobProfileGenerationRequest(BaseModel):
    job_codes: Optional[list[str]] = None
    title_keywords: Optional[list[str]] = None


class GraphQueryResponse(BaseModel):
    job_code: str
    title: str
    promotion_paths: list[list[str]]
    transition_paths: list[list[str]]
    upstream_jobs: list[str]
    downstream_jobs: list[str]
    required_skills: list[str]
    adjacent_skill_gaps: dict[str, list[str]]
