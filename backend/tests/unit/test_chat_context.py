from app.api.routers.chat import _build_user_context
from app.models import MatchResult, PathRecommendation, Student, StudentProfile, UploadedFile, User


def test_build_user_context_includes_profile_match_and_ocr_raw_text(db_session):
    user = User(
        username="chat_context_student",
        password_hash="test",
        role="student",
        full_name="测试学生",
    )
    db_session.add(user)
    db_session.flush()

    student = Student(
        user_id=user.id,
        major="软件工程",
        grade="大三",
        career_goal="数据工程师",
    )
    db_session.add(student)
    db_session.flush()

    profile = StudentProfile(
        student_id=student.id,
        source_summary="OCR 生成画像",
        skills_json=["Python", "SQL"],
        certificates_json=[],
        capability_scores={"learning": 85},
        completeness_score=0.8,
        competitiveness_score=0.75,
    )
    db_session.add(profile)
    db_session.flush()

    db_session.add(
        MatchResult(
            student_profile_id=profile.id,
            job_profile_id=1,
            total_score=82.5,
            summary="适合数据工程方向",
            gaps_json=[],
            suggestions_json=["补强数据仓库项目"],
        )
    )
    db_session.add(
        PathRecommendation(
            student_id=student.id,
            target_job_code="J-DE-001",
            recommendations_json=[{"title": "完成一个 ETL 项目", "description": "沉淀项目成果"}],
        )
    )
    db_session.add(
        UploadedFile(
            owner_id=user.id,
            file_type="resume",
            file_name="resume.pdf",
            content_type="application/pdf",
            storage_key="resume.pdf",
            url="resume.pdf",
            meta_json={
                "ocr": {
                    "raw_text": "教育背景\n姓名：测试学生\n技能：Python SQL",
                    "structured_json": {"skills": ["Python", "SQL"]},
                }
            },
        )
    )
    db_session.commit()

    context = _build_user_context(db_session, user.id)

    assert "【学生能力画像】" in context
    assert "【最近匹配结果】" in context
    assert "【最近职业路径建议】" in context
    assert "教育背景" in context
    assert "Python" in context
    assert "档案完整度：80%" in context
    assert "竞争力评分：75%" in context
