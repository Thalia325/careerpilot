from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    message: str = "ok"
    data: Optional[Any] = None


class Pagination(BaseModel):
    total: int
    page: int = 1
    page_size: int = 20


class EvidenceItem(BaseModel):
    source: str
    excerpt: str
    confidence: float = 1.0


class ExportedFile(BaseModel):
    format: str
    path: str
    file_name: str


class TimestampedModel(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DimensionWeight(BaseModel):
    basic_requirements: float = Field(default=0.2, ge=0, le=1)
    professional_skills: float = Field(default=0.4, ge=0, le=1)
    professional_literacy: float = Field(default=0.2, ge=0, le=1)
    development_potential: float = Field(default=0.2, ge=0, le=1)
