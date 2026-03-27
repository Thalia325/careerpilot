from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.models import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import authenticate

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db_session)) -> LoginResponse:
    user = authenticate(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return LoginResponse(
        access_token=f"demo-{user.id}-{user.role}",
        role=user.role,
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )


@router.get("/me", response_model=LoginResponse)
def me(db: Session = Depends(get_db_session)) -> LoginResponse:
    user = db.scalar(select(User).where(User.username == "student_demo"))
    if not user:
        raise HTTPException(status_code=404, detail="演示用户不存在")
    return LoginResponse(
        access_token=f"demo-{user.id}-{user.role}",
        role=user.role,
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )

