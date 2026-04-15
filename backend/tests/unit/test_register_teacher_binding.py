from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import CareerReport, Student, Teacher, TeacherStudentLink, User


def test_student_register_with_teacher_code_creates_link(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": "new_student_bound",
            "password": "demo123",
            "full_name": "新同学",
            "role": "student",
            "email": "new_student_bound@careerpilot.local",
            "teacher_code": "teacher_demo",
        },
    )
    assert resp.status_code == 200, resp.text

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "new_student_bound"))
        assert user is not None
        assert user.email == "new_student_bound@careerpilot.local"

        student = db.scalar(select(Student).where(Student.user_id == user.id))
        assert student is not None

        teacher_user = db.scalar(select(User).where(User.username == "teacher_demo"))
        teacher = db.scalar(select(Teacher).where(Teacher.user_id == teacher_user.id))
        link = db.scalar(
            select(TeacherStudentLink).where(
                TeacherStudentLink.teacher_id == teacher.id,
                TeacherStudentLink.student_id == student.id,
                TeacherStudentLink.status == "active",
            )
        )
        assert link is not None
        assert link.source == "invite_code"
        assert link.group_name == "自助注册"


def test_student_register_with_unknown_teacher_code_fails(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": "new_student_unbound",
            "password": "demo123",
            "full_name": "未绑定同学",
            "role": "student",
            "email": "new_student_unbound@careerpilot.local",
            "teacher_code": "missing_teacher",
        },
    )
    assert resp.status_code == 400
    assert "未找到对应老师" in resp.text


def test_student_info_update_syncs_to_teacher_view(client):
    register_resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": "profile_sync_student",
            "password": "demo123",
            "full_name": "待完善同学",
            "role": "student",
            "email": "profile_sync_student@careerpilot.local",
        },
    )
    assert register_resp.status_code == 200, register_resp.text
    student_token = register_resp.json()["access_token"]

    update_resp = client.put(
        "/api/v1/students/me",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "full_name": "同步测试学生",
            "email": "profile_sync_updated@careerpilot.local",
            "major": "软件工程",
            "grade": "大三",
            "career_goal": "前端开发工程师",
            "teacher_code": "teacher_demo",
        },
    )
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()
    assert updated["major"] == "软件工程"
    assert updated["grade"] == "大三"
    assert updated["career_goal"] == "前端开发工程师"
    assert updated["teacher"]["teacher_username"] == "teacher_demo"

    teacher_login = client.post("/api/v1/auth/login", json={
        "username": "teacher_demo",
        "password": "demo123",
    })
    assert teacher_login.status_code == 200, teacher_login.text
    teacher_token = teacher_login.json()["access_token"]

    reports_resp = client.get(
        "/api/v1/teacher/students/reports",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert reports_resp.status_code == 200, reports_resp.text
    rows = reports_resp.json()["data"]
    synced = next((row for row in rows if row["name"] == "同步测试学生"), None)
    assert synced is not None
    assert synced["major"] == "软件工程"
    assert synced["grade"] == "大三"
    assert synced["career_goal"] == "前端开发工程师"

    with SessionLocal() as db:
        report = CareerReport(
            student_id=updated["student_id"],
            target_job_code="J-FE-001",
            status="generated",
            content_json={
                "student_summary": {},
                "resume_summary": {},
                "capability_profile": {},
                "target_job_analysis": {},
                "matching_analysis": {},
                "gap_analysis": {},
                "career_path": {},
                "short_term_plan": {},
                "mid_term_plan": {},
                "evaluation_cycle": {},
                "teacher_comments": {},
            },
            markdown_content="# 同步测试报告\n\n教师端可查看。",
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        report_id = report.id

    list_resp = client.get(
        f"/api/v1/teacher/students/{updated['student_id']}/reports",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert list_resp.status_code == 200, list_resp.text
    report_rows = list_resp.json()["data"]
    assert any(row["report_id"] == report_id for row in report_rows)


def test_teacher_info_can_be_updated(client):
    login = client.post("/api/v1/auth/login", json={
        "username": "teacher_demo",
        "password": "demo123",
    })
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    resp = client.put(
        "/api/v1/teacher/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "王老师更新",
            "email": "teacher_updated@careerpilot.local",
            "department": "计算机学院",
            "title": "就业指导老师",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["username"] == "teacher_demo"
    assert data["full_name"] == "王老师更新"
    assert data["email"] == "teacher_updated@careerpilot.local"
    assert data["department"] == "计算机学院"
    assert data["title"] == "就业指导老师"
