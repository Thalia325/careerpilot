import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(tempfile.gettempdir()) / "careerpilot_test.db"

os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DB_PATH}"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["OCR_PROVIDER"] = "mock"
os.environ["RAGFLOW_PROVIDER"] = "mock"
os.environ["GRAPH_PROVIDER"] = "mock"
os.environ["STORAGE_PROVIDER"] = "local"

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import create_app


@pytest.fixture()
def prepare_database():
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture()
def client(prepare_database):
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(prepare_database):
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
