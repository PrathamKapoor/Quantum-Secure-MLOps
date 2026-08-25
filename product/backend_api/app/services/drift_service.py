"""Read-only drift-event access built on the evidence ledger.

Events carry a stable identifier (ledger entry-hash prefix) so the API can
serve both the timeline and single-event lookups without inventing state.
"""
from __future__ import annotations

from qsmlops.config import PlatformConfig
from qsmlops.evidence.ledger import EvidenceLedger

EVENT_ID_LEN = 16

_ledger = None


def get_ledger():
    global _ledger
    if _ledger is None:
        config = PlatformConfig()
        _ledger = EvidenceLedger(config.ledger_path)
    return _ledger


def _event_from_entry(entry: dict) -> dict:
    record = entry["record"]
    summary = record.get("summary", {}) or {}
    entry_hash = entry.get("entry_hash") or ""
    return {
        "event_id": entry_hash[:EVENT_ID_LEN] or f"seq-{entry.get('seq')}",
        "timestamp": record.get("timestamp", entry.get("timestamp")),
        "target": record.get("model"),
        "drift_type": summary.get("drift_type", "unknown"),
        "severity": summary.get("max_severity", "UNKNOWN"),
        "score": summary.get("score", 0.0),
        "explanation_reference": entry_hash or str(entry.get("seq")),
        "reason": record.get("reason"),
        "ledger_seq": entry.get("seq"),
    }


def get_drift_events() -> list[dict]:
    events = []
    for entry in get_ledger().iter_entries():
        if entry["record"].get("type") == "drift_check":
            events.append(_event_from_entry(entry))
    events.sort(key=lambda e: e.get("ledger_seq") or 0, reverse=True)
    return events


def get_drift_event(event_id: str) -> dict | None:
    for entry in get_ledger().iter_entries():
        if entry["record"].get("type") != "drift_check":
            continue
        candidate = _event_from_entry(entry)
        if (
            candidate["event_id"] == event_id
            or candidate["explanation_reference"].startswith(event_id)
        ):
            return candidate
    return None
