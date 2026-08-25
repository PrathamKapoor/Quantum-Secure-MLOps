from fastapi import APIRouter, HTTPException

from ..schemas.drift import DriftEvent
from ..services import drift_service

router = APIRouter()


@router.get("/events", response_model=list[DriftEvent])
async def get_drift_events_list():
    return drift_service.get_drift_events()


@router.get("/events/{event_id}", response_model=DriftEvent)
async def get_drift_event_detail(event_id: str):
    event = drift_service.get_drift_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Drift event '{event_id}' not found.")
    return event
