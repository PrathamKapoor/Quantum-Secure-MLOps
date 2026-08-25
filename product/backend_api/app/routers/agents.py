from fastapi import APIRouter

from ..schemas.agent import AgentExplanation, ExplainRequest
from ..services.agent_service import get_agent_explanation

router = APIRouter()


@router.post("/explain", response_model=AgentExplanation)
async def explain(request: ExplainRequest):
    """Bounded decision-support explanation.

    Explanatory only: retrieves evidence and explains decisions. Requests for
    protected lifecycle actions are refused (never executed) — see
    services/agent_service.classify_protected_action.
    """
    return get_agent_explanation(request.query)
