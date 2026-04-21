from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.errors import require_role, raise_resource_forbidden
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.api.deps import get_current_user, get_db_session
from app.models import (
    AnalysisRun,
    CareerReport,
    ChatMessageRecord,
    FollowupRecord,
    HistoryTitle,
    JobProfile,
    JobPosting,
    MatchResult,
    PathRecommendation,
    ProfileVersion,
    Student,
    StudentProfile,
    Teacher,
    TeacherComment,
    TeacherStudentLink,
    UploadedFile,
    User,
)
from app.services.matching.recommendation import (
    extract_resume_experience_context,
    generate_recommendation_reason,
    score_recommended_job,
)
from app.schemas.job import RecommendedJobItem, RecommendedJobsResponse

router = APIRouter()


class StudentInfoUpdate(BaseModel):
    full_name: str = Field(default="", max_length=100)
    email: str = Field(default="", max_length=120)
    major: str = Field(default="", max_length=100)
    grade: str = Field(default="", max_length=20)
    career_goal: str = Field(default="", max_length=200)
    teacher_code: str = Field(default="", max_length=120)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        import re

        email = value.strip()
        if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("邮箱格式不正确")
        return email


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


def _get_primary_teacher_info(db: Session, student_id: int) -> dict | None:
    link = db.scalar(
        select(TeacherStudentLink)
        .where(
            TeacherStudentLink.student_id == student_id,
            TeacherStudentLink.status == "active",
        )
        .order_by(TeacherStudentLink.is_primary.desc(), TeacherStudentLink.id.desc())
        .limit(1)
    )
    if not link:
        return None

    teacher = db.get(Teacher, link.teacher_id)
    teacher_user = db.get(User, teacher.user_id) if teacher else None
    if not teacher or not teacher_user:
        return None
    return {
        "teacher_id": teacher.id,
        "teacher_user_id": teacher_user.id,
        "teacher_name": teacher_user.full_name,
        "teacher_username": teacher_user.username,
        "teacher_email": teacher_user.email,
        "link_id": link.id,
        "source": link.source,
    }


def _bind_student_to_teacher(db: Session, student: Student, teacher: Teacher) -> None:
    existing = db.scalar(
        select(TeacherStudentLink).where(
            TeacherStudentLink.teacher_id == teacher.id,
            TeacherStudentLink.student_id == student.id,
        )
    )

    active_primary_links = db.scalars(
        select(TeacherStudentLink).where(
            TeacherStudentLink.student_id == student.id,
            TeacherStudentLink.status == "active",
            TeacherStudentLink.is_primary == True,
        )
    ).all()
    for link in active_primary_links:
        if link.teacher_id != teacher.id:
            link.status = "inactive"
            link.is_primary = False

    if existing:
        existing.status = "active"
        existing.is_primary = True
        existing.group_name = existing.group_name or "学生自助绑定"
        existing.source = "student_profile"
        return

    db.add(TeacherStudentLink(
        teacher_id=teacher.id,
        student_id=student.id,
        group_name="学生自助绑定",
        is_primary=True,
        source="student_profile",
        status="active",
    ))


def resolve_target_job(db: Session, student: Student) -> tuple[str, str]:
    """Resolve the current target job with priority:
    1. 手动确认 (student.target_job_code)
    2. 已确认推荐岗位 (career_goal mapped to JobProfile)
    3. 最近匹配岗位 (most recent MatchResult)
    4. 默认回退 (empty)
    Returns (job_code, job_title).
    """
    # 1. 手动确认
    if student.target_job_code:
        return student.target_job_code, student.target_job_title or student.target_job_code

    # 2. 已确认推荐岗位 (career_goal mapped)
    if student.career_goal:
        jp = db.scalar(
            select(JobProfile)
            .where(func.lower(JobProfile.title).contains(student.career_goal.lower()))
            .limit(1)
        )
        if jp:
            return jp.job_code, jp.title

    # 3. 最近匹配岗位
    student_profile = db.scalar(
        select(StudentProfile).where(StudentProfile.student_id == student.id)
    )
    if student_profile:
        latest_match = db.scalar(
            select(MatchResult)
            .where(MatchResult.student_profile_id == student_profile.id)
            .order_by(MatchResult.created_at.desc())
            .limit(1)
        )
        if latest_match:
            jp = db.scalar(
                select(JobProfile).where(JobProfile.id == latest_match.job_profile_id).limit(1)
            )
            if jp:
                return jp.job_code, jp.title

    # 4. 默认回退
    return "", ""


@router.get("/me")
def get_current_student(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    student = db.scalar(select(Student).where(Student.user_id == current_user.id))
    if not student:
        return {
            "student_id": None,
            "user_id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "major": "",
            "grade": "",
            "career_goal": "",
            "target_job_code": "",
            "target_job_title": "",
            "suggested_job_code": None,
            "suggested_job_title": None,
            "resolved_job_code": "",
            "resolved_job_title": "",
            "teacher": None,
        }

    suggested_job_code = None
    suggested_job_title = None
    if student.career_goal:
        jp = db.scalar(
            select(JobProfile)
            .where(func.lower(JobProfile.title).contains(student.career_goal.lower()))
            .limit(1)
        )
        if jp:
            suggested_job_code = jp.job_code
            suggested_job_title = jp.title

    resolved_code, resolved_title = resolve_target_job(db, student)

    return {
        "student_id": student.id,
        "user_id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "major": student.major,
        "grade": student.grade,
        "career_goal": student.career_goal,
        "target_job_code": student.target_job_code or "",
        "target_job_title": student.target_job_title or "",
        "suggested_job_code": suggested_job_code,
        "suggested_job_title": suggested_job_title,
        "resolved_job_code": resolved_code,
        "resolved_job_title": resolved_title,
        "teacher": _get_primary_teacher_info(db, student.id),
    }


@router.put("/me")
def update_current_student(
    payload: StudentInfoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    require_role(current_user.role, "student")

    student = db.scalar(select(Student).where(Student.user_id == current_user.id))
    if not student:
        student = Student(user_id=current_user.id)
        db.add(student)
        db.flush()

    full_name = payload.full_name.strip()
    if full_name:
        current_user.full_name = full_name
    current_user.email = payload.email.strip()
    student.major = payload.major.strip()
    student.grade = payload.grade.strip()
    student.career_goal = payload.career_goal.strip()

    teacher_code = payload.teacher_code.strip()
    if teacher_code:
        teacher = _find_teacher_by_code(db, teacher_code)
        if not teacher:
            raise HTTPException(status_code=400, detail="未找到对应老师，请填写老师用户名或邮箱")
        _bind_student_to_teacher(db, student, teacher)

    db.commit()
    db.refresh(student)
    return get_current_student(current_user=current_user, db=db)


class TargetJobRequest(BaseModel):
    job_code: str = Field(..., min_length=1, max_length=80)
    job_title: str = Field(..., min_length=1, max_length=120)


@router.put("/me/target-job")
def update_target_job(
    payload: TargetJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    student = db.scalar(select(Student).where(Student.user_id == current_user.id))
    if not student:
        student = Student(user_id=current_user.id)
        db.add(student)
        db.flush()
    student.target_job_code = payload.job_code
    student.target_job_title = payload.job_title

    # Sync to the latest AnalysisRun for this student
    latest_run = db.scalar(
        select(AnalysisRun)
        .where(AnalysisRun.student_id == student.id)
        .order_by(AnalysisRun.id.desc())
        .limit(1)
    )
    if latest_run and latest_run.status in ("pending", "running"):
        latest_run.target_job_code = payload.job_code

    db.commit()
    return {
        "ok": True,
        "target_job_code": payload.job_code,
        "target_job_title": payload.job_title,
        "analysis_run_id": latest_run.id if latest_run else None,
    }


@router.delete("/me/target-job")
def clear_target_job(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    require_role(current_user.role, "student")

    student = db.scalar(select(Student).where(Student.user_id == current_user.id))
    if not student:
        return {"ok": True, "target_job_code": "", "target_job_title": ""}

    student.target_job_code = ""
    student.target_job_title = ""

    latest_run = db.scalar(
        select(AnalysisRun)
        .where(AnalysisRun.student_id == student.id)
        .order_by(AnalysisRun.id.desc())
        .limit(1)
    )
    if latest_run and latest_run.status in ("pending", "running"):
        latest_run.target_job_code = None

    db.commit()
    return {"ok": True, "target_job_code": "", "target_job_title": ""}


@router.get("/me/recommended-jobs")
def get_recommended_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    student = db.scalar(select(Student).where(Student.user_id == current_user.id))
    if not student:
        return {"items": []}

    student_profile = db.scalar(
        select(StudentProfile).where(StudentProfile.student_id == student.id)
    )

    jobs = []

    all_profiles = list(db.scalars(select(JobProfile)).all())
    postings = {
        item.job_code: item
        for item in db.scalars(select(JobPosting)).all()
    }
    experience = extract_resume_experience_context(db, current_user.id, source_summary=student_profile.source_summary if student_profile else "")
    max_recommended = 30
    min_recommended = min(8, len(all_profiles))
    quality_floor = 35.0

    if student_profile:
        scored_profiles = []

        for jp in all_profiles:
            posting = postings.get(jp.job_code)
            scoring = score_recommended_job(student_profile, jp, experience, posting)
            final_score = scoring["score"]
            scored_profiles.append((final_score, scoring, jp, posting))

        scored_profiles.sort(
            key=lambda item: (
                item[0],
                item[1].get("skill_score", 0),
                item[1].get("experience_score", 0),
            ),
            reverse=True,
        )
        qualified_profiles = [item for item in scored_profiles if item[0] >= quality_floor]
        if len(qualified_profiles) < min_recommended:
            qualified_profiles = scored_profiles[:min_recommended]

        diversified_profiles = []
        title_counts: dict[str, int] = {}
        max_per_title = 6
        for item in qualified_profiles:
            title = item[2].title
            if title_counts.get(title, 0) >= max_per_title:
                continue
            diversified_profiles.append(item)
            title_counts[title] = title_counts.get(title, 0) + 1
            if len(diversified_profiles) >= max_recommended:
                break

        logger.info(
            "推荐岗位统计: 总岗位数=%s, 质量线以上岗位数=%s, 多样化后=%s, 项目数=%s, 实习数=%s, 将返回=%s",
            len(all_profiles),
            len([item for item in scored_profiles if item[0] >= quality_floor]),
            len(diversified_profiles),
            experience["project_count"],
            experience["internship_count"],
            min(len(diversified_profiles), max_recommended),
        )

        for _, scoring, jp, posting in diversified_profiles:
            company_name = posting.company_name if posting else "推荐岗位"
            salary_range = posting.salary_range if posting and posting.salary_range else ""
            skills = jp.skill_requirements[:5] if jp.skill_requirements else []
            matched = list(dict.fromkeys(
                scoring["matched_skills"]
                + scoring["experience_tags"]
                + scoring["intent_tags"]
            ))[:6]
            missing = scoring["missing_skills"][:4]

            reason = generate_recommendation_reason(
                scoring=scoring,
                student_profile=student_profile,
                student_info={"major": student.major, "grade": student.grade},
                job_profile=jp,
                experience=experience,
            )

            jobs.append(RecommendedJobItem(
                job_code=jp.job_code,
                title=jp.title,
                company=company_name,
                salary=salary_range,
                location=posting.location if posting else "",
                industry=posting.industry if posting else "",
                company_size=posting.company_size if posting else "",
                ownership_type=posting.ownership_type if posting else "",
                summary=jp.summary or (posting.description if posting else ""),
                tags=skills,
                matched_tags=matched,
                missing_tags=missing,
                experience_tags=scoring["experience_tags"],
                reason=reason,
                match_score=scoring["score"],
                base_score=scoring["base_score"],
                experience_score=scoring["experience_score"],
                skill_score=scoring["skill_score"],
                potential_score=scoring["potential_score"],
            ))

    return RecommendedJobsResponse(items=jobs)


@router.get("/me/history")
def get_student_history(
    record_type: Optional[str] = Query(None, alias="type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Unified history endpoint with optional type filter.

    Supported type values: upload, profile, matching, path, report, chat, feedback.
    Returns all types when type is not specified.
    """
    VALID_TYPES = {"upload", "profile", "matching", "path", "report", "chat", "feedback"}
    if record_type and record_type not in VALID_TYPES:
        return {"items": []}

    student = db.scalar(select(Student).where(Student.user_id == current_user.id))
    if not student:
        return {"items": []}

    records = []
    run_ids = list(db.scalars(select(AnalysisRun.id).where(AnalysisRun.student_id == student.id)).all())
    profile_version_ids = list(db.scalars(select(ProfileVersion.id).where(ProfileVersion.student_id == student.id)).all())
    has_scoped_analysis = bool(run_ids or profile_version_ids)

    # --- Upload records ---
    if not record_type or record_type == "upload":
        file_type_label = {"resume": "简历", "certificate": "证书", "transcript": "成绩单", "other": "其他材料"}
        uploads = list(db.scalars(
            select(UploadedFile)
            .where(UploadedFile.owner_id == current_user.id)
            .order_by(UploadedFile.created_at.desc())
            .limit(20)
        ).all())
        for f in uploads:
            label = file_type_label.get(f.file_type, f.file_type)
            records.append({
                "id": f"upload-{f.id}",
                "type": "upload",
                "ref_id": f.id,
                "title": f"上传{label} — {f.file_name[:40]}",
                "desc": f"文件类型: {label}",
                "time": f.created_at.isoformat() if f.created_at else "",
                "source_file_id": f.id,
            })

    # --- Profile version records ---
    if not record_type or record_type == "profile":
        profiles = list(db.scalars(
            select(ProfileVersion)
            .where(ProfileVersion.student_id == student.id)
            .order_by(ProfileVersion.created_at.desc())
            .limit(20)
        ).all())
        for pv in profiles:
            file_ids = pv.uploaded_file_ids or []
            source_desc = f"基于 {len(file_ids)} 份材料生成" if file_ids else "基于手动输入生成"
            records.append({
                "id": f"profile-{pv.id}",
                "type": "profile",
                "ref_id": pv.id,
                "title": f"能力画像 — 版本 {pv.version_no}",
                "desc": source_desc,
                "time": pv.created_at.isoformat() if pv.created_at else "",
                "profile_version_id": pv.id,
                "uploaded_file_ids": file_ids,
            })

    # --- Matching records ---
    if not record_type or record_type == "matching":
        student_profile = db.scalar(
            select(StudentProfile).where(StudentProfile.student_id == student.id)
        )
        if student_profile:
            if has_scoped_analysis:
                match_query = select(MatchResult).where(MatchResult.student_id == student.id)
                scoped_conditions = []
                if run_ids:
                    scoped_conditions.append(MatchResult.analysis_run_id.in_(run_ids))
                if profile_version_ids:
                    scoped_conditions.append(MatchResult.profile_version_id.in_(profile_version_ids))
                match_query = match_query.where(or_(*scoped_conditions))
            else:
                match_query = select(MatchResult).where(MatchResult.student_profile_id == student_profile.id)
            matches = list(db.scalars(
                match_query
                .order_by(MatchResult.created_at.desc())
                .limit(20)
            ).all())

            for m in matches:
                jp = db.scalar(
                    select(JobProfile).where(JobProfile.id == m.job_profile_id).limit(1)
                )
                title = f"岗位匹配 — {jp.title}" if jp else "岗位匹配"
                desc = f"匹配度 {round(m.total_score, 1)}"
                records.append({
                    "id": f"match-{m.id}",
                    "type": "matching",
                    "ref_id": m.id,
                    "title": title,
                    "desc": desc,
                    "time": m.created_at.isoformat() if m.created_at else "",
                    "profile_version_id": m.profile_version_id,
                    "analysis_run_id": m.analysis_run_id,
                })

    # --- Path planning records ---
    if not record_type or record_type == "path":
        path_query = select(PathRecommendation).where(PathRecommendation.student_id == student.id)
        if has_scoped_analysis:
            scoped_conditions = []
            if run_ids:
                scoped_conditions.append(PathRecommendation.analysis_run_id.in_(run_ids))
            if profile_version_ids:
                scoped_conditions.append(PathRecommendation.profile_version_id.in_(profile_version_ids))
            path_query = path_query.where(or_(*scoped_conditions))
        paths = list(db.scalars(
            path_query
            .order_by(PathRecommendation.created_at.desc())
            .limit(10)
        ).all())

        for p in paths:
            jp = db.scalar(
                select(JobProfile).where(JobProfile.job_code == p.target_job_code).limit(1)
            )
            title = f"职业路径规划 — {jp.title}" if jp else f"职业路径规划 — {p.target_job_code}"
            records.append({
                "id": f"path-{p.id}",
                "type": "path",
                "ref_id": p.id,
                "title": title,
                "desc": "已生成职业发展路径",
                "time": p.created_at.isoformat() if p.created_at else "",
                "profile_version_id": p.profile_version_id,
                "match_result_id": p.match_result_id,
                "analysis_run_id": p.analysis_run_id,
            })

    # --- Report records ---
    if not record_type or record_type == "report":
        report_query = select(CareerReport).where(CareerReport.student_id == student.id)
        if has_scoped_analysis:
            scoped_conditions = []
            if run_ids:
                scoped_conditions.append(CareerReport.analysis_run_id.in_(run_ids))
            if profile_version_ids:
                scoped_conditions.append(CareerReport.profile_version_id.in_(profile_version_ids))
            report_query = report_query.where(or_(*scoped_conditions))
        reports = list(db.scalars(
            report_query
            .order_by(CareerReport.created_at.desc())
            .limit(20)
        ).all())

        for r in reports:
            jp = db.scalar(
                select(JobProfile).where(JobProfile.job_code == r.target_job_code).limit(1)
            )
            title = f"职业规划报告 — {jp.title}" if jp else f"职业规划报告 — {r.target_job_code}"
            desc = f"报告状态: {r.status}"
            if r.status == "completed":
                desc = "已完成职业规划报告"
            elif r.status == "edited":
                desc = "已编辑职业规划报告"
            records.append({
                "id": f"report-{r.id}",
                "type": "report",
                "ref_id": r.id,
                "title": title,
                "desc": desc,
                "time": r.created_at.isoformat() if r.created_at else "",
                "profile_version_id": r.profile_version_id,
                "match_result_id": r.match_result_id,
                "analysis_run_id": r.analysis_run_id,
            })

    # --- Chat records ---
    if not record_type or record_type == "chat":
        chat_msgs = list(db.scalars(
            select(ChatMessageRecord)
            .where(ChatMessageRecord.user_id == current_user.id, ChatMessageRecord.role == "user")
            .order_by(ChatMessageRecord.created_at.desc())
            .limit(30)
        ).all())

        for msg in chat_msgs:
            summary = msg.content[:50] + ("..." if len(msg.content) > 50 else "")
            records.append({
                "id": f"chat-{msg.id}",
                "type": "chat",
                "ref_id": msg.id,
                "title": f"AI 对话 — {summary}",
                "desc": "AI 职业规划咨询" + ("（含简历上下文）" if msg.has_context else ""),
                "time": msg.created_at.isoformat() if msg.created_at else "",
            })

    # --- Teacher feedback records ---
    if not record_type or record_type == "feedback":
        feedbacks = list(db.scalars(
            select(FollowupRecord)
            .where(FollowupRecord.student_id == student.id)
            .order_by(FollowupRecord.created_at.desc())
            .limit(20)
        ).all())
        for fb in feedbacks:
            fb_type_label = {"advice": "指导建议", "comment": "点评反馈", "followup": "跟进记录"}.get(fb.record_type, fb.record_type)
            summary = fb.content[:50] + ("..." if len(fb.content) > 50 else "") if fb.content else ""
            records.append({
                "id": f"feedback-{fb.id}",
                "type": "feedback",
                "ref_id": fb.id,
                "title": f"教师反馈 — {fb_type_label}",
                "desc": summary or fb_type_label,
                "time": fb.created_at.isoformat() if fb.created_at else "",
            })

    records.sort(key=lambda x: x["time"], reverse=True)

    custom_titles = db.scalars(
        select(HistoryTitle).where(HistoryTitle.user_id == current_user.id)
    ).all()
    title_map = {f"{ct.record_type}-{ct.ref_id}": ct.custom_title for ct in custom_titles}

    for rec in records:
        key = f"{rec['type']}-{rec['ref_id']}"
        if key in title_map and title_map[key]:
            rec["title"] = title_map[key]

    return {"items": records[:50]}


class RenameHistoryRequest(BaseModel):
    record_type: str = Field(..., min_length=1, max_length=40)
    ref_id: int = Field(..., gt=0)
    custom_title: str = Field(..., min_length=1, max_length=200)


@router.patch("/me/history/rename")
def rename_history_item(
    payload: RenameHistoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    existing = db.scalar(
        select(HistoryTitle).where(
            HistoryTitle.user_id == current_user.id,
            HistoryTitle.record_type == payload.record_type,
            HistoryTitle.ref_id == payload.ref_id,
        )
    )
    if existing:
        existing.custom_title = payload.custom_title
    else:
        db.add(HistoryTitle(
            user_id=current_user.id,
            record_type=payload.record_type,
            ref_id=payload.ref_id,
            custom_title=payload.custom_title,
        ))
    db.commit()
    return {"ok": True}


@router.get("/me/history/detail")
def get_history_detail(
    record_type: str = Query(..., alias="type"),
    ref_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Return detail payload for a specific history record, scoped to the authenticated user.

    Supported types: upload, profile, matching, path, report, feedback.
    Chat is handled by the dedicated /chat/history/{message_id} endpoint.
    """
    student = db.scalar(select(Student).where(Student.user_id == current_user.id))
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="学生信息不存在")

    if record_type == "upload":
        f = db.get(UploadedFile, ref_id)
        if not f or f.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
        return {
            "type": "upload",
            "ref_id": f.id,
            "file_name": f.file_name,
            "file_type": f.file_type,
            "created_at": f.created_at.isoformat() if f.created_at else "",
            "meta": f.meta_json or {},
        }

    elif record_type == "profile":
        pv = db.get(ProfileVersion, ref_id)
        if not pv or pv.student_id != student.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="画像版本不存在")
        return {
            "type": "profile",
            "ref_id": pv.id,
            "version_no": pv.version_no,
            "snapshot": pv.snapshot_json,
            "uploaded_file_ids": pv.uploaded_file_ids or [],
            "created_at": pv.created_at.isoformat() if pv.created_at else "",
        }

    elif record_type == "matching":
        m = db.get(MatchResult, ref_id)
        if not m:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="匹配记录不存在")
        # Verify ownership: match result must belong to this student's profile
        sp = db.scalar(select(StudentProfile).where(StudentProfile.id == m.student_profile_id))
        if not sp or sp.student_id != student.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="匹配记录不存在")
        return {
            "type": "matching",
            "ref_id": m.id,
            "total_score": m.total_score,
            "summary": m.summary or "",
            "strengths": m.strengths_json or [],
            "gap_items": m.gaps_json or [],
            "suggestions": m.suggestions_json or [],
            "created_at": m.created_at.isoformat() if m.created_at else "",
        }

    elif record_type == "path":
        p = db.get(PathRecommendation, ref_id)
        if not p or p.student_id != student.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="路径规划记录不存在")
        return {
            "type": "path",
            "ref_id": p.id,
            "target_job_code": p.target_job_code,
            "primary_path": p.primary_path_json or [],
            "alternate_paths": p.alternate_paths_json or [],
            "gaps": p.gaps_json or [],
            "recommendations": p.recommendations_json or [],
            "created_at": p.created_at.isoformat() if p.created_at else "",
        }

    elif record_type == "report":
        r = db.get(CareerReport, ref_id)
        if not r or r.student_id != student.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告不存在")
        return {
            "type": "report",
            "ref_id": r.id,
            "job_code": r.target_job_code,
            "status": r.status,
            "content": r.content_json,
            "markdown_content": r.markdown_content,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        }

    elif record_type == "feedback":
        fb = db.get(FollowupRecord, ref_id)
        if not fb or fb.student_id != student.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="反馈记录不存在")
        return {
            "type": "feedback",
            "ref_id": fb.id,
            "record_type": fb.record_type,
            "content": fb.content,
            "meta": fb.meta_json or {},
            "created_at": fb.created_at.isoformat() if fb.created_at else "",
        }

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的记录类型: {record_type}")


# --- Teacher Feedback for Students ---

@router.get("/me/teacher-feedback")
def get_teacher_feedback(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Student views teacher feedback (only visible_to_student=True comments)."""
    student = db.scalar(select(Student).where(Student.user_id == current_user.id))
    if not student:
        return {"items": []}

    from datetime import datetime, timezone
    comments = db.scalars(
        select(TeacherComment)
        .where(
            TeacherComment.student_id == student.id,
            TeacherComment.visible_to_student == True,
        )
        .order_by(TeacherComment.created_at.desc())
    ).all()

    items = []
    for c in comments:
        teacher_user = db.scalar(select(User).where(User.id == c.teacher_id))
        items.append({
            "id": c.id,
            "teacher_name": teacher_user.full_name if teacher_user else "教师",
            "report_id": c.report_id,
            "comment": c.comment,
            "priority": c.priority,
            "student_read_at": c.student_read_at.isoformat() if c.student_read_at else None,
            "follow_up_status": c.follow_up_status,
            "next_follow_up_date": c.next_follow_up_date.isoformat() if c.next_follow_up_date else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return {"items": items}


@router.post("/me/teacher-feedback/{comment_id}/read")
def mark_feedback_read(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Student marks a teacher feedback as read."""
    from datetime import datetime, timezone
    comment = db.scalar(select(TeacherComment).where(TeacherComment.id == comment_id))
    if not comment:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="反馈不存在")

    student = db.scalar(select(Student).where(Student.user_id == current_user.id))
    if not student or comment.student_id != student.id:
        raise_resource_forbidden()

    comment.student_read_at = datetime.now(timezone.utc)
    db.commit()

    return {"ok": True, "read_at": comment.student_read_at.isoformat()}
