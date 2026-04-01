from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "CareerPilot"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    jwt_secret_key: str = "your_secret_key_here_change_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    database_url: str = "sqlite+pysqlite:////tmp/careerpilot.db"
    test_database_url: str = "sqlite+pysqlite:///:memory:"
    redis_url: str = "redis://localhost:6379/0"
    scheduler_timezone: str = "Asia/Shanghai"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "careerpilot"
    minio_secure: bool = False
    local_storage_root: str = "backend/uploads"
    report_export_dir: str = "exports"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "careerpilot123"

    llm_provider: Literal["mock", "ernie"] = "mock"
    ocr_provider: Literal["mock", "paddle"] = "mock"
    ragflow_provider: Literal["mock", "ragflow"] = "mock"
    graph_provider: Literal["mock", "neo4j"] = "mock"
    storage_provider: Literal["local", "minio"] = "local"

    ernie_api_key: str = ""
    ernie_secret_key: str = ""
    ernie_base_url: str = "https://aistudio.baidu.com/llm/lmapi/v3"
    ernie_model: str = "ernie-4.5-turbo-128k"
    paddle_ocr_service_url: str = ""
    ragflow_base_url: str = ""
    ragflow_api_key: str = ""

    data_dir: Path = ROOT_DIR / "data"

    @property
    def local_storage_path(self) -> Path:
        return ROOT_DIR / self.local_storage_root

    @property
    def export_path(self) -> Path:
        return ROOT_DIR / self.report_export_dir


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.local_storage_path.mkdir(parents=True, exist_ok=True)
    settings.export_path.mkdir(parents=True, exist_ok=True)
    return settings
