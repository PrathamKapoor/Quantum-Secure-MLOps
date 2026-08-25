"""Bounded decision-support explanation service.

Read-only over the research system: classifies operator questions, refuses
protected lifecycle actions, and grounds every answer in real evidence-ledger
records. Adds no autonomous capabilities and never mutates state.
"""

from __future__ import annotations

import re

from qsmlops.config import PlatformConfig
from qsmlops.registry.registry import ModelRegistry
from qsmlops.artifacts.store import ArtifactStore
from qsmlops.crypto.keys import KeyStore
from qsmlops.evidence.ledger import EvidenceLedger

_config = None
_artifacts = None
_keystore = None
_ledger = None
_registry = None


def _init_singletons():
    global _config, _artifacts, _keystore, _ledger, _registry
    if _config is None:
        _config = PlatformConfig()
        _artifacts = ArtifactStore(_config.artifacts_dir)
        _keystore = KeyStore(_config.keys_dir)
        _ledger = EvidenceLedger(_config.ledger_path)
        _registry = ModelRegistry(
            _config.registry_path, _artifacts, _keystore, _ledger
        )


# ---------------------------------------------------------------------------
# Protected-action classification (refusal only — no execution paths exist)
# ---------------------------------------------------------------------------

GOVERNANCE_AUTHORITY = "Deterministic governance engine"
NEXT_STEP = "Request human review."

_POLITE_PREFIX = re.compile(
    r"^(?:please\s+|(?:can|could|would)\s+you\s+(?:please\s+)?|i\s+(?:want|would like)\s+to\s+|i'?d\s+like\s+to\s+)+",
    re.I,
)


def _leading_verb(query: str) -> str:
    stripped = _POLITE_PREFIX.sub("", query.strip(), count=1)
    parts = stripped.split(None, 1)
    return parts[0].lower().translate(str.maketrans("", "", ".,!?")) if parts else ""


_PROTECTED_ACTIONS = [
    {
        "action": "promote_model",
        "verbs": {"promote", "deploy", "ship", "push"},
        "topic": re.compile(r"\b(promot|challenger|champion|deploy)", re.I),
        "reason": "Agentic layer does not possess promotion authority.",
    },
    {
        "action": "rollback_model",
        "verbs": {"rollback", "roll"},
        "phrase": re.compile(r"\broll\s?back\b", re.I),
        "topic": re.compile(r"\broll\s?back\b", re.I),
        "reason": "Agentic layer does not possess rollback authority.",
    },
    {
        "action": "start_retraining",
        "verbs": {"retrain", "start", "trigger", "run", "launch"},
        "topic": re.compile(r"\bretrai?n|\btraining\b", re.I),
        "reason": "Agentic layer does not possess retraining authority.",
    },
    {
        "action": "change_features",
        "verbs": {"change", "modify", "add", "remove", "update", "swap", "replace"},
        "topic": re.compile(r"\bfeatures?\b", re.I),
        "reason": "Feature specifications are frozen in the locked pipeline.",
    },
    {
        "action": "change_policy",
        "verbs": {
            "change", "modify", "raise", "lower", "relax", "tighten",
            "update", "override", "adjust", "loosen",
        },
        "topic": re.compile(r"\b(threshold|polic(?:y|ies)|gates?)\b", re.I),
        "reason": "Governance policy is immutable from the agent layer.",
    },
]

_FINAL_TEST_PATTERN = re.compile(r"\bfinal[- ]?test\b|\bholdout\b|\btest\s+set\b", re.I)


def classify_protected_action(query: str) -> dict | None:
    """Return a refusal payload when the query *requests* a protected action.

    Explanatory questions about past decisions (e.g. "Explain the rollback
    decision") are NOT blocked — only imperative requests to perform the
    action are refused.
    """
    lowered = query.lower()

    # The final test set is sealed: any retrieval request is refused.
    if _FINAL_TEST_PATTERN.search(lowered):
        return {
            "kind": "blocked_action",
            "action": "access_final_test",
            "reason": (
                "The final test set is sealed until formal release; "
                "retrieval is not permitted."
            ),
            "authority": GOVERNANCE_AUTHORITY,
            "recommended_next_step": NEXT_STEP,
        }

    lead = _leading_verb(query)

    def _is_request(spec) -> bool:
        if lead in spec["verbs"]:
            return True
        if "phrase" in spec and spec["phrase"].search(lowered) and lead in {
            "", "please", "do", "execute", "perform", "initiate",
        }:
            return True
        # "... and then promote it" style chained requests
        chained = re.search(
            r"\b(?:then|and)\s+(?:to\s+)?(\w+)", lowered
        )
        return bool(chained and chained.group(1) in spec["verbs"])

    for spec in _PROTECTED_ACTIONS:
        if spec["topic"].search(lowered) and _is_request(spec):
            return {
                "kind": "blocked_action",
                "action": spec["action"],
                "reason": spec["reason"],
                "authority": GOVERNANCE_AUTHORITY,
                "recommended_next_step": NEXT_STEP,
            }
    return None


# ---------------------------------------------------------------------------
# Evidence helpers (real ledger records only)
# ---------------------------------------------------------------------------


def _short(ref: str | None) -> str:
    return f"{str(ref)[:12]}…" if ref else "unknown"


def _collect_entries():
    entries = []
    for entry in _ledger.iter_entries():
        entries.append(
            {
                "seq": entry.get("seq"),
                "timestamp": entry.get("timestamp"),
                "entry_hash": entry.get("entry_hash"),
                "record": entry["record"],
            }
        )
    return entries


def _evidence_item(seq, entry_hash, label, detail) -> dict:
    return {
        "ref": _short(entry_hash) if entry_hash else f"ledger#{seq}",
        "label": label,
        "detail": detail,
        "seq": seq,
    }


def _packet_evidence(entries, decision=None, objective_contains=None, limit=3):
    items = []
    for e in entries:
        r = e["record"]
        if r.get("type") != "verification_packet":
            continue
        if decision and r.get("decision") != decision:
            continue
        if objective_contains and objective_contains.lower() not in str(
            r.get("objective", "")
        ).lower():
            continue
        items.append(
            _evidence_item(
                e["seq"],
                e["entry_hash"],
                f"{r.get('decision')} — {r.get('objective')}",
                {
                    "actor": r.get("actor"),
                    "packet_id": r.get("packet_id"),
                    "digest": _short(r.get("digest")),
                    "ledger_seq": e["seq"],
                },
            )
        )
        if len(items) >= limit:
            break
    return items


def _transition_evidence(entries, version_id=None, to_state=None, limit=3):
    items = []
    for e in entries:
        r = e["record"]
        if r.get("type") != "state_transition":
            continue
        if version_id and r.get("version_id") != version_id:
            continue
        if to_state and r.get("to") != to_state:
            continue
        items.append(
            _evidence_item(
                e["seq"],
                e["entry_hash"],
                f"{r.get('from')} → {r.get('to')} ({r.get('reason')})",
                {
                    "version_id": r.get("version_id"),
                    "packet_id": r.get("packet_id"),
                    "ledger_seq": e["seq"],
                },
            )
        )
        if len(items) >= limit:
            break
    return items


def _registration_evidence(entries, limit=3):
    items = []
    for e in entries:
        r = e["record"]
        if r.get("type") != "registration":
            continue
        items.append(
            _evidence_item(
                e["seq"],
                e["entry_hash"],
                f"Registered {r.get('model')} v{r.get('version')}",
                {"version_id": r.get("version_id"), "ledger_seq": e["seq"]},
            )
        )
    return items[:limit]


def _respond(kind, query, explanation, rule, source, evidence, review=False):
    return {
        "kind": kind,
        "query": query,
        "explanation": explanation,
        "rule": rule,
        "source": source,
        "evidence": evidence,
        "requires_human_review": review,
    }


# ---------------------------------------------------------------------------
# Intent handlers
# ---------------------------------------------------------------------------


def explain_rejection(query: str, entries) -> dict:
    quarantines = _packet_evidence(entries, decision="QUARANTINE", limit=2)
    if not quarantines:
        return explain_no_evidence(
            query, "No rejected or quarantined models are recorded in the evidence ledger."
        )
    first = quarantines[0]
    version = None
    for e in entries:
        r = e["record"]
        if r.get("type") == "verification_packet" and r.get("decision") == "QUARANTINE":
            m = re.search(r"v(\d+)", str(r.get("objective", "")))
            version = m.group(0) if m else None
            break
    transitions = _transition_evidence(entries, to_state="QUARANTINED", limit=2)
    explanation = (
        f"The challenger was not promoted because the deterministic verification gate "
        f"quarantined it during verification. Decision recorded by actor "
        f"'{first['detail']['actor']}' in ledger sequence {first['detail']['ledger_seq']}. "
        f"Promotion authority remains exclusively with the governance engine."
    )
    all_ev = quarantines + transitions
    return _respond(
        "explanation",
        query,
        explanation,
        rule="VERIFICATION_QUARANTINE",
        source="REGISTERED_REFERENCE",
        evidence=all_ev,
    )


def explain_drift_investigation(query: str, entries) -> dict:
    drift_packets = [
        e["record"]
        for e in entries
        if e["record"].get("type") == "verification_packet"
        and "drift" in str(e["record"].get("objective", "")).lower()
    ]
    if not drift_packets:
        return _respond(
            "explanation",
            query,
            "No drift-triggered investigations are present in the current evidence "
            "ledger. Drift monitoring runs against live forecasts; when drift "
            "exceeds policy thresholds it files a supervision packet that appears "
            "here. The ledger currently contains registration, verification, "
            "state-transition and adaptation records only.",
            rule="NO_DRIFT_EVIDENCE_RECORDED",
            source="REGISTERED_REFERENCE",
            evidence=[],
        )
    return _respond(
        "explanation",
        query,
        "Drift investigation was triggered because monitored forecast error "
        "crossed the deterministic drift threshold defined in the frozen policy. "
        "Evidence below references the corresponding ledger packets.",
        rule="DRIFT_THRESHOLD_EXCEEDED",
        source="REGISTERED_REFERENCE",
        evidence=_packet_evidence(entries, limit=3),
    )


def explain_adaptation_experiment(query: str, entries) -> dict:
    retrains = []
    for e in entries:
        r = e["record"]
        if r.get("type") == "verification_packet" and r.get("decision") == "RETRAIN":
            retrains.append(
                _evidence_item(
                    e["seq"],
                    e["entry_hash"],
                    f"Adaptation packet — {r.get('objective')}",
                    {
                        "actor": r.get("actor"),
                        "decision": r.get("decision"),
                        "packet_id": r.get("packet_id"),
                        "ledger_seq": e["seq"],
                    },
                )
            )
    registrations = _registration_evidence(entries, limit=2)
    if not retrains:
        return explain_no_evidence(
            query, "No adaptation experiments are recorded in the evidence ledger."
        )
    actors = sorted({item["detail"]["actor"] for item in retrains})
    explanation = (
        f"Adaptation experiments are initiated by '{', '.join(actors)}' after "
        f"governance approval. Each approved experiment produces a new "
        f"challenger that must pass the same verification gate before any "
        f"lifecycle transition. {len(retrains)} adaptation packet(s) are "
        f"recorded in the ledger."
    )
    return _respond(
        "explanation",
        query,
        explanation,
        rule="SUPERVISED_ADAPTATION",
        source="REGISTERED_REFERENCE",
        evidence=(retrains + registrations)[:4],
    )


def explain_governance_decision(query: str, entries) -> dict:
    packets = _packet_evidence(entries, limit=4)
    if not packets:
        return explain_no_evidence(query, "No governance packets are recorded.")
    explanation = (
        f"The referenced governance decisions were produced by the deterministic "
        f"policy engine. Each packet below carries its actor, packet id and "
        f"tamper-evident ledger reference. The agentic layer can retrieve these "
        f"records but cannot alter them."
    )
    return _respond(
        "explanation",
        query,
        explanation,
        rule="EVIDENCE_LEDGER_VERIFIED",
        source="REGISTERED_REFERENCE",
        evidence=packets,
    )


def explain_rollback(query: str, entries) -> dict:
    rollbacks = _packet_evidence(entries, decision="ROLLBACK", limit=2)
    transitions = _transition_evidence(entries, to_state="ROLLED_BACK", limit=2)
    if not rollbacks and not transitions:
        return explain_no_evidence(query, "No rollback actions are recorded.")
    explanation = (
        "A rollback was executed through the deterministic lifecycle engine: the "
        "previously deployed champion was restored and the affected version was "
        "moved to ROLLED_BACK. The decision chain (packet + state transition) is "
        "referenced below."
    )
    return _respond(
        "explanation",
        query,
        explanation,
        rule="ROLLBACK_COMPLETED",
        source="REGISTERED_REFERENCE",
        evidence=(rollbacks + transitions)[:4],
    )


def explain_promotion(query_about_challenger: bool, query: str, entries) -> dict:
    deployments = _packet_evidence(entries, decision="DEPLOYED", limit=3)
    verifications = _packet_evidence(entries, decision="VERIFIED", limit=3)
    if not deployments:
        return explain_no_evidence(query, "No promotions are recorded.")
    explanation = (
        "Champion-challenger promotion follows a fixed sequence: challenger "
        "registers → verification gate evaluates it → only an APPROVED verdict "
        "allows deployment. Packets below show the recorded verification and "
        "deployment decisions."
    )
    return _respond(
        "explanation",
        query,
        explanation,
        rule="CHAMPION_CHALLENGER_GATE",
        source="REGISTERED_REFERENCE",
        evidence=(verifications + deployments)[:4],
    )


def explain_lifecycle_overview(query: str, entries) -> dict:
    registrations = _registration_evidence(entries, limit=2)
    deployments = _packet_evidence(entries, decision="DEPLOYED", limit=2)
    rollbacks = _transition_evidence(entries, to_state="ROLLED_BACK", limit=1)
    n = len(entries)
    explanation = (
        f"The evidence ledger currently holds {n} tamper-evident records covering "
        f"dataset provisioning, model registration, verification-gate decisions, "
        f"governed lifecycle transitions and supervised adaptation. The platform "
        f"forecasts Load, Wind and PV; deterministic policies decide whether "
        f"adaptation is permitted, and the agent layer explains — but never "
        f"executes — those decisions."
    )
    return _respond(
        "explanation",
        query,
        explanation,
        rule="SYSTEM_SUMMARY",
        source="REGISTERED_REFERENCE",
        evidence=(registrations + deployments + rollbacks)[:4],
    )


def explain_no_evidence(query: str, message: str) -> dict:
    return _respond(
        "explanation",
        query,
        message,
        rule="NO_MATCHING_EVIDENCE",
        source="REGISTERED_REFERENCE",
        evidence=[],
    )


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

_INTENTS = [
    (re.compile(r"\b(reject\w*|quarantin\w*|not promoted|not approved|failed)\b", re.I), "rejection"),
    (re.compile(r"\b(drift)\b", re.I), "drift"),
    (re.compile(r"\b(adaptation|adapt|experiment|retraining|retrain(ed|ing)?)\b", re.I), "adaptation"),
    (re.compile(r"\b(rollback|rolled back|roll back)\b", re.I), "rollback"),
    (re.compile(r"\b(promot|challenger|champion|deploy)\w*\b", re.I), "promotion"),
    (re.compile(r"\b(evidence|decision|audit|governance|policy)\b", re.I), "governance"),
]


def route_query(query: str, entries) -> dict:
    for pattern, intent in _INTENTS:
        if pattern.search(query):
            if intent == "rejection":
                return explain_rejection(query, entries)
            if intent == "drift":
                return explain_drift_investigation(query, entries)
            if intent == "adaptation":
                return explain_adaptation_experiment(query, entries)
            if intent == "rollback":
                return explain_rollback(query, entries)
            if intent == "promotion":
                return explain_promotion(True, query, entries)
            if intent == "governance":
                return explain_governance_decision(query, entries)
    return explain_lifecycle_overview(query, entries)


def get_agent_explanation(query: str) -> dict:
    _init_singletons()
    query = (query or "").strip()

    blocked = classify_protected_action(query)
    if blocked:
        response = _respond(
            "blocked_action",
            query,
            (
                f"Requested action '{blocked['action']}' is outside the agent's "
                f"authority. {blocked['reason']} Authority rests with the "
                f"{blocked['authority']}."
            ),
            rule="AGENT_ACTION_BLOCKED",
            source="POLICY_BOUNDARY",
            evidence=[],
            review=True,
        )
        response.update(
            {
                "action": blocked["action"],
                "reason": blocked["reason"],
                "authority": blocked["authority"],
                "recommended_next_step": blocked["recommended_next_step"],
            }
        )
        return response

    if not query:
        return explain_no_evidence("", "Empty query — nothing to explain.")

    try:
        entries = _collect_entries()
    except Exception as exc:  # pragma: no cover - defensive
        return _respond(
            "explanation",
            query,
            "The evidence ledger could not be read; refusing to speculate.",
            rule="LEDGER_UNAVAILABLE",
            source="SYSTEM",
            evidence=[{"ref": "error", "label": str(exc), "detail": {}, "seq": None}],
            review=True,
        )

    return route_query(query, entries)
