"""Shared FastAPI dependencies.

The research-system singletons (ledger, registry) intentionally live inside
their service modules as lazy singletons so that every route shares one
read-only handle. This module exposes cross-cutting dependency helpers only.
"""
from __future__ import annotations

from fastapi import Depends, Request


def get_settings(request: Request):
    """Attach the app-level settings object to handlers when needed."""
    return request.app.state.settings


SettingsDep = Depends(get_settings)
