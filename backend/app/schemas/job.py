from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import DimensionWeight


class JobPostingIn(BaseModel):
    title: str
    location: str
    salary_range: str
    company_name: str
    industry: str
    company_size: str
    ownership_type: str
    job_code: str
    description: str
    company_intro: str


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
