"""Application entry point: composition root for the platform API.

Builds the :class:`ServiceContainer` from :func:`load_settings`, initializes
platform state (directories, database migrations, bootstrap keys) and
assembles a FastAPI application with foundation + dashboard routes.

Run with::

    python -m qsmlops.app --env development
    python -m qsmlops.app --env production --port 8080

or programmatically::

    from qsmlops.app import build_app
    app = build_app()
"""
from __future__ import annotations

import argparse
from typing import Any

from qsmlops import __version__
from qsmlops.core.logging import configure_logging, get_logger
from qsmlops.core.settings import load_settings

log = get_logger(__name__)


def build_container(env: str | None = None, **overrides: Any):
    """Load settings, wire services and initialize platform state."""
    from qsmlops.core.context import ServiceContainer

    settings = load_settings(env=env, overrides=overrides)
    configure_logging(settings.log_level, json_format=settings.json_logs)
    container = ServiceContainer(settings)
    container.initialize()
    log.info(
        "platform initialized",
        extra={"event": "platform.initialized", "service": "app"},
    )
    return container


def build_app(container=None, env: str | None = None):
    """Create the FastAPI application with all routes registered."""
    from fastapi import FastAPI

    if container is None:
        container = build_container(env=env)

    from qsmlops.api.app import register_dashboard_routes
    from qsmlops.api.foundation import register_foundation_routes

    app = FastAPI(
        title="Quantum-Secure Agentic MLOps Pipeline Management System",
        version=__version__,
    )
    app.state.container = container

    register_foundation_routes(
        app,
        settings=container.settings,
        identity_service=container.get("identity_service"),
        audit_service=container.get("audit_service"),
        container=container,
    )
    register_dashboard_routes(app, container.get("pipeline"))
    return app


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="qsmlops platform server")
    parser.add_argument("--env", default=None, help="environment profile")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--home", default=None, help="platform home directory")
    args = parser.parse_args(argv)

    overrides: dict[str, Any] = {}
    if args.host:
        overrides["api.host"] = args.host
    if args.port:
        overrides["api.port"] = args.port
    if args.home:
        overrides["home"] = args.home

    container = build_container(env=args.env, **overrides)
    settings = container.settings
    app = build_app(container)

    import uvicorn

    uvicorn.run(app, host=settings.api.host, port=settings.api.port, log_level="warning")


if __name__ == "__main__":
    main()
