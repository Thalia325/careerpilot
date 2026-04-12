from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models import (
    CareerReport,
    JobPosting,
    JobProfile,
    MatchResult,
    Student,
    Teacher,
    User,
)
from app.schemas.common import APIResponse

router = APIRouter()


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
        "items": [
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role,
                "email": u.email,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None,
            }
            for u in rows
        ],
    })


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
