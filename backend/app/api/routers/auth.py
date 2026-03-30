from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import create_access_token, get_current_user, get_db_session
from app.core.config import get_settings
from app.models import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import authenticate

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db_session)) -> LoginResponse:
    """Authenticate user and return JWT token."""
    user = authenticate(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    settings = get_settings()
    access_token_expires = timedelta(hours=settings.jwt_expiration_hours)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)

    return LoginResponse(
        access_token=access_token,
        role=user.role,
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )


@router.get("/me", response_model=LoginResponse)
def me(current_user: User = Depends(get_current_user)) -> LoginResponse:
    """Get current authenticated user info."""
    settings = get_settings()
    access_token_expires = timedelta(hours=settings.jwt_expiration_hours)
    access_token = create_access_token(data={"sub": str(current_user.id)}, expires_delta=access_token_expires)

    return LoginResponse(
        access_token=access_token,
        role=current_user.role,
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
    )

