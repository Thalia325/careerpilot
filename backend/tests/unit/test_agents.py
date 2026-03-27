import pytest

from app.services.bootstrap import create_service_container, initialize_demo_data


@pytest.mark.asyncio
async def test_main_controller_agent_build_job_profiles(db_session):
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    result = await container.controller_agent.execute(
        db_session,
        "build_job_profiles",
        {"job_codes": ["J-FE-001", "J-BE-001"]},
    )
    assert result["workflow"] == "build_job_profiles"
    assert result["result"]["job_codes"]

