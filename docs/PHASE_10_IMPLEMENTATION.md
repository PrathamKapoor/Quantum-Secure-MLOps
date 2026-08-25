# Phase 10 — Adaptive Supervisor (Implementation)

Status: COMPLETE within scope · Entry 254 passed → Exit **271 passed** ·
compileall clean · demo SUCCESS · REPO-B (guardrailed-product) untouched
(git `bc835e3`, working tree clean).

This phase **evolves** the existing supervisor (`qsmlops/supervisor/*`) per the
roadmap PART 14 §7.7 — it is not a rewrite. Phase 1–9 governance, security,
crypto, and trust invariants are preserved.

---

## 1. Scope (per spec)

- Evidence-validation engine hardening
- Risk-engine refinement (confidence-aware / adaptive)
- Decision-engine expansion + explainability

Out of scope: Phase 11. No product/backend_api/frontend artifacts, no Guardrailed
(REPO-B) linkage.

---

## 2. Evidence-validation engine — `qsmlops/supervisor/validation.py` (NEW)

Fail-safe contract: **never raises**; returns `(clean_observation, ValidationReport)`.

`validate_observation(obs) -> (Observation, ValidationReport)`:

| Condition | Action |
|-----------|--------|
| input not an `Observation` | replace with `malformed_finding` (HIGH, recommendation `ESCALATE`) |
| finding severity not in `{CRITICAL,HIGH,MEDIUM,LOW,INFO}` | dropped; problem recorded |
| `confidence` outside `[0,1]` | clamped; `confidences_clamped += 1` |
| duplicate finding (same `name`, passed, severity) | collapsed; `duplicates_collapsed += 1` |
| evidence entry without a `source` | problem recorded; **finding retained** (not silently trusted) |

`ValidationReport` exposes `ok`, `problems`, `duplicates_collapsed`,
`confidences_clamped`, and `to_dict()`. The supervisor appends a HIGH
`evidence_validation` finding (recommendation `ESCALATE`) when `problems` exist.

Constants: `VALID_SEVERITIES`, `ADAPTIVE_CONFIDENCE_FLOOR = 0.6`,
`CRITICAL_RISK_FLOOR = 20.0`.

---

## 3. Confidence-aware adaptive risk — `qsmlops/supervisor/decisions.py`

Legacy (preserved, severity-only): `observation_risk(obs)` and
`aggregate_risk(obs_list, adaptive=False)`.

Adaptive (Phase 10 default): `observation_risk_adaptive(obs)`:

```
probability = 0.6 + 0.4 * confidence        # ADAPTIVE_CONFIDENCE_FLOOR
raw        = severity_weight * probability
score      = max(raw, CRITICAL_RISK_FLOOR) if severity == CRITICAL else raw
return round(score, 4)
```

Properties:
- **Bounded** to `[0, 100]` via aggregate `min(100, 0.6·worst + 0.4·mean)`.
- **Deterministic**, no randomness, no external trust, no LLM/RL —
  satisfies "no circular trust".
- **Anti-evasion**: a CRITICAL finding can never be diluted below 20 by low
  confidence (clone/forged-artifact attacks lose the "report low confidence"
  evasion path).
- Blend shape unchanged: a single catastrophic signal still dominates
  (`0.6·worst`), while many moderate signals accumulate (`0.4·mean`).

`DecisionReport.validation: list[dict]` added; `to_dict()` includes it.

### Test-assertion note
`tests/test_supervisor.py::test_aggregate_risk_one_critical` was updated to
assert **both** semantics explicitly (adaptive `18.4`, legacy `20.0`). This is a
documented, spec-driven change in the risk model — not a regression mask.

---

## 4. Decision-engine wiring — `qsmlops/supervisor/supervisor.py`

- `collect_observations(context)` now validates each agent's output via
  `validate_observation`, stores `_last_validation`, and appends the
  `evidence_validation` finding when problems exist. Agent crashes are still
  caught and wrapped (`agent_executed` HIGH + `ESCALATE`).
- `reason()` uses the **adaptive** `aggregate_risk` and passes `validation`
  into `DecisionReport`, so every decision carries its evidence trail.

`SelfHealingMLOps.evaluate_version` now routes through
`supervisor.collect_observations(context)` (single crash-safe, validated
source of truth) instead of an inline loop.

---

## 5. Governance agent change

`governance-agent` trust-presence rule is now lifecycle-aware: a `REGISTERED`
version that has not reached verification reports the trust evaluation as
`LOW`/`pending` (not a spurious `MEDIUM` failure), while `APPROVED`/`DEPLOYED`
versions without a persisted trust decision still fail `MEDIUM` as a real gap.

---

## 6. Hard security overrides preserved (verified)

These still hard-fail to `QUARANTINE` regardless of adaptive confidence
(covered by `tests/test_phase10_adaptive_supervisor.py`):

- invalid / forged signature
- revoked signer
- artifact corruption / digest mismatch
- trust state `BLOCKED` / `QUARANTINED`
- separation-of-duties violation
- `drift_*` QUARANTINE-exemption regression

---

## 7. Explainability surface (`DecisionReport.to_dict()`)

`decision, risk_score, category_scores, scores, observations, rationale, facts,
policy_decisions, validation` — every field present and inspectable. The
`validation` list gives per-agent evidence-problem traces for audit.

---

## 8. Tests added

`tests/test_phase10_adaptive_supervisor.py` (17 tests):

- A–E validator units (bad severity, confidence clamp, duplicate collapse,
  evidence-without-source, non-Observation input)
- F–H adaptive vs legacy weighting, CRITICAL floor, aggregate blend
- I–L multi-agent determinism, forced crash → ESCALATE, hard-override matrix
- feedback-loop consecutive failures → ESCALATE (LearningStore)
- M–O full decision trace, validation-failure → policy-consumable fact
- R/W/X determinism, healthy-quiet residual-risk bound, repo-boundary grep

Full suite: **271 passed**.

---

## 9. Phase 11

Not started. Per directive: STOP after Phase 10.
