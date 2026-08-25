from fastapi import APIRouter, HTTPException, Query

from ..schemas.forecast import ForecastStatus, TargetForecastSummary
from ..services import forecast_service

router = APIRouter()


@router.get("/status", response_model=ForecastStatus)
async def forecast_status():
    return forecast_service.get_forecast_status()


@router.get("/predictions/{target}")
async def forecast_predictions_for_target(target: str):
    """Per-target prediction rows from the frozen final-evaluation artifact."""
    target = target.upper()
    if target not in forecast_service.VALID_TARGETS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown target '{target}'. Valid targets: LOAD, WIND, PV.",
        )
    summary = forecast_service.get_target_summary(target)
    rows = forecast_service.get_predictions(target=target)
    return {**summary, "predictions": rows}


@router.get("/predictions")
async def forecast_predictions(
    target: str | None = Query(default=None, description="Optional LOAD/WIND/PV filter"),
    limit: int = Query(default=0, ge=0, description="Optional max row count"),
):
    data = forecast_service.get_predictions(target=target, limit=limit)
    if target is not None and not data:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown target '{target}'. Valid targets: LOAD, WIND, PV.",
        )
    return data


@router.get("/summary/{target}", response_model=TargetForecastSummary)
async def forecast_target_summary(target: str):
    summary = forecast_service.get_target_summary(target.upper())
    if summary is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown target '{target}'. Valid targets: LOAD, WIND, PV.",
        )
    return summary
