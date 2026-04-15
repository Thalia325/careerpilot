from datetime import datetime, timedelta, timezone
import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.core.config import get_settings
from app.models import (
    CareerReport,
    JobPosting,
    JobProfile,
    MatchResult,
    Student,
    Teacher,
    TeacherStudentLink,
    User,
)
from app.schemas.common import APIResponse

router = APIRouter()

VALID_USER_ROLES = {"student", "teacher", "admin"}


class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=100)
    role: str = "student"
    email: str = ""


class AdminUserUpdate(BaseModel):
    username: str | None = Field(None, min_length=1, max_length=64)
    password: str | None = Field(None, min_length=1, max_length=128)
    full_name: str | None = Field(None, min_length=1, max_length=100)
    role: str | None = None
    email: str | None = None


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def _ensure_role_profile(db: Session, user: User) -> None:
    if user.role == "student" and not db.scalar(select(Student).where(Student.user_id == user.id)):
        db.add(Student(user_id=user.id, major="", grade="", career_goal="", learning_preferences={}))
    if user.role == "teacher" and not db.scalar(select(Teacher).where(Teacher.user_id == user.id)):
        db.add(Teacher(user_id=user.id, department="", title=""))


@router.get("/users", response_model=APIResponse)
def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以查看用户列表")

    total = db.query(User).count()
    rows = db.scalars(select(User).order_by(User.id).offset(skip).limit(limit)).all()

    return APIResponse(data={
        "total": total,
        "items": [_serialize_user(u) for u in rows],
    })


# --- User CRUD ---

@router.post("/users", response_model=APIResponse)
def create_user(
    payload: AdminUserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")
    if payload.role not in VALID_USER_ROLES:
        raise HTTPException(status_code=400, detail=f"无效角色，允许值：{', '.join(sorted(VALID_USER_ROLES))}")
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=400, detail="用户名已存在")

    from app.services.auth_service import hash_password
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        email=payload.email,
    )
    db.add(user)
    try:
        db.flush()
        _ensure_role_profile(db, user)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="用户创建失败，请检查用户名或关联数据是否重复") from exc
    db.refresh(user)
    return APIResponse(data=_serialize_user(user))


@router.get("/users/{user_id}", response_model=APIResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return APIResponse(data=_serialize_user(user))


@router.put("/users/{user_id}", response_model=APIResponse)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if payload.username is not None and payload.username != user.username:
        if db.scalar(select(User).where(User.username == payload.username, User.id != user_id)):
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = payload.username
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        if payload.role not in VALID_USER_ROLES:
            raise HTTPException(status_code=400, detail=f"无效角色，允许值：{', '.join(sorted(VALID_USER_ROLES))}")
        if user.id == current_user.id and payload.role != "admin":
            raise HTTPException(status_code=400, detail="不能取消自己的管理员角色")
        user.role = payload.role
    if payload.email is not None:
        user.email = payload.email
    if payload.password:
        from app.services.auth_service import hash_password
        user.password_hash = hash_password(payload.password)

    try:
        _ensure_role_profile(db, user)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="用户更新失败，请检查数据是否重复") from exc
    db.refresh(user)

    return APIResponse(data=_serialize_user(user))


@router.delete("/users/{user_id}", response_model=APIResponse)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    related_student = db.scalar(select(Student).where(Student.user_id == user_id))
    related_teacher = db.scalar(select(Teacher).where(Teacher.user_id == user_id))

    if related_student:
        has_student_data = db.scalar(select(CareerReport.id).where(CareerReport.student_id == related_student.id).limit(1))
        has_student_data = has_student_data or db.scalar(select(MatchResult.id).where(MatchResult.student_id == related_student.id).limit(1))
        has_student_data = has_student_data or db.scalar(select(TeacherStudentLink.id).where(TeacherStudentLink.student_id == related_student.id).limit(1))
        if has_student_data:
            raise HTTPException(status_code=400, detail="该学生已有报告、匹配或师生绑定数据，不能直接删除")
        db.delete(related_student)

    if related_teacher:
        has_teacher_data = db.scalar(select(TeacherStudentLink.id).where(TeacherStudentLink.teacher_id == related_teacher.id).limit(1))
        if has_teacher_data:
            raise HTTPException(status_code=400, detail="该教师已有师生绑定数据，不能直接删除")
        db.delete(related_teacher)

    db.delete(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="该用户存在关联数据，不能直接删除") from exc
    return APIResponse(data={"deleted": True, "id": user_id})


@router.patch("/users/{user_id}/status", response_model=APIResponse)
def toggle_user_status(
    user_id: int,
    active: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.email = user.email or ""  # ensure non-null
    # Store disabled status in email field prefix as a simple mechanism
    if not active:
        if not user.email.startswith("[disabled]"):
            user.email = f"[disabled]{user.email}"
    else:
        if user.email.startswith("[disabled]"):
            user.email = user.email[len("[disabled]"):]
    db.commit()

    return APIResponse(data={"id": user.id, "active": active})


@router.get("/stats/overview", response_model=APIResponse)
def stats_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    total_users = db.query(User).count()
    total_jobs = db.query(JobPosting).count()
    total_reports = db.query(CareerReport).count()

    avg_score_row = db.scalar(
        select(func.avg(MatchResult.total_score))
    )
    avg_match_score = round(float(avg_score_row), 1) if avg_score_row else 0.0

    return APIResponse(data={
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_reports": total_reports,
        "avg_match_score": avg_match_score,
    })


@router.get("/stats/trends", response_model=APIResponse)
def stats_trends(
    days: int = 14,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.execute(
        text("""
            SELECT DATE(created_at) AS d,
                   SUM(CASE WHEN :reports_table = 1 THEN 1 ELSE 0 END) AS reports,
                   SUM(CASE WHEN :users_table = 1 THEN 1 ELSE 0 END) AS users
            FROM (
                SELECT created_at, 1 AS reports_table, 0 AS users_table FROM career_reports WHERE created_at >= :since
                UNION ALL
                SELECT created_at, 0, 1 FROM users WHERE created_at >= :since
            ) sub
            GROUP BY DATE(created_at)
            ORDER BY d
        """),
        {"since": since, "reports_table": 1, "users_table": 1},
    ).fetchall()

    result = []
    for r in rows:
        d = r[0]
        result.append({
            "date": d.isoformat() if hasattr(d, "isoformat") else str(d),
            "reports": int(r[1] or 0),
            "users": int(r[2] or 0),
        })

    return APIResponse(data=result)


@router.get("/stats/weekly", response_model=APIResponse)
def stats_weekly(
    weeks: int = 8,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    since = datetime.now(timezone.utc) - timedelta(weeks=weeks)

    report_rows = db.execute(
        text("""
            SELECT strftime('%Y-W%W', created_at) AS week_label,
                   COUNT(*) AS cnt
            FROM career_reports
            WHERE created_at >= :since
            GROUP BY week_label
            ORDER BY week_label
        """),
        {"since": since},
    ).fetchall()
    report_map = {r[0]: int(r[1]) for r in report_rows}

    match_rows = db.execute(
        text("""
            SELECT strftime('%Y-W%W', created_at) AS week_label,
                   COUNT(*) AS cnt
            FROM match_results
            WHERE created_at >= :since
            GROUP BY week_label
            ORDER BY week_label
        """),
        {"since": since},
    ).fetchall()
    match_map = {r[0]: int(r[1]) for r in match_rows}

    all_weeks = sorted(set(list(report_map.keys()) + list(match_map.keys())))

    return APIResponse(data=[
        {
            "week": w,
            "reports": report_map.get(w, 0),
            "matches": match_map.get(w, 0),
        }
        for w in all_weeks
    ])


@router.get("/system/health", response_model=APIResponse)
def system_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    start = datetime.now(timezone.utc)
    try:
        db.scalar(select(1))
        db_ok = True
    except Exception:
        db_ok = False
    elapsed_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

    return APIResponse(data={
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "error",
        "api_response_ms": elapsed_ms,
        "last_check": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    })


# --- Teacher-Student Link CRUD ---

@router.get("/teacher-student-links", response_model=APIResponse)
def list_links(
    skip: int = 0,
    limit: int = 50,
    teacher_id: int | None = None,
    student_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    query = select(TeacherStudentLink).order_by(TeacherStudentLink.id)
    if teacher_id:
        query = query.where(TeacherStudentLink.teacher_id == teacher_id)
    if student_id:
        query = query.where(TeacherStudentLink.student_id == student_id)

    total = len(db.scalars(query).all())
    links = db.scalars(query.offset(skip).limit(limit)).all()

    items = []
    for link in links:
        teacher = db.scalar(select(Teacher).where(Teacher.id == link.teacher_id))
        teacher_user = db.scalar(select(User).where(User.id == teacher.user_id)) if teacher else None
        student = db.scalar(select(Student).where(Student.id == link.student_id))
        student_user = db.scalar(select(User).where(User.id == student.user_id)) if student else None

        items.append({
            "id": link.id,
            "teacher_id": link.teacher_id,
            "teacher_name": teacher_user.full_name if teacher_user else "未知",
            "student_id": link.student_id,
            "student_name": student_user.full_name if student_user else "未知",
            "group_name": link.group_name,
            "is_primary": link.is_primary,
            "source": link.source,
            "status": link.status,
            "created_at": link.created_at.isoformat() if link.created_at else None,
        })

    return APIResponse(data={"total": total, "items": items})


@router.post("/teacher-student-links", response_model=APIResponse)
def create_link(
    teacher_id: int,
    student_id: int,
    group_name: str = "",
    is_primary: bool = True,
    source: str = "manual",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    teacher = db.scalar(select(Teacher).where(Teacher.id == teacher_id))
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    student = db.scalar(select(Student).where(Student.id == student_id))
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # Check for existing active link
    existing = db.scalar(
        select(TeacherStudentLink).where(
            TeacherStudentLink.teacher_id == teacher_id,
            TeacherStudentLink.student_id == student_id,
            TeacherStudentLink.status == "active",
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="该教师学生绑定关系已存在")

    link = TeacherStudentLink(
        teacher_id=teacher_id,
        student_id=student_id,
        group_name=group_name,
        is_primary=is_primary,
        source=source,
        status="active",
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return APIResponse(data={"id": link.id, "teacher_id": link.teacher_id, "student_id": link.student_id, "status": link.status})


@router.put("/teacher-student-links/{link_id}", response_model=APIResponse)
def update_link(
    link_id: int,
    group_name: str | None = None,
    is_primary: bool | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    link = db.scalar(select(TeacherStudentLink).where(TeacherStudentLink.id == link_id))
    if not link:
        raise HTTPException(status_code=404, detail="绑定关系不存在")

    if group_name is not None:
        link.group_name = group_name
    if is_primary is not None:
        link.is_primary = is_primary
    if status is not None:
        link.status = status

    db.commit()

    return APIResponse(data={"id": link.id, "updated": True})


@router.delete("/teacher-student-links/{link_id}", response_model=APIResponse)
def delete_link(
    link_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    link = db.scalar(select(TeacherStudentLink).where(TeacherStudentLink.id == link_id))
    if not link:
        raise HTTPException(status_code=404, detail="绑定关系不存在")

    db.delete(link)
    db.commit()

    return APIResponse(data={"deleted": True, "id": link_id})


@router.post("/teacher-student-links/import", response_model=APIResponse)
def batch_import_links(
    links: list[dict],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Batch import teacher-student links."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    created = 0
    skipped = 0
    for item in links:
        teacher_id = item.get("teacher_id")
        student_id = item.get("student_id")
        if not teacher_id or not student_id:
            skipped += 1
            continue

        existing = db.scalar(
            select(TeacherStudentLink).where(
                TeacherStudentLink.teacher_id == teacher_id,
                TeacherStudentLink.student_id == student_id,
                TeacherStudentLink.status == "active",
            )
        )
        if existing:
            skipped += 1
            continue

        link = TeacherStudentLink(
            teacher_id=teacher_id,
            student_id=student_id,
            group_name=item.get("group_name", ""),
            is_primary=item.get("is_primary", True),
            source="batch_import",
            status="active",
        )
        db.add(link)
        created += 1

    db.commit()
    return APIResponse(data={"created": created, "skipped": skipped})


# --- Student CRUD (US-028) ---

@router.get("/students", response_model=APIResponse)
def list_students(
    skip: int = 0,
    limit: int = 50,
    major: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    query = select(Student).order_by(Student.id)
    if major:
        query = query.where(Student.major == major)
    total = len(db.scalars(query).all())
    rows = db.scalars(query.offset(skip).limit(limit)).all()

    items = []
    for s in rows:
        user = db.scalar(select(User).where(User.id == s.user_id))
        items.append({
            "id": s.id, "user_id": s.user_id,
            "full_name": user.full_name if user else "",
            "major": s.major, "grade": s.grade,
            "career_goal": s.career_goal,
            "target_job_code": s.target_job_code,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return APIResponse(data={"total": total, "items": items})


@router.post("/students", response_model=APIResponse)
def create_student(
    user_id: int,
    major: str = "",
    grade: str = "",
    career_goal: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    student = Student(user_id=user_id, major=major, grade=grade, career_goal=career_goal)
    db.add(student)
    db.commit()
    db.refresh(student)
    return APIResponse(data={"id": student.id, "user_id": student.user_id})


@router.put("/students/{student_id}", response_model=APIResponse)
def update_student(
    student_id: int,
    major: str | None = None,
    grade: str | None = None,
    career_goal: str | None = None,
    target_job_code: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    student = db.scalar(select(Student).where(Student.id == student_id))
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    if major is not None: student.major = major
    if grade is not None: student.grade = grade
    if career_goal is not None: student.career_goal = career_goal
    if target_job_code is not None: student.target_job_code = target_job_code
    db.commit()
    return APIResponse(data={"id": student.id, "updated": True})


@router.delete("/students/{student_id}", response_model=APIResponse)
def delete_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    student = db.scalar(select(Student).where(Student.id == student_id))
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    db.delete(student)
    db.commit()
    return APIResponse(data={"deleted": True, "id": student_id})


# --- Teacher CRUD (US-028) ---

@router.get("/teachers", response_model=APIResponse)
def list_teachers(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    total = db.scalar(select(func.count(Teacher.id))) or 0
    rows = db.scalars(select(Teacher).order_by(Teacher.id).offset(skip).limit(limit)).all()

    items = []
    for t in rows:
        user = db.scalar(select(User).where(User.id == t.user_id))
        student_count = db.scalar(
            select(func.count(TeacherStudentLink.id)).where(
                TeacherStudentLink.teacher_id == t.id,
                TeacherStudentLink.status == "active",
            )
        ) or 0
        items.append({
            "id": t.id, "user_id": t.user_id,
            "full_name": user.full_name if user else "",
            "student_count": student_count,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return APIResponse(data={"total": total, "items": items})


@router.post("/teachers", response_model=APIResponse)
def create_teacher(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    teacher = Teacher(user_id=user_id)
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return APIResponse(data={"id": teacher.id, "user_id": teacher.user_id})


@router.delete("/teachers/{teacher_id}", response_model=APIResponse)
def delete_teacher(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    teacher = db.scalar(select(Teacher).where(Teacher.id == teacher_id))
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")

    db.delete(teacher)
    db.commit()
    return APIResponse(data={"deleted": True, "id": teacher_id})


# --- Job CRUD (US-030) ---

@router.post("/jobs", response_model=APIResponse)
def create_job(
    job_code: str,
    title: str,
    company_name: str = "",
    city: str = "",
    salary: str = "",
    industry: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    job = JobPosting(job_code=job_code, title=title, company_name=company_name,
                     city=city, salary=salary, industry=industry)
    db.add(job)
    db.commit()
    db.refresh(job)
    return APIResponse(data={"id": job.id, "job_code": job.job_code, "title": job.title})


@router.delete("/jobs/{job_id}", response_model=APIResponse)
def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    job = db.scalar(select(JobPosting).where(JobPosting.id == job_id))
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    db.delete(job)
    db.commit()
    return APIResponse(data={"deleted": True, "id": job_id})


# --- Report Management (US-032) ---

@router.get("/reports", response_model=APIResponse)
def list_reports(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    total = db.scalar(select(func.count(CareerReport.id))) or 0
    rows = db.scalars(
        select(CareerReport).order_by(CareerReport.created_at.desc()).offset(skip).limit(limit)
    ).all()

    items = []
    for r in rows:
        student = db.scalar(select(Student).where(Student.id == r.student_id))
        user = db.scalar(select(User).where(User.id == student.user_id)) if student else None
        items.append({
            "id": r.id,
            "student_name": user.full_name if user else "未知",
            "target_job_code": r.target_job_code,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        })

    return APIResponse(data={"total": total, "items": items})


@router.put("/reports/{report_id}/status", response_model=APIResponse)
def update_report_status(
    report_id: int,
    new_status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    report = db.scalar(select(CareerReport).where(CareerReport.id == report_id))
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    report.status = new_status
    db.commit()
    return APIResponse(data={"id": report.id, "status": report.status})


@router.delete("/reports/{report_id}", response_model=APIResponse)
def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    report = db.scalar(select(CareerReport).where(CareerReport.id == report_id))
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    db.delete(report)
    db.commit()
    return APIResponse(data={"deleted": True, "id": report_id})


# --- System Config (US-033) ---

@router.get("/system/configs", response_model=APIResponse)
def list_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    from app.models import SystemConfig
    configs = db.scalars(select(SystemConfig)).all()
    items = [{"key": c.key, "value": c.value, "updated_at": c.updated_at.isoformat() if c.updated_at else None} for c in configs]
    settings = get_settings()

    return APIResponse(data={"items": items, "env": {
        "LLM_PROVIDER": settings.llm_provider,
        "OCR_PROVIDER": settings.ocr_provider,
        "STORAGE_PROVIDER": settings.storage_provider,
    }})


@router.put("/system/configs/{config_key}", response_model=APIResponse)
def update_config(
    config_key: str,
    value: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    from app.models import SystemConfig
    config = db.scalar(select(SystemConfig).where(SystemConfig.key == config_key))
    if config:
        config.value = value
    else:
        config = SystemConfig(key=config_key, value=value)
        db.add(config)
    db.commit()
    return APIResponse(data={"key": config_key, "value": value})
