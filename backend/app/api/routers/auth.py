from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import create_access_token, get_current_user, get_db_session
from app.core.config import get_settings
from app.core.errors import raise_invalid_credentials
from app.models import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.services.auth_service import authenticate, hash_password, register_user, verify_password

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db_session)) -> LoginResponse:
    user = authenticate(db, payload.username, payload.password)
    if not user:
        raise_invalid_credentials(message="用户名或密码错误")

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


@router.post("/register", response_model=LoginResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db_session)) -> LoginResponse:
    try:
        user = register_user(
            db,
            payload.username,
            payload.password,
            payload.full_name,
            payload.role,
            email=str(payload.email or ""),
            teacher_code=(payload.teacher_code or ""),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

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
    return LoginResponse(
        access_token="",
        role=current_user.role,
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
    )


@router.post("/change-password")
def change_password(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    old_password = payload.get("old_password", "")
    new_password = payload.get("new_password", "")

    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="旧密码和新密码不能为空")

    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="旧密码不正确")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6位")

    current_user.password_hash = hash_password(new_password)
    db.commit()

    return {"message": "密码修改成功"}
