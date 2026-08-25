"""Alert evaluation for the monitoring foundation (Phase 7).

Deterministic rule evaluation over evidence the platform already produces:
recorded model metrics (against the deployment thresholds used everywhere
else), drift-engine summaries, and trust decisions. No external alerting
infrastructure is invented here; alerts are structured records an operator
or the API can consume.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from qsmlops.config import DEFAULT_METRIC_THRESHOLDS

_LEVELS = ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")

_DRIFT_ALERT = {
    "CRITICAL": ("CRITICAL", "DRIFT_CRITICAL"),
    "HIGH": ("HIGH", "DRIFT_HIGH"),
    "MEDIUM": ("MEDIUM", "DRIFT_MEDIUM"),
}

_TRUST_ALERT = {
    "BLOCKED": ("CRITICAL", "TRUST_BLOCKED"),
    "QUARANTINED": ("CRITICAL", "TRUST_QUARANTINED"),
    "REVIEW_REQUIRED": ("HIGH", "TRUST_REVIEW_REQUIRED"),
}


@dataclass
class Alert:
    level: str
    code: str
    model_id: str
    detail: str = ""
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {"level": self.level, "code": self.code,
                "model_id": self.model_id, "detail": self.detail,
                "ts": self.ts}


def evaluate(
    model_id: str,
    metrics: dict | None = None,
    drift_summary: dict | None = None,
    trust_decision: str | None = None,
    thresholds: dict | None = None,
) -> list[Alert]:
    """Evaluate monitoring rules; returns open alerts (empty == healthy)."""
    thresholds = {**DEFAULT_METRIC_THRESHOLDS, **(thresholds or {})}
    metrics = metrics or {}
    alerts: list[Alert] = []

    r2 = metrics.get("r2")
    mse = metrics.get("mse")
    if r2 is not None and mse is not None:
        r2_bad = r2 < thresholds["min_r2"]
        mse_bad = mse > thresholds["max_mse"]
        if r2_bad or mse_bad:
            level = "CRITICAL" if (r2_bad and mse_bad) else "HIGH"
            alerts.append(Alert(
                level, "PERFORMANCE_DEGRADED", model_id,
                detail=(f"r2={r2} (min {thresholds['min_r2']}), "
                        f"mse={mse} (max {thresholds['max_mse']})"),
            ))

    sev = str((drift_summary or {}).get("max_severity", "NONE")).upper()
    if sev in _DRIFT_ALERT:
        level, code = _DRIFT_ALERT[sev]
        alerts.append(Alert(level, code, model_id, detail=json_detail(drift_summary)))

    if trust_decision in _TRUST_ALERT:
        level, code = _TRUST_ALERT[trust_decision]
        alerts.append(Alert(level, code, model_id,
                            detail=f"trust decision {trust_decision}"))

    return alerts


def json_detail(summary: dict | None) -> str:
    import json as _json

    try:
        return _json.dumps(summary or {}, sort_keys=True)
    except (TypeError, ValueError):
        return str(summary)


def worst_level(alerts: list[Alert]) -> str:
    """Highest severity present, or 'NONE'."""
    order = {lvl: i for i, lvl in enumerate(_LEVELS)}
    worst = "NONE"
    for a in alerts:
        if order.get(a.level, -1) > order.get(worst, -1):
            worst = a.level
    return worst
