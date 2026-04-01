import pytest

from app.services.bootstrap import create_service_container, initialize_demo_data


@pytest.mark.asyncio
async def test_graph_query_supports_transition_and_promotion(db_session):
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    result = await container.graph_query_service.query_job("J-FE-001")
    assert result["promotion_paths"]
    assert len(result["transition_paths"]) >= 2
    assert result["required_skills"]

