"""Typed response schemas for the product API.

These formalize the existing JSON payloads; adding them changes no wire
format. Schemas are deliberately permissive where research records carry
dynamic fields.
"""
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    research_pipeline: str
    product_api: str


class ForecastStatus(BaseModel):
    targets: list[str]
    horizon: str
    models_locked: bool


class TargetForecastSummary(BaseModel):
    target: str
    horizon: str
    model: str | None = None
    count: int | None = None
    mae_from_absolute_errors: float | None = None
