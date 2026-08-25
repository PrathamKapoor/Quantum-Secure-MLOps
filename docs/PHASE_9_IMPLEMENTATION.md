# Phase 9 Implementation: Agentic Intelligence Layer

> Specification: architecture document PART 14 §14.3 (PHASE 9), §6.15/6.20/
> 6.21/6.22 (archetypes), §23.18 (restrictions); PART 21 STAGE 8 list.

## Requirement reconstruction (from spec)

Phase 9 completes the agent roster with four missing archetypes alongside the
five existing ones: **Training Optimization, Incident Response, Governance,
Optimization**. Every agent: consumes existing platform evidence, emits
Observation + Findings + Evidence + Confidence + Risk + Recommendation, is
deterministic (rule-based; no LLM), never mutates state, and cannot deploy /
modify security / change policy / delete evidence. Supervisor facts and the
existing PolicyEngine remain the only decision surface.

## Existing architecture used (no duplication)

BaseAgent / Observation / Finding / Evidence (`agents/base.py`) · supervisor
`collect_observations` + `aggregate_risk` (per-agent risk keys become
`<agent>_risk` policy facts automatically via `build_facts`) · ledger /
registry / telemetry as read-only evidence sources · existing registration
list `SelfHealingMLOps.agents`.

## Agents implemented (all observational)

| Agent | Name | Evidence consumed | Findings emitted |
|---|---|---|---|
| Training Optimization | `training-optimization-agent` | passport.training_info/metrics (+resolvable dataset) | metadata completeness, reproducible-seed presence, sample adequacy (≥2×features), drift-informed retrain hint |
| Incident Response | `incident-response-agent` | ledger tail (denials/approval-denials/escalations/post-verify failures/quarantine+rollback transitions), version state, CRITICAL drift | recent-signal count, subject-state clearance, ongoing critical drift (`drift_critical_ongoing` — participates in the established drift_* quarantine exemption) |
| Governance | `governance-agent` | signature vs trust anchors, BOM entries vs artifact store, passport.security_status, registry state legality, persisted trust evaluation | 5 compliance findings incl. CRITICAL signature/BOM breaches |
| Optimization | `optimization-agent` | registry versions (artifact digests, registered_at, states) | duplicate-artifact reuse, stale REGISTERED housekeeping, subject-artifact uniqueness |

Recommendations map to existing vocabulary (ACCEPT/MONITOR/RETRAIN/
ESCALATE/INVESTIGATE/REVIEW/BLOCK/OPTIMIZE/COLLECT_MORE_DATA/
RETRAIN_WITH_SEED/EVALUATE_TRUST/REVIEW_PIPELINE). Healthy platforms produce
zero failed findings from all four agents.

## Supervisor / policy integration

No supervisor or build_facts changes were required: per-agent risk keys
(`training-optimization-agent_risk`, …) flow into facts automatically and are
policy-consumable (proven by a gate-rule test). One wiring gap fixed:
`evaluate_version`/`health_check` contexts now carry `version_record` and
resolvable `datasets` so agents read real state instead of guessing.

## Security verification (STEP 7)

Static test asserts no `*_agent.py` contains `.deploy(`, `.approve_deployment(`,
`.transition(`, `.request_approval(`, `.quarantine(`, `.revoke(`. Full Phase-5
approval/SoD suite, keystore remediation suite, and deployment-gate suite
re-run green after registration.

## Regression note (one failure during development, root-caused & fixed)

The incident agent initially named its critical-drift finding
`critical_drift_ongoing`, which tripped the supervisor's hard-quarantine rule
(that rule exempts only `drift_*`-prefixed findings) and flipped an established
Phase-2 semantic (critical drift → ROLLBACK/RETRAIN, not QUARANTINE). Renamed
to `drift_critical_ongoing`; exemption applies; original decision restored.

## Files created

qsmlops/agents/{training_optimization_agent, incident_response_agent,
governance_agent, optimization_agent}.py · tests/test_phase9_agentic_layer.py
· docs/PHASE_9_IMPLEMENTATION.md

## Files modified

qsmlops/pipeline/selfheal.py (imports, registration, context carries
version_record + datasets) · HANDOFF-A.md (addendum)

## Verification

| Suite | Result |
|---|---|
| New phase-9 suite | 15/15 |
| Full core suite | **254 passed** (239 + 15) |
| compileall | clean |
| demo.py | SUCCESS (chain OK, RETRAIN recovery) |

## Limitations

Training agent's sample-adequacy needs a resolvable dataset (else honest
UNAVAILABLE); incident lookback is a fixed ledger tail (25 entries); governance
trust-presence check legitimately transitions False→True after the first sweep;
optimization scope limited to registry housekeeping evidence that exists today.
