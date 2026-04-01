import pytest

from app.schemas.profile import ManualStudentInput
from app.services.bootstrap import create_service_container, initialize_demo_data


@pytest.mark.asyncio
async def test_report_completeness_logic(db_session):
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="希望成为前端工程师",
            skills=["JavaScript", "TypeScript", "React", "Next.js"],
            certificates=["英语四级"],
            projects=["CareerPilot"],
            internships=["前端开发实习"],
        ),
    )
    report = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    completeness = container.report_service.check_completeness(db_session, report["report_id"])
    assert completeness["is_complete"] is True
    assert completeness["missing_sections"] == []

