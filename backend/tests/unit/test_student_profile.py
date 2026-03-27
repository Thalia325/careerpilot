import pytest

from app.schemas.profile import ManualStudentInput
from app.services.bootstrap import create_service_container
from app.services.bootstrap import initialize_demo_data


@pytest.mark.asyncio
async def test_student_profile_dual_input(db_session):
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    result = await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="我希望从事前端研发",
            skills=["JavaScript", "React", "Next.js"],
            certificates=["英语四级"],
            projects=["CareerPilot"],
            internships=["前端开发实习"],
        ),
    )
    assert result["skills"]
    assert result["completeness_score"] > 0
    assert result["competitiveness_score"] > 0
    assert result["evidence"]

