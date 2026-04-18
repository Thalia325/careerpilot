from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import *  # noqa: F401,F403
from app.services.bootstrap import create_service_container, initialize_demo_data

logger = logging.getLogger(__name__)


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
        redirect_slashes=False,
    )

    # Parse allowed origins from settings
    allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    app.mount("/exports", StaticFiles(directory=settings.export_path), name="exports")

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
        response = JSONResponse(
            status_code=500,
            content={"detail": {"message": "服务器内部错误，请稍后重试", "error_code": "INTERNAL_ERROR"}},
        )
        # Explicitly add CORS headers so browser never blocks error responses
        origin = request.headers.get("origin", "")
        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
        return response

    @app.get("/")
    def root():
        return {"project": settings.project_name, "docs": "/docs"}

    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=False)
