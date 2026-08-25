"""Supervisor decision types and risk scoring."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from qsmlops.agents.base import Observation
from qsmlops.config import SEVERITY_WEIGHTS


class Decision(str, Enum):
    ACCEPT = "ACCEPT"
    DEPLOY = "DEPLOY"
    RETRAIN = "RETRAIN"
    ROLLBACK = "ROLLBACK"
    QUARANTINE = "QUARANTINE"
    ROTATE_KEYS = "ROTATE_KEYS"
    BLOCK_DEPLOYMENT = "BLOCK_DEPLOYMENT"
    ESCALATE = "ESCALATE"


@dataclass
class SupervisorPolicy:
    quarantine_risk: float = 40.0
    block_risk: float = 55.0
    escalate_risk: float = 70.0
    max_auto_recoveries: int = 2

    def decide(self, risk_score: float) -> Decision:
        if risk_score >= self.escalate_risk:
            return Decision.ESCALATE
        if risk_score >= self.block_risk:
            return Decision.BLOCK_DEPLOYMENT
        if risk_score >= self.quarantine_risk:
            return Decision.QUARANTINE
        return Decision.ACCEPT


@dataclass
class DecisionReport:
    decision: Decision
    risk_score: float
    category_scores: dict[str, float]
    observations: list[dict]
    rationale: str
    subject_id: str = ""
    facts: dict = field(default_factory=dict)
    policy_decisions: list[dict] = field(default_factory=list)
    scores: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "risk_score": round(self.risk_score, 2),
            "category_scores": {k: round(v, 2) for k, v in self.category_scores.items()},
            "rationale": self.rationale,
            "subject_id": self.subject_id,
            "observations": self.observations,
            "scores": {k: round(v, 2) for k, v in self.scores.items()},
            "policy_decisions": self.policy_decisions,
            "facts": self.facts,
        }


def observation_risk(observation: Observation) -> float:
    """Weighted sum of failed findings for a single observation (capped at 100)."""
    total = sum(
        SEVERITY_WEIGHTS.get(f.severity, 1.0)
        for f in observation.findings
        if not f.passed
    )
    return min(100.0, total)


def aggregate_risk(observations: list[Observation]) -> tuple[float, dict[str, float]]:
    """Aggregate per-agent risk into a global score.

    Global score is the max of category scores blended with the mean, so a
    single catastrophic signal dominates while many moderate signals still
    accumulate.
    """
    per_agent = {
        obs.agent: observation_risk(obs) for obs in observations
    }
    if not per_agent:
        return 0.0, {}
    worst = max(per_agent.values())
    mean = sum(per_agent.values()) / len(per_agent)
    global_score = min(100.0, 0.6 * worst + 0.4 * mean)
    return global_score, per_agent
