from app.services.bootstrap import create_service_container


def test_mock_provider_container_creation():
    container = create_service_container()
    assert container.file_service is not None
    assert container.job_import_service is not None
    assert container.report_service is not None

