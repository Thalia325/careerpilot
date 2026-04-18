import re

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.errors import require_role, raise_resource_forbidden
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models import (
    CareerReport,
    FollowupRecord,
    GrowthTask,
    JobProfile,
    MatchResult,
    ProfileVersion,
    Student,
    StudentProfile,
    Teacher,
    TeacherComment,
    TeacherStudentLink,
    UploadedFile,
    User,
)
from app.schemas.common import APIResponse

router = APIRouter()


class TeacherInfoUpdate(BaseModel):
    full_name: str = Field(default="", max_length=100)
    email: str = Field(default="", max_length=120)
    department: str = Field(default="", max_length=100)
    title: str = Field(default="", max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip()
        if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("邮箱格式不正确")
        return email


def _get_teacher_bound_student_ids(current_user: User, db: Session) -> list[int] | None:
    """Return list of student IDs bound to current teacher, or None if admin (no filter)."""
    if current_user.role == "admin":
        return None  # Admin sees all

    teacher = db.scalar(select(Teacher).where(Teacher.user_id == current_user.id))
    if not teacher:
        return []

    link_rows = db.scalars(
        select(TeacherStudentLink.student_id).where(
            TeacherStudentLink.teacher_id == teacher.id,
            TeacherStudentLink.status == "active",
        )
    ).all()
    return list(link_rows)


def _ensure_teacher_can_access_student(current_user: User, db: Session, student_id: int) -> None:
    bound_ids = _get_teacher_bound_student_ids(current_user, db)
    if bound_ids is not None and student_id not in bound_ids:
        raise_resource_forbidden()


def _teacher_info(current_user: User, db: Session) -> dict:
    teacher = db.scalar(select(Teacher).where(Teacher.user_id == current_user.id))
    if not teacher:
        teacher = Teacher(user_id=current_user.id, department="", title="")
        db.add(teacher)
        db.commit()
        db.refresh(teacher)

    student_count = db.scalar(
        select(func.count(TeacherStudentLink.id)).where(
            TeacherStudentLink.teacher_id == teacher.id,
            TeacherStudentLink.status == "active",
        )
    ) or 0

    return {
        "teacher_id": teacher.id,
        "user_id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "department": teacher.department,
        "title": teacher.title,
        "student_count": student_count,
    }


@router.get("/me", response_model=APIResponse)
def get_teacher_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    require_role(current_user.role, "teacher")
    return APIResponse(data=_teacher_info(current_user, db))


@router.put("/me", response_model=APIResponse)
def update_teacher_info(
    payload: TeacherInfoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    require_role(current_user.role, "teacher")

    teacher = db.scalar(select(Teacher).where(Teacher.user_id == current_user.id))
    if not teacher:
        teacher = Teacher(user_id=current_user.id, department="", title="")
        db.add(teacher)
        db.flush()

    full_name = payload.full_name.strip()
    if full_name:
        current_user.full_name = full_name
    current_user.email = payload.email.strip()
    teacher.department = payload.department.strip()
    teacher.title = payload.title.strip()

    db.commit()
    db.refresh(teacher)
    return APIResponse(data=_teacher_info(current_user, db))


@router.get("/students/reports", response_model=APIResponse)
def get_student_reports(
    major: str | None = Query(None, alias="major"),
    grade: str | None = Query(None, alias="grade"),
    target_job: str | None = Query(None, alias="target_job"),
    report_status: str | None = Query(None, alias="report_status"),
    score_min: float | None = Query(None, alias="score_min"),
    score_max: float | None = Query(None, alias="score_max"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    require_role(current_user.role, "teacher", "admin")

    bound_ids = _get_teacher_bound_student_ids(current_user, db)

    query = select(Student).order_by(Student.id)
    if bound_ids is not None:
        query = query.where(Student.id.in_(bound_ids))
    if major:
        query = query.where(Student.major == major)
    if grade:
        query = query.where(Student.grade == grade)

    students = db.scalars(query).all()

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

        resolved_target_job = ""
        resolved_report_status = "未开始"
        match_score = 0.0
        last_analysis_time = None
        followup_status = "无"

        if latest_report:
            resolved_target_job = latest_report.target_job_code
            resolved_report_status = latest_report.status if latest_report.status in ("draft", "edited", "completed") else "已完成"
            if resolved_report_status == "draft":
                resolved_report_status = "进行中"
            elif resolved_report_status == "edited" or resolved_report_status == "completed":
                resolved_report_status = "已完成"
            last_analysis_time = latest_report.created_at.isoformat() if latest_report.created_at else None

            jp = db.scalar(
                select(JobProfile).where(JobProfile.job_code == latest_report.target_job_code).limit(1)
            )
            if jp:
                resolved_target_job = jp.title

        if latest_match:
            match_score = round(latest_match.total_score, 1)
            if not resolved_target_job:
                jp = db.scalar(
                    select(JobProfile).where(JobProfile.id == latest_match.job_profile_id).limit(1)
                )
                resolved_target_job = jp.title if jp else stu.career_goal
            if not latest_report:
                resolved_report_status = "待生成报告"
            if last_analysis_time is None and latest_match.created_at:
                last_analysis_time = latest_match.created_at.isoformat()

        # Followup status from GrowthTask
        latest_task = db.scalar(
            select(GrowthTask)
            .where(GrowthTask.student_id == stu.id)
            .order_by(GrowthTask.created_at.desc())
            .limit(1)
        )
        if latest_task:
            task_status = latest_task.status
            if task_status == "completed":
                followup_status = "已完成"
            elif task_status == "in_progress":
                followup_status = "跟进中"
            elif task_status == "overdue":
                followup_status = "已逾期"
            else:
                followup_status = "待跟进"

        # Apply filters
        if target_job and resolved_target_job != target_job and stu.career_goal != target_job:
            continue
        if report_status and resolved_report_status != report_status:
            continue
        if score_min is not None and match_score < score_min:
            continue
        if score_max is not None and match_score > score_max:
            continue

        items.append({
            "student_id": stu.id,
            "name": name,
            "target_job": resolved_target_job or stu.career_goal,
            "match_score": match_score,
            "report_status": resolved_report_status,
            "major": stu.major,
            "grade": stu.grade,
            "career_goal": stu.career_goal,
            "last_analysis_time": last_analysis_time,
            "followup_status": followup_status,
        })

    return APIResponse(data=items)


@router.get("/stats/match-distribution", response_model=APIResponse)
def match_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    require_role(current_user.role, "teacher", "admin")

    bound_ids = _get_teacher_bound_student_ids(current_user, db)

    scores_query = select(MatchResult.total_score)
    if bound_ids is not None:
        scores_query = scores_query.join(StudentProfile).where(StudentProfile.student_id.in_(bound_ids))
    scores = db.scalars(scores_query).all()

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
    require_role(current_user.role, "teacher", "admin")

    bound_ids = _get_teacher_bound_student_ids(current_user, db)

    query = select(Student.major, func.count(Student.id)).group_by(Student.major)
    if bound_ids is not None:
        query = query.where(Student.id.in_(bound_ids))
    rows = db.execute(query).all()

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
    require_role(current_user.role, "teacher", "admin")

    bound_ids = _get_teacher_bound_student_ids(current_user, db)

    query = select(Student).order_by(Student.id)
    if bound_ids is not None:
        query = query.where(Student.id.in_(bound_ids))
    students = db.scalars(query).all()
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
                gap_names = [g.get("item") or g.get("name") or "" for g in gaps[:2]] if gaps else ["核心技能"]
                advice_text = f"建议重点补强：{'、'.join(gap_names)}，可通过项目实践快速提升。"
            elif score >= 60:
                advice_text = "匹配度中等，建议系统性补齐目标岗位的核心技能，并积累相关实习经历。"
            else:
                advice_text = "匹配度偏低，建议重新评估职业目标，或制定长期技能提升计划。"

            if gaps:
                gap_names = [g.get("item") or g.get("name") or "" for g in gaps[:3] if g.get("item") or g.get("name")]
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


@router.get("/stats/overview", response_model=APIResponse)
def overview_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    require_role(current_user.role, "teacher", "admin")

    bound_ids = _get_teacher_bound_student_ids(current_user, db)

    # 1. 学生总数
    student_count_query = select(func.count(Student.id))
    if bound_ids is not None:
        student_count_query = student_count_query.where(Student.id.in_(bound_ids))
    total_students = db.scalar(student_count_query) or 0

    # 2. 已上传简历人数 — students who have at least one resume-type UploadedFile
    resume_file_owner_ids = db.scalars(
        select(UploadedFile.owner_id)
        .where(UploadedFile.file_type == "resume")
        .distinct()
    ).all()
    # Map owner_id (user_id) → student_id
    students_with_resume = 0
    if resume_file_owner_ids:
        resume_query = select(func.count(Student.id)).where(Student.user_id.in_(resume_file_owner_ids))
        if bound_ids is not None:
            resume_query = resume_query.where(Student.id.in_(bound_ids))
        students_with_resume = db.scalar(resume_query) or 0

    # 3. 已生成画像人数 — students with at least one StudentProfile
    profile_query = select(func.count(func.distinct(StudentProfile.student_id)))
    if bound_ids is not None:
        profile_query = profile_query.where(StudentProfile.student_id.in_(bound_ids))
    students_with_profile = db.scalar(profile_query) or 0

    # 4. 已生成报告人数 — students with at least one CareerReport
    report_query = select(func.count(func.distinct(CareerReport.student_id)))
    if bound_ids is not None:
        report_query = report_query.where(CareerReport.student_id.in_(bound_ids))
    students_with_report = db.scalar(report_query) or 0

    # 5. 平均匹配分数
    avg_match_score = 0.0
    score_query = select(MatchResult.total_score).join(
        StudentProfile, MatchResult.student_profile_id == StudentProfile.id
    )
    if bound_ids is not None:
        score_query = score_query.where(StudentProfile.student_id.in_(bound_ids))
    all_scores = db.scalars(score_query).all()
    if all_scores:
        avg_match_score = round(sum(all_scores) / len(all_scores), 1)

    # 6. 待点评报告数 — reports in draft status (not yet reviewed)
    draft_query = select(func.count(CareerReport.id)).where(CareerReport.status == "draft")
    if bound_ids is not None:
        draft_query = draft_query.where(CareerReport.student_id.in_(bound_ids))
    pending_review = db.scalar(draft_query) or 0

    # 7. 待跟进学生数 — students with GrowthTask in pending/overdue status
    followup_query = select(func.distinct(GrowthTask.student_id)).where(
        GrowthTask.status.in_(["pending", "overdue"])
    )
    if bound_ids is not None:
        followup_query = followup_query.where(GrowthTask.student_id.in_(bound_ids))
    followup_student_ids = db.scalars(followup_query).all()
    students_need_followup = len(followup_student_ids)

    return APIResponse(data={
        "total_students": total_students,
        "students_with_resume": students_with_resume,
        "students_with_profile": students_with_profile,
        "students_with_report": students_with_report,
        "avg_match_score": avg_match_score,
        "pending_review_reports": pending_review,
        "students_need_followup": students_need_followup,
    })


@router.get("/students/{student_id}/reports", response_model=APIResponse)
def get_student_report_list(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Teacher views a specific student's report list."""
    require_role(current_user.role, "teacher", "admin")

    student = db.scalar(select(Student).where(Student.id == student_id))
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    _ensure_teacher_can_access_student(current_user, db, student_id)

    reports = db.scalars(
        select(CareerReport)
        .where(CareerReport.student_id == student_id)
        .order_by(CareerReport.created_at.desc())
    ).all()

    items = []
    for report in reports:
        jp = db.scalar(
            select(JobProfile).where(JobProfile.job_code == report.target_job_code).limit(1)
        )
        profile_version = db.scalar(
            select(ProfileVersion).where(ProfileVersion.id == report.profile_version_id).limit(1)
        ) if report.profile_version_id else None

        items.append({
            "report_id": report.id,
            "target_job": jp.title if jp else report.target_job_code,
            "status": report.status,
            "profile_version_id": report.profile_version_id,
            "match_result_id": report.match_result_id,
            "analysis_run_id": report.analysis_run_id,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "updated_at": report.updated_at.isoformat() if report.updated_at else None,
            "profile_version_no": profile_version.version_no if profile_version else None,
        })

    return APIResponse(data=items)


@router.get("/reports/{report_id}", response_model=APIResponse)
def get_report_detail(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Teacher views a single report detail with all sections."""
    require_role(current_user.role, "teacher", "admin")

    report = db.scalar(select(CareerReport).where(CareerReport.id == report_id))
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    _ensure_teacher_can_access_student(current_user, db, report.student_id)

    student = db.scalar(select(Student).where(Student.id == report.student_id))
    user = db.scalar(select(User).where(User.id == student.user_id)) if student else None

    # Resume summary from profile version
    resume_summary = {}
    if report.profile_version_id:
        pv = db.scalar(select(ProfileVersion).where(ProfileVersion.id == report.profile_version_id))
        if pv:
            resume_summary = {
                "version_no": pv.version_no,
                "source_files": pv.source_files,
                "uploaded_file_ids": pv.uploaded_file_ids_json or [],
                "created_at": pv.created_at.isoformat() if pv.created_at else None,
            }

    # Match analysis
    match_data = {}
    if report.match_result_id:
        match = db.scalar(select(MatchResult).where(MatchResult.id == report.match_result_id))
        if match:
            match_data = {
                "total_score": match.total_score,
                "gaps": match.gaps_json or [],
                "strengths": match.strengths_json or [],
                "suggestions": match.suggestions_json or [],
            }

    # Profile snapshot
    profile_snapshot = {}
    if report.profile_version_id:
        pv = db.scalar(select(ProfileVersion).where(ProfileVersion.id == report.profile_version_id))
        if pv and pv.snapshot_json:
            profile_snapshot = pv.snapshot_json

    return APIResponse(data={
        "report_id": report.id,
        "student_id": report.student_id,
        "student_name": user.full_name if user else "未知",
        "student_major": student.major if student else "",
        "student_grade": student.grade if student else "",
        "target_job_code": report.target_job_code,
        "status": report.status,
        "content": report.content_json or {},
        "markdown_content": report.markdown_content or "",
        "resume_summary": resume_summary,
        "profile_snapshot": profile_snapshot,
        "match_analysis": match_data,
        "profile_version_id": report.profile_version_id,
        "match_result_id": report.match_result_id,
        "path_recommendation_id": report.path_recommendation_id,
        "analysis_run_id": report.analysis_run_id,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
    })


@router.get("/stats/class-overview", response_model=APIResponse)
def class_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Class overview statistics for teacher dashboard."""
    require_role(current_user.role, "teacher", "admin")

    bound_ids = _get_teacher_bound_student_ids(current_user, db)

    student_count_query = select(func.count(Student.id))
    if bound_ids is not None:
        student_count_query = student_count_query.where(Student.id.in_(bound_ids))
    total_students = db.scalar(student_count_query) or 0

    # Job distribution
    job_query = (
        select(Student.career_goal, func.count(Student.id))
        .where(Student.career_goal != "")
        .group_by(Student.career_goal)
    )
    if bound_ids is not None:
        job_query = job_query.where(Student.id.in_(bound_ids))
    job_rows = db.execute(job_query).all()
    job_distribution = [{"name": row[0], "value": row[1]} for row in job_rows]

    # Report completion rate
    report_count_query = select(func.count(func.distinct(CareerReport.student_id)))
    if bound_ids is not None:
        report_count_query = report_count_query.where(CareerReport.student_id.in_(bound_ids))
    students_with_report = db.scalar(report_count_query) or 0
    report_completion_rate = round(students_with_report / total_students * 100, 1) if total_students > 0 else 0.0

    # Resume completeness distribution
    profile_query = select(StudentProfile)
    if bound_ids is not None:
        profile_query = profile_query.where(StudentProfile.student_id.in_(bound_ids))
    profiles = db.scalars(profile_query).all()
    completeness_buckets = {"高(80%+)": 0, "中(50-79%)": 0, "低(<50%)": 0}
    for p in profiles:
        score = p.completeness_score or 0
        if score >= 80:
            completeness_buckets["高(80%+)"] += 1
        elif score >= 50:
            completeness_buckets["中(50-79%)"] += 1
        else:
            completeness_buckets["低(<50%)"] += 1
    resume_completeness = [{"name": k, "value": v} for k, v in completeness_buckets.items()]

    # Skill gaps top N — aggregate from match results for bound students
    gap_query = select(MatchResult).join(
        StudentProfile, MatchResult.student_profile_id == StudentProfile.id
    )
    if bound_ids is not None:
        gap_query = gap_query.where(StudentProfile.student_id.in_(bound_ids))
    all_gaps = []
    for mr in db.scalars(gap_query).all():
        all_gaps.extend(mr.gaps_json or [])
    gap_counts: dict[str, int] = {}
    for g in all_gaps:
        name = g.get("item") or g.get("name") or ""
        if name:
            gap_counts[name] = gap_counts.get(name, 0) + 1
    skill_gaps = sorted(
        [{"name": k, "count": v} for k, v in gap_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )[:10]

    # Students needing followup
    followup_query = select(func.distinct(GrowthTask.student_id)).where(
        GrowthTask.status.in_(["pending", "overdue"])
    )
    if bound_ids is not None:
        followup_query = followup_query.where(GrowthTask.student_id.in_(bound_ids))
    followup_students = db.scalars(followup_query).all()
    followup_list = []
    for sid in followup_students:
        stu = db.scalar(select(Student).where(Student.id == sid))
        if stu:
            u = db.scalar(select(User).where(User.id == stu.user_id))
            followup_list.append({
                "student_id": sid,
                "name": u.full_name if u else "未知",
                "major": stu.major,
                "career_goal": stu.career_goal,
            })

    return APIResponse(data={
        "job_distribution": job_distribution,
        "report_completion_rate": report_completion_rate,
        "resume_completeness": resume_completeness,
        "skill_gaps": skill_gaps,
        "followup_students": followup_list,
    })


@router.patch("/students/{student_id}/followup", response_model=APIResponse)
def update_followup_status(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    status_value: str | None = None,
    next_followup_date: str | None = None,
    teacher_notes: str | None = None,
) -> APIResponse:
    """Teacher updates followup status for a student."""
    require_role(current_user.role, "teacher", "admin")

    student = db.scalar(select(Student).where(Student.id == student_id))
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    _ensure_teacher_can_access_student(current_user, db, student_id)

    # Find or create a GrowthTask for followup tracking
    task = db.scalar(
        select(GrowthTask)
        .where(GrowthTask.student_id == student_id)
        .order_by(GrowthTask.created_at.desc())
        .limit(1)
    )

    valid_statuses = ["pending", "in_progress", "completed", "overdue", "read", "communicated", "review"]
    if status_value and status_value not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，允许值：{', '.join(valid_statuses)}")

    if task:
        if status_value:
            task.status = status_value
        if next_followup_date:
            from datetime import datetime
            task.deadline = datetime.fromisoformat(next_followup_date)
        db.commit()
    else:
        # Create a new GrowthTask if none exists
        task = GrowthTask(
            student_id=student_id,
            title="教师跟进",
            phase="followup",
            status=status_value or "pending",
            deadline=None,
        )
        if next_followup_date:
            from datetime import datetime
            task.deadline = datetime.fromisoformat(next_followup_date)
        db.add(task)
        db.commit()
        db.refresh(task)

    # Save teacher notes as FollowupRecord
    if teacher_notes:
        record = FollowupRecord(
            student_id=student_id,
            task_id=task.id,
            record_type="followup",
            content=teacher_notes,
            meta_json={"teacher_id": current_user.id},
        )
        db.add(record)
        db.commit()

    return APIResponse(data={
        "student_id": student_id,
        "status": task.status,
        "deadline": task.deadline.isoformat() if task.deadline else None,
        "updated": True,
    })


# --- Teacher Comment CRUD ---

@router.post("/reports/{report_id}/comments", response_model=APIResponse)
def create_comment(
    report_id: int,
    comment_text: str,
    priority: str = "normal",
    visible_to_student: bool = True,
    follow_up_status: str | None = None,
    next_follow_up_date: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Teacher adds a comment to a student report."""
    require_role(current_user.role, "teacher", "admin")

    report = db.scalar(select(CareerReport).where(CareerReport.id == report_id))
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    _ensure_teacher_can_access_student(current_user, db, report.student_id)

    valid_priorities = ["low", "normal", "high", "urgent"]
    if priority not in valid_priorities:
        raise HTTPException(status_code=400, detail=f"优先级无效，允许值：{', '.join(valid_priorities)}")

    valid_followup_statuses = ["pending", "in_progress", "completed", "overdue", "read", "communicated", "review"]
    if follow_up_status and follow_up_status not in valid_followup_statuses:
        raise HTTPException(status_code=400, detail=f"跟进状态无效，允许值：{', '.join(valid_followup_statuses)}")

    parsed_date = None
    if next_follow_up_date:
        from datetime import datetime as dt
        parsed_date = dt.fromisoformat(next_follow_up_date)

    comment = TeacherComment(
        teacher_id=current_user.id,
        student_id=report.student_id,
        report_id=report_id,
        analysis_run_id=report.analysis_run_id,
        comment=comment_text,
        priority=priority,
        visible_to_student=visible_to_student,
        follow_up_status=follow_up_status,
        next_follow_up_date=parsed_date,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return APIResponse(data={
        "id": comment.id,
        "teacher_id": comment.teacher_id,
        "student_id": comment.student_id,
        "report_id": comment.report_id,
        "comment": comment.comment,
        "priority": comment.priority,
        "visible_to_student": comment.visible_to_student,
        "follow_up_status": comment.follow_up_status,
        "next_follow_up_date": comment.next_follow_up_date.isoformat() if comment.next_follow_up_date else None,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    })


@router.get("/reports/{report_id}/comments", response_model=APIResponse)
def list_comments(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """List all comments for a report."""
    require_role(current_user.role, "teacher", "admin")

    report = db.scalar(select(CareerReport).where(CareerReport.id == report_id))
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    _ensure_teacher_can_access_student(current_user, db, report.student_id)

    comments = db.scalars(
        select(TeacherComment)
        .where(TeacherComment.report_id == report_id)
        .order_by(TeacherComment.created_at.desc())
    ).all()

    items = []
    for c in comments:
        teacher = db.scalar(select(User).where(User.id == c.teacher_id))
        items.append({
            "id": c.id,
            "teacher_id": c.teacher_id,
            "teacher_name": teacher.full_name if teacher else "未知",
            "student_id": c.student_id,
            "report_id": c.report_id,
            "comment": c.comment,
            "priority": c.priority,
            "visible_to_student": c.visible_to_student,
            "student_read_at": c.student_read_at.isoformat() if c.student_read_at else None,
            "follow_up_status": c.follow_up_status,
            "next_follow_up_date": c.next_follow_up_date.isoformat() if c.next_follow_up_date else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })

    return APIResponse(data=items)


@router.put("/comments/{comment_id}", response_model=APIResponse)
def update_comment(
    comment_id: int,
    comment_text: str | None = None,
    priority: str | None = None,
    visible_to_student: bool | None = None,
    follow_up_status: str | None = None,
    next_follow_up_date: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Teacher updates their own comment."""
    require_role(current_user.role, "teacher", "admin")

    comment = db.scalar(select(TeacherComment).where(TeacherComment.id == comment_id))
    if not comment:
        raise HTTPException(status_code=404, detail="点评不存在")

    _ensure_teacher_can_access_student(current_user, db, comment.student_id)

    if comment.teacher_id != current_user.id and current_user.role != "admin":
        raise_resource_forbidden("只能修改自己的点评")

    if comment_text is not None:
        comment.comment = comment_text
    if priority is not None:
        valid_priorities = ["low", "normal", "high", "urgent"]
        if priority not in valid_priorities:
            raise HTTPException(status_code=400, detail=f"优先级无效")
        comment.priority = priority
    if visible_to_student is not None:
        comment.visible_to_student = visible_to_student
    if follow_up_status is not None:
        valid_followup_statuses = ["pending", "in_progress", "completed", "overdue", "read", "communicated", "review"]
        if follow_up_status not in valid_followup_statuses:
            raise HTTPException(status_code=400, detail=f"跟进状态无效，允许值：{', '.join(valid_followup_statuses)}")
        comment.follow_up_status = follow_up_status
    if next_follow_up_date is not None:
        from datetime import datetime as dt
        comment.next_follow_up_date = dt.fromisoformat(next_follow_up_date)

    db.commit()
    db.refresh(comment)

    return APIResponse(data={
        "id": comment.id,
        "comment": comment.comment,
        "priority": comment.priority,
        "visible_to_student": comment.visible_to_student,
        "follow_up_status": comment.follow_up_status,
        "next_follow_up_date": comment.next_follow_up_date.isoformat() if comment.next_follow_up_date else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
    })


@router.delete("/comments/{comment_id}", response_model=APIResponse)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Teacher deletes their own comment."""
    require_role(current_user.role, "teacher", "admin")

    comment = db.scalar(select(TeacherComment).where(TeacherComment.id == comment_id))
    if not comment:
        raise HTTPException(status_code=404, detail="点评不存在")

    _ensure_teacher_can_access_student(current_user, db, comment.student_id)

    if comment.teacher_id != current_user.id and current_user.role != "admin":
        raise_resource_forbidden("只能删除自己的点评")

    db.delete(comment)
    db.commit()

    return APIResponse(data={"deleted": True, "id": comment_id})


# --- Roster Management ---

@router.get("/roster/search", response_model=APIResponse)
def search_roster_candidates(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Search candidate students by username, email, major, or grade."""
    require_role(current_user.role, "teacher", "admin")

    teacher = db.scalar(select(Teacher).where(Teacher.user_id == current_user.id))
    if not teacher:
        teacher = Teacher(user_id=current_user.id, department="", title="")
        db.add(teacher)
        db.flush()

    # Build search condition across User (username, email) and Student (major, grade)
    kw = f"%{keyword}%"
    user_ids_matching = db.scalars(
        select(User.id).where(
            (User.username.ilike(kw)) | (User.email.ilike(kw)) | (User.full_name.ilike(kw))
        )
    ).all()

    query = (
        select(Student)
        .where(
            Student.user_id.in_(user_ids_matching)
            | Student.major.ilike(kw)
            | Student.grade.ilike(kw)
        )
        .order_by(Student.id)
    )
    students = db.scalars(query).all()

    # Get already-bound student IDs for this teacher
    already_bound_ids = set(
        db.scalars(
            select(TeacherStudentLink.student_id).where(
                TeacherStudentLink.teacher_id == teacher.id,
                TeacherStudentLink.status == "active",
            )
        ).all()
    )

    items = []
    for stu in students:
        user = db.scalar(select(User).where(User.id == stu.user_id))
        items.append({
            "student_id": stu.id,
            "user_id": stu.user_id,
            "username": user.username if user else "",
            "full_name": user.full_name if user else "",
            "email": user.email if user else "",
            "major": stu.major,
            "grade": stu.grade,
            "already_bound": stu.id in already_bound_ids,
        })

    return APIResponse(data=items)


@router.post("/roster/{student_id}", response_model=APIResponse)
def add_student_to_roster(
    student_id: int,
    group_name: str = Query("", description="分组名称"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Bind an eligible student to the current teacher's class."""
    require_role(current_user.role, "teacher", "admin")

    student = db.scalar(select(Student).where(Student.id == student_id))
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    teacher = db.scalar(select(Teacher).where(Teacher.user_id == current_user.id))
    if not teacher:
        teacher = Teacher(user_id=current_user.id, department="", title="")
        db.add(teacher)
        db.flush()

    # Check if already bound to this teacher
    existing = db.scalar(
        select(TeacherStudentLink).where(
            TeacherStudentLink.teacher_id == teacher.id,
            TeacherStudentLink.student_id == student_id,
            TeacherStudentLink.status == "active",
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="该学生已在您的班级中")

    # Check if student is bound to another teacher (reject cross-teacher binding)
    other_teacher_link = db.scalar(
        select(TeacherStudentLink).where(
            TeacherStudentLink.student_id == student_id,
            TeacherStudentLink.status == "active",
            TeacherStudentLink.teacher_id != teacher.id,
        )
    )
    if other_teacher_link:
        other_teacher = db.scalar(select(Teacher).where(Teacher.id == other_teacher_link.teacher_id))
        other_user = db.scalar(select(User).where(User.id == other_teacher.user_id)) if other_teacher else None
        teacher_name = other_user.full_name if other_user else "未知教师"
        raise HTTPException(
            status_code=403,
            detail=f"该学生已被 {teacher_name} 绑定，无法重复绑定",
        )

    link = TeacherStudentLink(
        teacher_id=teacher.id,
        student_id=student_id,
        group_name=group_name,
        is_primary=True,
        source="manual",
        status="active",
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return APIResponse(data={
        "id": link.id,
        "teacher_id": teacher.id,
        "student_id": student_id,
        "group_name": link.group_name,
        "source": link.source,
        "status": link.status,
        "created_at": link.created_at.isoformat() if link.created_at else None,
    })


@router.delete("/roster/{student_id}", response_model=APIResponse)
def remove_student_from_roster(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Remove a student from the current teacher's class."""
    require_role(current_user.role, "teacher", "admin")

    teacher = db.scalar(select(Teacher).where(Teacher.user_id == current_user.id))
    if not teacher:
        raise HTTPException(status_code=404, detail="教师记录不存在")

    link = db.scalar(
        select(TeacherStudentLink).where(
            TeacherStudentLink.teacher_id == teacher.id,
            TeacherStudentLink.student_id == student_id,
            TeacherStudentLink.status == "active",
        )
    )
    if not link:
        raise HTTPException(status_code=404, detail="该学生不在您的班级中")

    link.status = "inactive"
    db.commit()
    db.refresh(link)

    return APIResponse(data={"removed": True, "student_id": student_id})


@router.post("/students/{student_user_id}/reset-password", response_model=APIResponse)
def reset_student_password(
    student_user_id: int,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Teacher resets password for a bound student. Admin can also use this."""
    require_role(current_user.role, "teacher", "admin")

    new_password = payload.get("new_password", "")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6位")

    # Look up student by user_id
    student = db.scalar(select(Student).where(Student.user_id == student_user_id))
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # Teacher can only reset for bound students; admin bypasses
    _ensure_teacher_can_access_student(current_user, db, student.id)

    user = db.scalar(select(User).where(User.id == student_user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    from app.services.auth_service import hash_password
    user.password_hash = hash_password(new_password)
    db.commit()

    return APIResponse(data={"message": "密码重置成功", "user_id": student_user_id})
