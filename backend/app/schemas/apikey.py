from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SaveApiKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=1, max_length=500)
    secret_key: Optional[str] = Field(None, max_length=500)
    auth_mode: str = Field("qianfan", pattern=r"^(qianfan|aistudio)$")


class ApiKeyStatusResponse(BaseModel):
    configured: bool
    auth_mode: Optional[str] = None
    api_key_masked: Optional[str] = None
    secret_key_masked: Optional[str] = None
    model_name: Optional[str] = None


class ApiKeyTestResponse(BaseModel):
    success: bool
    message: str
