import os
import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("OCR_PROVIDER", "mock")
os.environ.setdefault("RAGFLOW_PROVIDER", "mock")
os.environ.setdefault("GRAPH_PROVIDER", "mock")
os.environ.setdefault("STORAGE_PROVIDER", "local")

from app.db.base import Base

# Use a unique DB per pytest worker to avoid Windows file locks
_TEST_DB_PATH = Path(tempfile.gettempdir()) / f"careerpilot_test_{uuid.uuid4().hex[:8]}.db"

_test_engine = create_engine(
    f"sqlite+pysqlite:///{_TEST_DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

# Patch global engine/SessionLocal so app.main.lifespan uses the test DB
import app.db.session as _db_mod
_db_mod.engine = _test_engine
_db_mod.SessionLocal = _TestSessionLocal

from app.main import create_app  # noqa: E402


@pytest.fixture()
def prepare_database():
    _test_engine.dispose()
    if _TEST_DB_PATH.exists():
        try:
            _TEST_DB_PATH.unlink()
        except PermissionError:
            pass
    Base.metadata.create_all(bind=_test_engine)
    yield
    try:
        _TestSessionLocal.close_all_sessions()
    except Exception:
        pass
    _test_engine.dispose()
    try:
        if _TEST_DB_PATH.exists():
            _TEST_DB_PATH.unlink()
    except PermissionError:
        pass


@pytest.fixture()
def client(prepare_database):
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(prepare_database):
    """Provide a DB session after running app lifespan (which seeds demo data)."""
    app = create_app()
    with TestClient(app):
        session = _TestSessionLocal()
        try:
            yield session
        finally:
            session.close()
