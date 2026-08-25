from pydantic import BaseModel


class DriftEvent(BaseModel):
    event_id: str
    timestamp: float | str | None = None
    target: str | None = None
    drift_type: str | None = None
    severity: str | None = None
    score: float | None = None
    explanation_reference: str | None = None
    reason: str | None = None
    ledger_seq: int | None = None


class GovernanceEvent(BaseModel):
    timestamp: float | str | None = None
    seq: int | None = None
    type: str
    actor: str | None = None
    target: str | None = None
    evidence_ref: str | None = None
    reason: str | None = None
    details: dict | None = None
