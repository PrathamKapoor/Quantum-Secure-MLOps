from fastapi import APIRouter

from ..services import governance_service

router = APIRouter()


@router.get("/events")
async def get_governance_events_list():
    """Full audit timeline (decisions + lifecycle transitions)."""
    return governance_service.get_governance_events()


@router.get("/decisions")
async def get_governance_decisions_list():
    """Decision/packet records only (the REQUEST→EVALUATION→DECISION chain)."""
    return governance_service.get_governance_decisions()
