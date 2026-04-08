from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.core.config import get_settings
from app.core.crypto import decrypt_value, encrypt_value
from app.models import User, UserApiKey
from app.schemas.apikey import ApiKeyStatusResponse, ApiKeyTestResponse, SaveApiKeyRequest

router = APIRouter()


def _mask(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return value[:2] + "***" + value[-2:]
    return value[:3] + "***" + value[-3:]


@router.post("", response_model=ApiKeyStatusResponse)
def save_api_key(
    payload: SaveApiKeyRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ApiKeyStatusResponse:
    existing = db.scalar(
        select(UserApiKey).where(UserApiKey.user_id == current_user.id)
    )
    enc_api = encrypt_value(payload.api_key)
    enc_secret = encrypt_value(payload.secret_key) if payload.secret_key else None

    if existing:
        existing.encrypted_api_key = enc_api
        existing.encrypted_secret_key = enc_secret
        existing.auth_mode = payload.auth_mode
    else:
        db.add(
            UserApiKey(
                user_id=current_user.id,
                encrypted_api_key=enc_api,
                encrypted_secret_key=enc_secret,
                auth_mode=payload.auth_mode,
            )
        )
    db.commit()

    settings = get_settings()
    return ApiKeyStatusResponse(
        configured=True,
        auth_mode=payload.auth_mode,
        api_key_masked=_mask(payload.api_key),
        secret_key_masked=_mask(payload.secret_key),
        model_name=settings.ernie_model,
    )


@router.get("", response_model=ApiKeyStatusResponse)
def get_api_key_status(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ApiKeyStatusResponse:
    existing = db.scalar(
        select(UserApiKey).where(UserApiKey.user_id == current_user.id)
    )
    if not existing:
        return ApiKeyStatusResponse(configured=False)

    settings = get_settings()
    raw_api = decrypt_value(existing.encrypted_api_key)
    raw_secret = decrypt_value(existing.encrypted_secret_key) if existing.encrypted_secret_key else None
    return ApiKeyStatusResponse(
        configured=True,
        auth_mode=existing.auth_mode,
        api_key_masked=_mask(raw_api),
        secret_key_masked=_mask(raw_secret),
        model_name=settings.ernie_model,
    )


@router.delete("", response_model=ApiKeyStatusResponse)
def delete_api_key(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ApiKeyStatusResponse:
    existing = db.scalar(
        select(UserApiKey).where(UserApiKey.user_id == current_user.id)
    )
    if existing:
        db.delete(existing)
        db.commit()
    return ApiKeyStatusResponse(configured=False)


@router.post("/test", response_model=ApiKeyTestResponse)
def test_api_key(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ApiKeyTestResponse:
    keys = get_user_api_keys(db, current_user.id)
    if not keys:
        return ApiKeyTestResponse(success=False, message="未配置 API Key，请先保存密钥")

    settings = get_settings()
    from app.integrations.llm.providers import ErnieLLMProvider

    provider = ErnieLLMProvider(
        api_key=keys.api_key,
        secret_key=keys.secret_key,
        base_url=settings.ernie_base_url,
        aistudio_base_url=settings.ernie_aistudio_base_url,
        model=settings.ernie_model,
        auth_mode=keys.auth_mode,
    )
    try:
        reply = provider._chat("你是一个测试助手。", "请回复：连接成功")
        if reply:
            return ApiKeyTestResponse(success=True, message=f"密钥验证成功，模型已就绪。模型回复：{reply[:80]}")
        return ApiKeyTestResponse(success=False, message="模型返回为空，请检查密钥是否正确")
    except Exception as exc:
        return ApiKeyTestResponse(success=False, message=f"密钥验证失败：{exc}")


@dataclass
class UserApiKeys:
    api_key: str
    secret_key: str | None
    auth_mode: str


def get_user_api_keys(db: Session, user_id: int) -> UserApiKeys | None:
    row = db.scalar(select(UserApiKey).where(UserApiKey.user_id == user_id))
    if not row:
        return None
    return UserApiKeys(
        api_key=decrypt_value(row.encrypted_api_key),
        secret_key=decrypt_value(row.encrypted_secret_key) if row.encrypted_secret_key else None,
        auth_mode=row.auth_mode or "qianfan",
    )
