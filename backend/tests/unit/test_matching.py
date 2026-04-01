import pytest

from app.schemas.profile import ManualStudentInput
from app.services.bootstrap import create_service_container, initialize_demo_data


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

