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


class JobProfileCreate(BaseModel):
    """Admin create JobProfile — job_code and title required, rest optional."""
    job_code: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=120)
    summary: str = ""
    skill_requirements: list[str] = []
    certificate_requirements: list[str] = []
    innovation_requirements: str = ""
    learning_requirements: str = ""
    resilience_requirements: str = ""
    communication_requirements: str = ""
    internship_requirements: str = ""
    capability_scores: dict[str, Any] = {}
    dimension_weights: dict[str, Any] = {}
    explanation_json: dict[str, Any] = {}


class JobProfileUpdate(BaseModel):
    """Admin update JobProfile — all fields optional."""
    job_code: Optional[str] = Field(None, min_length=1, max_length=80)
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    summary: Optional[str] = None
    skill_requirements: Optional[list[str]] = None
    certificate_requirements: Optional[list[str]] = None
    innovation_requirements: Optional[str] = None
    learning_requirements: Optional[str] = None
    resilience_requirements: Optional[str] = None
    communication_requirements: Optional[str] = None
    internship_requirements: Optional[str] = None
    capability_scores: Optional[dict[str, Any]] = None
    dimension_weights: Optional[dict[str, Any]] = None
    explanation_json: Optional[dict[str, Any]] = None


class JobProfileGenerationRequest(BaseModel):
    job_codes: Optional[list[str]] = None
    title_keywords: Optional[list[str]] = None


class RecommendedJobItem(BaseModel):
    """Standardized recommendation result for frontend display and downstream use."""

    job_code: str
    title: str
    company: str
    location: str = ""
    salary: str = ""
    industry: str = ""
    industry_group: str = ""
    company_size: str = ""
    ownership_type: str = ""
    match_score: float
    matched_tags: list[str] = []
    missing_tags: list[str] = []
    reason: str = ""
    summary: str = ""
    tags: list[str] = []
    experience_tags: list[str] = []
    base_score: Optional[float] = None
    experience_score: Optional[float] = None
    skill_score: Optional[float] = None
    potential_score: Optional[float] = None


class RecommendedJobsResponse(BaseModel):
    items: list[RecommendedJobItem]


class GraphQueryResponse(BaseModel):
    job_code: str
    title: str
    promotion_paths: list[list[str]]
    transition_paths: list[list[str]]
    upstream_jobs: list[str]
    downstream_jobs: list[str]
    required_skills: list[str]
    adjacent_skill_gaps: dict[str, list[str]]
