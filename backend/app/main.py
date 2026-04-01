from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import *  # noqa: F401,F403
from app.services.bootstrap import create_service_container, initialize_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    Base.metadata.create_all(bind=engine)
    container = create_service_container()
    app.state.container = container
    with SessionLocal() as db:
        await initialize_demo_data(db, container)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        description="CareerPilot - 基于 AI 的大学生职业规划智能体",
        lifespan=lifespan,
    )

    # Parse allowed origins from settings
    allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/")
    def root():
        return {"project": settings.project_name, "docs": "/docs"}

    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=False)
