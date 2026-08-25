"""Operator-facing governance audit events, built read-only from the ledger."""

from qsmlops.config import PlatformConfig
from qsmlops.evidence.ledger import EvidenceLedger

_ledger = None


def get_ledger():
    global _ledger
    if _ledger is None:
        config = PlatformConfig()
        _ledger = EvidenceLedger(config.ledger_path)
    return _ledger


def _audit_type(record: dict) -> str:
    rtype = record.get("type")
    decision = record.get("decision")
    if rtype == "verification_packet":
        mapping = {
            "QUARANTINE": "MODEL_PROMOTION_BLOCKED",
            "VERIFIED": "VERIFICATION_PASSED",
            "DEPLOYED": "MODEL_DEPLOYED",
            "RETRAIN": "RETRAINING_APPROVED",
            "ROLLBACK": "ROLLBACK_COMPLETED",
        }
        return mapping.get(decision, f"GOVERNANCE_{decision or 'PACKET'}")
    if rtype == "state_transition":
        return f"STATE_TRANSITION_{record.get('to', 'UNKNOWN')}"
    return (rtype or "LEDGER_EVENT").upper()


def _extract_target(record: dict) -> str:
    for key in ("model", "version_id", "name", "packet_id"):
        if record.get(key):
            value = str(record[key])
            return value if len(value) <= 40 else value[:12] + "…"
    objective = record.get("objective")
    return str(objective)[:40] if objective else "system"


def get_governance_events():
    ledger = get_ledger()
    events = []
    for entry in ledger.iter_entries():
        record = entry["record"]
        events.append(
            {
                "timestamp": entry.get("timestamp"),
                "seq": entry.get("seq"),
                "type": _audit_type(record),
                "actor": record.get("actor", "system"),
                "target": _extract_target(record),
                "evidence_ref": (entry.get("entry_hash") or "")[:16],
                "reason": record.get("reason") or record.get("objective") or record.get("decision"),
                "details": record,
            }
        )
    events.sort(key=lambda e: (e["seq"] if e["seq"] is not None else 0), reverse=True)
    return events


DECISION_RECORD_TYPES = {"verification_packet", "registration", "dataset_provisioned"}


def get_governance_decisions():
    """Subset of audit events representing explicit decisions/packets
    (REQUEST -> EVALUATION -> DECISION chain outcomes), excluding pure
    lifecycle state transitions."""
    return [e for e in get_governance_events()
            if e["details"].get("type") in DECISION_RECORD_TYPES]
