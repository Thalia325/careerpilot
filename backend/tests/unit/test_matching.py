import pytest
from sqlalchemy import select

from app.models import JobPosting, JobProfile
from app.schemas.profile import ManualStudentInput
from app.services.matching.scoring import score_professional_skills
from app.services.bootstrap import create_service_container, initialize_demo_data


def test_professional_skills_scores_related_skill_families():
    score, evidence = score_professional_skills(
        {"skills": ["PyTorch", "深度学习", "SQL"]},
        {"skill_requirements": ["TensorFlow", "机器学习", "数据分析"]},
    )

    assert score >= 50
    assert evidence["related_skills"]
    assert "TensorFlow" in evidence["missing_skills"]


@pytest.mark.asyncio
async def test_four_dimension_matching(db_session):
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="专注前端工程",
            skills=["JavaScript", "TypeScript", "React", "Next.js", "HTML"],
            certificates=["英语四级"],
            projects=["职业规划平台"],
            internships=["前端开发实习"],
        ),
    )
    result = container.matching_service.analyze_match(db_session, 1, "J-FE-001")
    assert result["total_score"] > 0
    assert len(result["dimensions"]) == 4
    assert any(item["dimension"] == "职业技能" for item in result["dimensions"])


@pytest.mark.asyncio
async def test_matching_creates_fallback_job_profile_for_imported_posting(db_session):
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="新岗位",
            self_introduction="具备项目开发经验",
            skills=["Python", "SQL"],
            certificates=[],
            projects=["数据看板"],
            internships=[],
        ),
    )
    db_session.add(
        JobPosting(
            job_code="J-NEW-FALLBACK-001",
            title="智能应用开发工程师",
            location="西安",
            salary_range="10-15K",
            company_name="测试企业",
            industry="信息化服务",
            company_size="100-499人",
            ownership_type="民营",
            description="负责智能应用开发、接口联调和数据处理。",
            company_intro="测试企业",
        )
    )
    db_session.commit()

    result = container.matching_service.analyze_match(db_session, 1, "J-NEW-FALLBACK-001")

    created_profile = db_session.scalar(
        select(JobProfile).where(JobProfile.job_code == "J-NEW-FALLBACK-001")
    )
    assert created_profile is not None
    assert result["job_code"] == "J-NEW-FALLBACK-001"
    assert result["total_score"] > 0
