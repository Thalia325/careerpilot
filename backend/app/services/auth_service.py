from __future__ import annotations

import hashlib
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Student, Teacher, TeacherStudentLink, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash. Also supports legacy SHA256 hashes."""
    # Try bcrypt first
    if hashed_password.startswith("$2"):
        return pwd_context.verify(plain_password, hashed_password)
    # Fallback to legacy SHA256 for existing users
    sha256_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    if sha256_hash == hashed_password:
        return True
    return False


def migrate_password_hash(db: Session, user: User, plain_password: str) -> None:
    """Migrate legacy SHA256 password to bcrypt."""
    if not user.password_hash.startswith("$2"):
        user.password_hash = hash_password(plain_password)
        db.commit()


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
    if verify_password(password, user.password_hash):
        if not user.password_hash.startswith("$2"):
            migrate_password_hash(db, user, password)
        return user
    return None


def _find_teacher_by_code(db: Session, teacher_code: str) -> Teacher | None:
    code = teacher_code.strip()
    if not code:
        return None
    return db.scalar(
        select(Teacher)
        .join(User, Teacher.user_id == User.id)
        .where(User.role == "teacher")
        .where((User.username == code) | (User.email == code))
    )


def register_user(
    db: Session,
    username: str,
    password: str,
    full_name: str,
    role: str = "student",
    email: str = "",
    teacher_code: str = "",
) -> User:
    if db.scalar(select(User).where(User.username == username)):
        raise ValueError("账号已存在")
    teacher = None
    if role == "student" and teacher_code.strip():
        teacher = _find_teacher_by_code(db, teacher_code)
        if not teacher:
            raise ValueError("未找到对应老师，请检查老师账号或绑定邮箱")

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        full_name=full_name,
        email=email,
    )
    db.add(user)
    db.flush()
    if role == "student":
        student = Student(
            user_id=user.id,
            major="",
            grade="",
            career_goal="",
            learning_preferences={},
        )
        db.add(student)
        db.flush()
        if teacher:
            db.add(TeacherStudentLink(
                teacher_id=teacher.id,
                student_id=student.id,
                group_name="自助注册",
                is_primary=True,
                source="invite_code",
                status="active",
            ))
    elif role == "teacher":
        db.add(Teacher(
            user_id=user.id,
            department="",
            title="",
        ))
    db.commit()
    db.refresh(user)
    return user
