import logging
import os
import sys

# Make the frozen research package importable regardless of launch directory.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .routers import (
    agents,
    drift,
    experiments,
    forecasts,
    governance,
    health,
    models,
    reports,
)

logger = logging.getLogger("product_api")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.title,
        description=settings.description,
        version=settings.version,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
    )
    app.state.settings = settings

    # Controlled CORS: explicit origin allow-list, credentials unused.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    # Structured error hygiene: never leak tracebacks to clients.
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(forecasts.router, prefix="/api/forecast", tags=["forecast"])
    app.include_router(models.router, prefix="/api/models", tags=["models"])
    app.include_router(experiments.router, prefix="/api/experiments", tags=["experiments"])
    app.include_router(drift.router, prefix="/api/drift", tags=["drift"])
    app.include_router(governance.router, prefix="/api/governance", tags=["governance"])
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

    @app.get("/", tags=["root"])
    async def root():
        return {
            "message": "Guardrailed Agentic MLOps product API",
            "docs": "/docs",
            "research_pipeline": "locked",
        }

    return app


app = create_app()
