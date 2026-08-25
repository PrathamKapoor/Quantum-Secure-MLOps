from pydantic import BaseModel, Field


class ExplainRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class AgentExplanation(BaseModel):
    kind: str  # "explanation" | "blocked_action"
    query: str
    explanation: str
    rule: str | None = None
    source: str | None = None
    evidence: list = []
    requires_human_review: bool = False
    # Present only when kind == "blocked_action"
    action: str | None = None
    reason: str | None = None
    authority: str | None = None
    recommended_next_step: str | None = None
