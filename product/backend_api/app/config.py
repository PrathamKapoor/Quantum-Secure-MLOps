"""Product API configuration.

Environment-driven, read-only. Research paths keep coming from the frozen
``qsmlops.config.PlatformConfig``; this module only configures the product
HTTP layer itself.
"""
from __future__ import annotations

import os


class Settings:
    title: str = "Guardrailed Agentic MLOps API"
    description: str = (
        "Read-only product boundary over the locked research/MLOps system. "
        "Lifecycle mutations are not exposed."
    )
    version: str = "1.0.0"

    # Comma-separated list; defaults to the Vite dev server origin.
    cors_origins: list[str]

    # Interactive docs (/docs, /redoc, /openapi.json). No repository policy
    # disables them today, so they stay on by default for development and
    # can be turned off in a deployment via env var.
    enable_docs: bool

    def __init__(self) -> None:
        raw = os.environ.get(
            "PRODUCT_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        )
        self.cors_origins = [o.strip() for o in raw.split(",") if o.strip()]
        self.enable_docs = os.environ.get(
            "PRODUCT_ENABLE_DOCS", "true"
        ).strip().lower() not in {"0", "false", "no"}


def get_settings() -> Settings:
    return Settings()
