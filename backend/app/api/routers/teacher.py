from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models import (
    CareerReport,
    JobProfile,
    MatchResult,
    Student,
    StudentProfile,
    User,
)
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/students/reports", response_model=APIResponse)
def get_student_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    students = db.scalars(
        select(Student).order_by(Student.id)
    ).all()

    items = []
    for stu in students:
        user = db.scalar(select(User).where(User.id == stu.user_id))
        name = user.full_name if user else "未知"

        latest_report = db.scalar(
            select(CareerReport)
            .where(CareerReport.student_id == stu.id)
            .order_by(CareerReport.created_at.desc())
            .limit(1)
        )

        latest_match = db.scalar(
            select(MatchResult)
            .join(StudentProfile, MatchResult.student_profile_id == StudentProfile.id)
            .where(StudentProfile.student_id == stu.id)
            .order_by(MatchResult.created_at.desc())
            .limit(1)
        )

        target_job = ""
        report_status = "未开始"
        match_score = 0.0

        if latest_report:
            target_job = latest_report.target_job_code
            report_status = latest_report.status if latest_report.status in ("draft", "edited", "completed") else "已完成"
            if report_status == "draft":
                report_status = "进行中"
            elif report_status == "edited" or report_status == "completed":
                report_status = "已完成"

            jp = db.scalar(
                select(JobProfile).where(JobProfile.job_code == latest_report.target_job_code).limit(1)
            )
            if jp:
                target_job = jp.title

        if latest_match:
            match_score = round(latest_match.total_score, 1)

        items.append({
            "student_id": stu.id,
            "name": name,
            "target_job": target_job,
            "match_score": match_score,
            "report_status": report_status,
            "major": stu.major,
            "grade": stu.grade,
            "career_goal": stu.career_goal,
        })

    return APIResponse(data=items)


@router.get("/stats/match-distribution", response_model=APIResponse)
def match_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    scores = db.scalars(
        select(MatchResult.total_score)
    ).all()

    ranges = [
        ("90分以上", 90, 101),
        ("80-89分", 80, 90),
        ("70-79分", 70, 80),
        ("60-69分", 60, 70),
        ("60分以下", 0, 60),
    ]

    result = []
    for label, low, high in ranges:
        count = sum(1 for s in scores if low <= s < high)
        result.append({"name": label, "count": count})

    return APIResponse(data=result)


@router.get("/stats/major-distribution", response_model=APIResponse)
def major_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    rows = db.execute(
        select(Student.major, func.count(Student.id))
        .group_by(Student.major)
    ).all()

    result = [
        {"name": row[0] if row[0] else "未设置", "value": row[1]}
        for row in rows
    ]

    if not result:
        result = [{"name": "暂无数据", "value": 0}]

    return APIResponse(data=result)


@router.get("/advice", response_model=APIResponse)
def get_teacher_advice(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    students = db.scalars(select(Student).order_by(Student.id)).all()
    items = []

    for stu in students:
        user = db.scalar(select(User).where(User.id == stu.user_id))
        name = user.full_name if user else "未知"

        latest_report = db.scalar(
            select(CareerReport)
            .where(CareerReport.student_id == stu.id)
            .order_by(CareerReport.created_at.desc())
            .limit(1)
        )

        latest_match = db.scalar(
            select(MatchResult)
            .join(StudentProfile, MatchResult.student_profile_id == StudentProfile.id)
            .where(StudentProfile.student_id == stu.id)
            .order_by(MatchResult.created_at.desc())
            .limit(1)
        )

        target_job = ""
        advice_text = "暂无数据，请先完成能力分析。"

        if latest_report:
            jp = db.scalar(
                select(JobProfile).where(JobProfile.job_code == latest_report.target_job_code).limit(1)
            )
            target_job = jp.title if jp else latest_report.target_job_code

        score = latest_match.total_score if latest_match else 0.0
        gaps = latest_match.gaps_json if latest_match else []

        if latest_match and score > 0:
            if score >= 85:
                advice_text = "整体匹配度高，建议关注细节提升和面试准备。"
            elif score >= 70:
                gap_names = [g.get("item", "") for g in gaps[:2]] if gaps else ["核心技能"]
                advice_text = f"建议重点补强：{'、'.join(gap_names)}，可通过项目实践快速提升。"
            elif score >= 60:
                advice_text = "匹配度中等，建议系统性补齐目标岗位的核心技能，并积累相关实习经历。"
            else:
                advice_text = "匹配度偏低，建议重新评估职业目标，或制定长期技能提升计划。"

            if gaps:
                gap_names = [g.get("item", "") for g in gaps[:3] if g.get("item")]
                if gap_names:
                    advice_text += f" 关键差距项：{'、'.join(gap_names)}。"

        items.append({
            "student_id": stu.id,
            "name": name,
            "target_job": target_job or stu.career_goal or "未设置",
            "match_score": round(score, 1),
            "advice": advice_text,
        })

    total_students = len(students)
    students_with_reports = sum(1 for s in students if db.scalar(
        select(CareerReport).where(CareerReport.student_id == s.id).limit(1)
    ))
    avg_score = 0.0
    if latest_matches := db.scalars(
        select(MatchResult.total_score)
        .join(StudentProfile, MatchResult.student_profile_id == StudentProfile.id)
    ).all():
        avg_score = round(sum(latest_matches) / len(latest_matches), 1) if latest_matches else 0.0

    items.append({
        "student_id": 0,
        "name": "全班汇总",
        "target_job": "通用",
        "match_score": avg_score,
        "advice": f"全班 {total_students} 名学生，{students_with_reports} 人已生成报告，班级平均匹配度 {avg_score}。建议按月复盘成长任务完成率，并同步更新职业目标。",
    })

    return APIResponse(data=items)
