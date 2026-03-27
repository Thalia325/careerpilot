from __future__ import annotations

import hashlib
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Student, Teacher, User


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def ensure_demo_users(db: Session) -> None:
    if db.scalar(select(User).where(User.username == "student_demo")):
        return
    student_user = User(
        username="student_demo",
        password_hash=hash_password("demo123"),
        role="student",
        full_name="陈同学",
        email="student_demo@careerpilot.local",
    )
    teacher_user = User(
        username="teacher_demo",
        password_hash=hash_password("demo123"),
        role="teacher",
        full_name="王老师",
        email="teacher_demo@careerpilot.local",
    )
    admin_user = User(
        username="admin_demo",
        password_hash=hash_password("demo123"),
        role="admin",
        full_name="系统管理员",
        email="admin_demo@careerpilot.local",
    )
    db.add_all([student_user, teacher_user, admin_user])
    db.flush()
    db.add(
        Student(
            user_id=student_user.id,
            major="软件工程",
            grade="大三",
            career_goal="前端开发工程师",
            learning_preferences={"preferred_roles": ["前端开发工程师", "全栈工程师"]},
        )
    )
    db.add(Teacher(user_id=teacher_user.id, department="计算机学院", title="就业指导老师"))
    db.commit()


def authenticate(db: Session, username: str, password: str) -> Optional[User]:
    user = db.scalar(select(User).where(User.username == username))
    if not user:
        return None
    return user if user.password_hash == hash_password(password) else None
