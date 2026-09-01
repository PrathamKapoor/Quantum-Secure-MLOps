# Handoff – Quantum-Secure Agentic MLOps Pipeline Management System

> Updated: Phase 5 (Secure Model Registry — trust-scored approval & governed
> promotion) implementation session.
> Baseline on entry: 154 core + 14 product tests passing. Current: **188 core
> tests passing (154 + 34 new Phase 5); compileall clean; demo green.**
> ⚠️ A separate workstream concurrently restructured `product/` during this
> session — see "External interference" below.

## 1. Original Phase 5 objective (architecture document)

PART 14 §14.3 / PART 21 STAGE 5 / §23.15: Secure Model Registry — versioning,
approval workflow, **trust scoring**, pre-approval checks (Passport ∧ QML-BOM ∧
Signature ∧ Evaluation), `/registry/*` APIs, rollback. Detail: PART 9 §9.9–9.10.

## 2. What the repository already had

Full registry state machine (REGISTERED→VERIFIED→APPROVED→DEPLOYED +
QUARANTINED/REVOKED/ROLLED_BACK), versioning, rollback, revocation,
separation of duties (verifier≠signer), VerificationPackets with crypto
proofs (Phase 4), evidence ledger, PolicyEngine with scores in facts,
CLI + dashboard API.

## 3–4. Gap analysis → what was implemented

Gaps: no trust decision layer, no explainable scoring, approval not gated on
trust, denials unaudited, no trust persistence, no /registry/approve|revoke
API, no CLI trust commands.

Implemented (extend-only; no second anything):
- `qsmlops/scores.py`: `TrustResult` + `evaluate_trust` — five weighted
  components (security/integrity/lineage/performance/operational) from real
  evidence; hard crypto blockers dominate as BLOCKED; decisions TRUSTED /
  CONDITIONALLY_TRUSTED / REVIEW_REQUIRED / BLOCKED / QUARANTINED;
  deterministic and fully explainable. Existing score functions unchanged.
- `qsmlops/config.py`: `DEFAULT_TRUST_THRESHOLDS` {trusted:90, conditional:70}.
- `qsmlops/registry/registry.py`: idempotent trust-column migration;
  `trust_evaluation()` (persist latest + ledger event) & `latest_trust()`;
  `approve_deployment` now a governed gate (packet ∧ approver≠signer ∧
  passing trust), returns structured result, audits `approval_denied`,
  appends gate packets.
- `qsmlops/supervisor/policy.py`: `build_facts(..., trust=…)` exposes
  trust_score/decision/eligibility/blockers to policies (defaults unchanged).
- `qsmlops/pipeline/selfheal.py`: evaluate_version returns trust report; new
  `request_approval()` (approve-without-deploy); approve_and_deploy gated.
- `qsmlops/api/app.py`: GET /registry/models, GET /registry/versions/{vid},
  GET+POST /registry/trust/{vid}, POST /registry/approve/{vid} (409+explanation),
  POST /registry/revoke/{vid}; /incidents includes trust events & denials.
- `qsmlops/cli.py`: `trust [--refresh]`, `request-approval`, `registry`,
  `revoke`; `approve` emits structured denial JSON on refusal.

## 5. Intentionally NOT implemented

No default policy rule firing on low trust (available via policy documents;
avoids behavioural regression). No second registry/engine/ledger/policy/
crypto/deployment/CLI/API. Supervisor untouched beyond fact exposure.
Deployment mechanics unchanged (APPROVED-only gate inherits trust).

## 6–7. Files created / modified

Created: `tests/test_phase5_trust.py`, `tests/test_phase5_approval.py`,
`tests/test_phase5_registry_api.py`, `tests/test_phase5_cli.py`,
`docs/PHASE_5_IMPLEMENTATION.md`.
Modified: `qsmlops/scores.py`, `qsmlops/config.py`, `qsmlops/registry/registry.py`,
`qsmlops/supervisor/policy.py`, `qsmlops/pipeline/selfheal.py`,
`qsmlops/api/app.py`, `qsmlops/cli.py`, `tests/conftest.py` (see §10),
`HANDOFF.md`.

## 8–11. Tests (exact)

| Suite | Before session | After Phase 5 |
|---|---|---|
| Core `pytest tests/` | 154 | **188 passed** (154 + 34) |
| Phase 5 suites alone | — | 34/34 |
| `compileall qsmlops` | clean | clean |
| `demo.py` | success | success (RETRAIN recovery; chain OK) |
| CLI smoke (trust --refresh) | — | TRUSTED, 100.0 |

Remaining failures in MY scope: none.

## External interference (important)

Mid-session, another process/session modified `product/backend_api` (new
routers/schemas/services, `.integrity/post_stage1_reissue.json`) and added
`tests/product/` (11 files) whose basenames collided with core test modules,
breaking core collection. Resolution without touching their files:
`tests/conftest.py` excludes `product/*` from the CORE suite via
`collect_ignore_glob` (commented). The product tree was being restructured
while commands ran (`product/backend_api/tests` disappeared between two
invocations); its state is the other workstream's responsibility and is NOT
verified here. The last stable product measurement this session was 14 passed
before their changes landed.

## 12. Known limitations

Phase 5: synchronous in-process evaluation; performance component uses
passport-recorded metrics only; default policy rules deliberately unchanged.
Pre-existing: corrupted legacy top-level dirs; stubbed `mlops/`;
`run_phase19_evaluation.py` broken (pandas/mlflow missing; committed CSVs are
DummyModel zeros); `qsmlops/serving/service.py.bak` debris.

## 13. Recommended starting point for Phase 6 (Secure Deployment)

Document PART 14 §14.3 PHASE 6 / STAGE 6: deployment service, inference
serving with pre-load passport/signature/integrity checks, rollback system.
Entry point: `qsmlops/serving/service.py` already enforces DEPLOYED-state +
signature/key checks behind gates; extend it with environment validation and
the document's deployment-request flow, wiring promotion eligibility from
`TrustResult.promotion_eligible`. Reuse `registry.deploy` as the only
promotion mechanism. Do NOT create a second serving path.


---

# SESSION ADDENDUM — Post-separation autonomous session (Phase 6 + Gate-D)

Baseline on entry: 188 passed / compile clean / demo OK (post-separation).
State at exit: **208 passed** (188 prior + 4 keystore-remediation + 16 Phase-6),
compileall clean, demo SUCCESS, CLI smokes green.

## Security remediation (authorized prerequisite)
`QSMLOPS_KEYSTORE_PASSPHRASE` now routes the platform through
EncryptedKeyStore (vault; legacy plaintext auto-migrated then deleted).
Unset ⇒ legacy dev behavior unchanged. Tests:
tests/test_keystore_remediation.py. NOTE: existing `~/.qsmlops/keys/secret_keys.json`
migrates automatically the first time an operator sets the variable.

## Phase 6 (COMPLETE within scope)
Governed deployment-request flow wired end-to-end: pipeline delegates →
DeploymentService validates identity/state/crypto/trust(promotion_eligible)/
environment/policy → registry.deploy() promotes (sole mechanism) → serving-gate
post-verification → ledger evidence. API: POST /deployment/request,
GET /deployment/status/{model}, GET /deployment/validation/{vid},
POST /deployment/rollback/{model}. CLI: request-deployment /
validate-deployment / deployment-status. Repairs to interrupted-session code:
_resolve_version restored, dead code removed, unknown-version denial audited.

## Files created
docs/PHASE_6_IMPLEMENTATION.md · tests/test_keystore_remediation.py ·
tests/test_phase6_deployment_flow.py

## Files modified
qsmlops/config.py (keystore_passphrase) · qsmlops/crypto n/a (mechanism existed) ·
qsmlops/serving/deployment.py (repairs) · qsmlops/pipeline/selfheal.py (keystore
selection + deployments service + delegates) · qsmlops/api/app.py (4 routes) ·
qsmlops/cli.py (3 commands) · HANDOFF-A.md (this addendum)

## Known limitations / residue
- Smoke-test residue in default runtime home `~/.smlops`: one REGISTERED model
  ("sm"/"x" from a mis-env'd smoke run). Harmless, ledger-consistent; remove via
  registry revoke if undesired.
- Frontend build failure in Guardrailed repo is pre-existing and out of scope.
- KEM/hybrid encryption still implemented-but-disconnected (pre-existing).

## Phase 7 readiness — exact entry point
Per document PART 14 §14.3 PHASE 7 / STAGE 7 (Monitoring & Observability):
telemetry collector + metrics store + alerting on top of existing drift engine
(`ml/drift.py`) and ledger telemetry (`serving` inference records). Entry files:
`qsmlops/ml/drift.py`, `qsmlops/api/app.py` (metrics surface), new
`qsmlops/monitoring/` module inside qsmlops (name free — root corpse dir is
archived under _archive/). Do NOT resurrect archived modules.


---

# SESSION ADDENDUM 2 — Phase 7 (Monitoring & Observability Foundation)

Entry baseline: 208 passed / compile clean / demo OK.
Exit state: **221 passed** (208 + 13 monitoring), compileall clean, demo SUCCESS.

## Implemented
qsmlops/monitoring/{collector,alerts}.py — TelemetryCollector (JSONL at
<home>/monitoring/telemetry.jsonl; record/series/latest/summary/drift_history)
+ deterministic alert rules (performance thresholds, drift severity mapping,
trust-decision alerts) with worst_level. health_check() now persists telemetry
and returns outcome["alerts"]/["alert_level"]. API: GET /metrics/{model},
GET /alerts/{model}. PlatformConfig.telemetry_path added.

## Files created
qsmlops/monitoring/{__init__,collector,alerts}.py ·
tests/test_phase7_monitoring.py · docs/PHASE_7_IMPLEMENTATION.md

## Files modified
qsmlops/config.py · qsmlops/pipeline/selfheal.py · qsmlops/api/app.py ·
HANDOFF-A.md

## Known limitations
Tier-3 JSONL store (single host); no retention policy; stateless alerts (no
ack/suppression); inference latency not instrumented yet.

## Phase 8 readiness — exact entry point
Document PART 14 §14.3 PHASE 8 (Advanced Drift Intelligence): deepen
ml/drift.py consumers — per-feature drift attribution surfaced through the
new telemetry/alerts stack, rolling-window performance drift baselines fed
from TelemetryCollector.summary(), and DriftReports persisted via
telemetry.record_drift (already wired). Do NOT start without owner signal.


---

# SESSION ADDENDUM 3 — Phase 8 (Advanced Drift Intelligence)

Entry baseline: 221 passed / compile clean / demo OK.
Exit state: **239 passed** (221 + 18), compileall clean, demo SUCCESS.

## Implemented
ml/drift.py: build_feature_attribution() (merges existing per-feature PSI/KS/
prediction reports; real baseline/current means from arrays or UNAVAILABLE;
ranked) + classify_drift() (six deterministic interpretations incl. broad vs
isolated vs drift+performance combos). monitoring/collector.py:
record_feature_attribution (kind=feature_drift, shared check_ts),
feature_history/latest_feature_attribution, rolling_baseline(metric,window,
min_history). alerts.evaluate extended (backward-compatible kwargs):
FEATURE_DRIFT_CRITICAL / FEATURE_DRIFT_BROAD /
SUSTAINED_PERFORMANCE_DEGRADATION. run_drift_check embeds attribution +
intelligence into summary; health_check persists per-feature rows, computes
mse/r2 rolling baselines from telemetry, returns feature_attribution /
rolling_baseline / drift_intelligence. API: GET /drift/{model}/attribution,
GET /performance/{model}/rolling. Config knobs: MONITORING_ROLLING_WINDOW,
MONITORING_MIN_HISTORY, DRIFT_BROAD_FEATURE_FRACTION.

## Files created
tests/test_phase8_drift_intelligence.py · docs/PHASE_8_IMPLEMENTATION.md

## Files modified
qsmlops/ml/drift.py · qsmlops/monitoring/collector.py ·
qsmlops/monitoring/alerts.py · qsmlops/pipeline/selfheal.py ·
qsmlops/api/app.py · qsmlops/config.py · HANDOFF-A.md

## Known limitations
Attribution covers features present in detector reports (PSI/KS thresholds
gate emission); prediction-drift pseudo-feature "predictions" included;
rolling baselines require >= min_history observations per metric; no
retention policy on telemetry.jsonl.

## Phase 9 readiness — exact entry point
Document PART 14 §14.3 PHASE 9 (Agentic Intelligence Layer): add the missing
agent archetypes (Training Optimization, Incident Response, Governance,
Optimization) onto BaseAgent with evidence-bearing Observations, register in
SelfHealingMLOps.agents, extend supervisor facts — no new decision path.
Do NOT start without owner signal.


---

# SESSION ADDENDUM 4 — Phase 9 (Agentic Intelligence Layer)

Entry baseline: 239 passed. Exit: **254 passed** (239 + 15), compileall clean,
demo SUCCESS.

## Implemented
Four roadmap archetypes on BaseAgent, observational-only, deterministic:
training-optimization-agent (metadata completeness / reproducible seed /
sample adequacy vs features / drift-informed retrain hint),
incident-response-agent (ledger-tail incident signals incl.
deployment_denied/approval_denied/escalation/post-verification-failure +
adverse states + critical drift via drift_-prefixed finding that respects the
supervisor quarantine exemption), governance-agent (signature vs anchors,
BOM verified-ratio, security_status completeness, state legality, trust
evaluation presence), optimization-agent (duplicate artifact reuse, stale
REGISTERED housekeeping, subject-artifact uniqueness). Registered in
SelfHealingMLOps.agents → 9 agents total. Supervisor facts auto-extend via
aggregate_risk per-agent keys (<agent>_risk) — policy-consumable (gate-rule
test). evaluate_version/health_check contexts now carry version_record and
resolvable datasets. Static safety test proves agents contain no promotion/
mutation calls.

## Regression root-caused during development
Incident agent's critical-drift finding initially bypassed the supervisor's
drift_* quarantine exemption and flipped a Phase-2 semantic to QUARANTINE;
renamed drift_critical_ongoing; original decisions restored.

## Files created / modified
Created: agents ×4 files, tests/test_phase9_agentic_layer.py,
docs/PHASE_9_IMPLEMENTATION.md. Modified: pipeline/selfheal.py,
HANDOFF-A.md.

## Phase 10 readiness — exact entry point
Document PART 14 §14.3 PHASE 10 (Adaptive Supervisor): evidence-validation
engine hardening, risk-engine refinement, decision-engine expansion on the
EXISTING supervisor/policy modules. Entry files: qsmlops/supervisor/*. Do NOT
start without owner signal.

# SESSION ADDENDUM 5 — Phase 10 (Adaptive Supervisor)

Entry baseline: 254 passed. Exit: **271 passed** (254 + 17), compileall clean,
demo SUCCESS, REPO-B (guardrailed-product) untouched (git bc835e3, clean).

## Implemented
Evolution of the EXISTING supervisor — not a rewrite. Three pillars from
PART 14 §7.7:

1. **Evidence-validation engine** (`supervisor/validation.py`, NEW): fail-safe
   `validate_observation(obs) -> (clean_obs, ValidationReport)`. Drops findings
   with invalid severity, clamps confidence to [0,1], collapses duplicate
   findings, flags evidence lacking a source (finding retained, not trusted),
   replaces malformed/non-Observation input with a HIGH `malformed_finding`
   marker. Never raises; always returns (clean, report).
2. **Confidence-aware adaptive risk** (`supervisor/decisions.py`): legacy
   `observation_risk` (severity-only, used by `aggregate_risk(adaptive=False)`)
   preserved verbatim. New `observation_risk_adaptive` = severity_weight ×
   [0.6 + 0.4·confidence], with `CRITICAL_RISK_FLOOR=20.0` anti-evasion;
   `aggregate_risk` default is adaptive. Bounded, deterministic, no circular
   trust, no LLM/RL.
3. **Explainability**: `DecisionReport.validation` carries per-agent
   ValidationReport dicts; `to_dict()` exposes full trace (validation list,
   facts, policy_decisions, scores, rationale). `supervisor.collect_observations`
   now validates every agent sweep, appends a HIGH `evidence_validation`
   finding when problems exist, and feeds `reason()` the adaptive aggregate.
   `SelfHealingMLOps.evaluate_version` routes through the same crash-safe,
   validated collector (single source of truth).

## Governance hard overrides preserved
Forged/invalid signature, revoked signer, artifact corruption/mismatch, trust
BLOCKED/QUARANTINED, SoD violation still hard-fail to QUARANTINE regardless of
adaptive confidence. drift_* quarantine exemption retained. See
tests/test_phase10_adaptive_supervisor.py (hard-override matrix + drift
regression) and docs/PHASE_10_IMPLEMENTATION.md.

## Files created / modified
Created: tests/test_phase10_adaptive_supervisor.py, docs/PHASE_10_IMPLEMENTATION.md.
Modified: supervisor/validation.py (NEW semantics), supervisor/decisions.py,
supervisor/supervisor.py, agents/governance_agent.py (lifecycle-aware
trust-presence rule so a not-yet-verified REGISTERED version does not emit a
spurious MEDIUM), pipeline/selfheal.py (collector reuse), tests/test_supervisor.py
(test updated to assert BOTH legacy (20.0) and adaptive (18.4) semantics — a
documented spec-driven change, not a regression mask), HANDOFF-A.md.

## Phase 11 readiness — exact entry point
None. Per directive: STOP after Phase 10. Do NOT start Phase 11 without owner signal.

# SESSION ADDENDUM 6 — Phase 11 Forensic Reconstruction (BLOCKER)

An exhaustive six-hour forensic reconstruction of Phase 11 was performed
(read-only): full working-tree docs sweep, `git log --all` (13 commits),
`git tag` (`forensic/corpse-archive`, `forensic/pre-split`), `git grep` across
both forensic refs, test-suite scan, and sibling-repo boundary re-check.

**Verdict: Phase 11 CANNOT be reconstructed from authoritative QSMLOps
evidence.** `PART 14 §14.3` is defined only for Phases 1–10 (no §14.3 PHASE 11,
no PART 21 STAGE 11). `DELIVERABLE.md` "Future Roadmap" uses a *separate*
quarter-based label set (Production Hardening / ML Framework / Advanced
Security / Platform Features) and is NOT mapped to "Phase 11". Git history
contains no Phase-11 commit/branch/tag/stub. No Phase-11 test scaffold exists.
The only "Phase 11" text in the forensic refs is FOREIGN Guardrailed material
(`docs/productization/research_boundary.md`: RTS-GMLC "Phase 11-19"),
explicitly off-limits.

Per the mandate's §16, implementation was NOT performed and a fake Phase 11 was
NOT invented. Full evidence trail: `docs/PHASE_11_FORENSIC_BLOCKER.md`.

Repository state unchanged: HEAD `3e494da`, 271 passed, compileall clean, demo
`Chain OK: True`, contamination clean, REPO-B (`guardrailed-product`) untouched
at `bc835e3`. The 26 staged renames from the earlier Guardrailed-residue
isolation task remain intentionally uncommitted (not Phase-11 work).

To unblock: supply the authoritative `PART 14 §14.x PHASE 11` source, or a
concrete bounded scope statement, or confirm a selected Future-Roadmap subset
is to be treated as "Phase 11".

---

# SESSION ADDENDUM — Workstream A1 (HSM PKCS#11 Backend Operationalization)

**Forensic premise:** A previous claim “Workstream A1 — HSM Backend Implementation complete”
was certified as **UN-CERTIFIED**: `PKCS11Backend` did not exist, `create_hsm_backend({'use_hsm': True})`
silently returned `SoftwareFallbackBackend`, no HSM tests, `python-pkcs11` not declared.
Reference: this workstream’s mission brief §§ PHASE 0–23.

**Directive:** Not Phase 11/12; a specifically authorized post-roadmap hardening workstream
A1 that turns the non-certifiable HSM *architecture* into the strongest honest
operational implementation without creating a parallel crypto authority and without
pretending a mock is a physical HSM.

**Entry baseline (forensic):** 271 core tests (pre-A1 HEAD `3e494da` + post-roadmap hardening),
`compileall` clean, `demo.py` SUCCESS, `qsmlops/crypto/hsm.py` = abstraction only
(`PKCS11Backend` absent, factory returned `SoftwareFallbackBackend` on `use_hsm=True`).

**Exit state:** **368 collected (271 prior + 61 A1 + 36 pre-existing hardening)**, all
partitioned runs green (full-suite wall time exceeds the 120 s single-call tool budget,
hence partitioned verification), `compileall` clean, `demo.py` SUCCESS, `Chain OK: True`,
`python-pkcs11` declared, no Guardrailed contamination, REPO-B untouched.

## Implemented (extend-only)

* `qsmlops/crypto/hsm.py` — operational `PKCS11Backend` (895 lines):
  `pkcs11.lib` token/slot discovery, session management, ML-DSA
  (`ML-DSA-44/65/87` via `KeyType.ML_DSA` / `MLDSAParameterSet`),
  real `sign`/`verify` via `SignMixin`/`VerifyMixin`, honest `health_check`,
  explicit `HSMUnsupportedMechanismError` for ML-KEM (no `ML_KEM` in `python-pkcs11` 0.9.5),
  fail-closed `create_hsm_backend` (never falls back when `use_hsm=True`),
  PIN-redacted `__repr__`, no private extraction outside mock fixture.
  `SoftwareFallbackBackend` kept honest (`required_mechanisms_available=False`, `sign` raises).
* `qsmlops/crypto/keys.py` — fix `generate_keypair` to detect explicit `PKCS11Backend`
  vs software fallback, fail-closed HSM path, use `HSMKeyInfo.public_key_hex`,
  no secret serialization for `hsm_backed=True`.
* `qsmlops/passport/passport.py` — fix `sign` to detect HSM-backed active signer
  via `list_records` before `active_signing_key` (which must raise for HSM keys) and
  route to `sign_with_hsm`; verification already routes via `verify_with_hsm`.
* `pyproject.toml` / `requirements.txt` — add `python-pkcs11>=0.9.0` (+ `pydantic` alignment).

## Tests created

`tests/test_hsm_backend.py` (36), `tests/test_hsm_fail_closed.py` (12),
`tests/test_hsm_integration.py` (13) — **61 dedicated A1 tests**.  Mock fixture
(`PKCS11Backend({"mock": True})` / `QSMLOPS_HSM_MOCK=1`) performs **real**
Dilithium signing/verification via `dilithium-py` but is labelled
`"mock backend (test fixture; not a production HSM)"` in every health `details`.
No test claims physical-HSM validation.  Real-token path is implemented against the
actual `python-pkcs11` API and fails closed when no token is present.

## Certification gates A–N

A ✅ (backend exists) · B ✅ (selector fail-closed) · C ✅ (fail closed) ·
D ✅ (key boundary) · E ✅ mock / ENV-LIMITED real · F ✅ (verification) ·
G ✅ (passport) · H ✅ (keystore) · I ✅ (dependency) · J ✅ (61 tests) ·
K ✅ (regression) · L ✅ (no leakage / no silent fallback) · M ✅ (no contamination) ·
N ✅ (doc distinguishes IMPLEMENTED / ENVIRONMENT-LIMITED)

**Final status: IMPLEMENTED BUT ENVIRONMENT-LIMITED** — `PKCS11Backend` is genuinely
implemented, fail-closed semantics work, 61 HSM tests pass, software fallback remains
correct, but physical HSM interoperability cannot be exercised on this Windows host
(no SoftHSM2 / vendor library).  Full report: `docs/HSM_IMPLEMENTATION.md`.

---

# SESSION ADDENDUM — Workstream F1 (Evidence Packet Persistence)

**Forensic question:** Evidence F1 — does the ledger’s promise of “immutable evidence for every operation” (packet.py, ARCHITECTURE.md, DELIVERABLE.md) require durable packet bodies, given that `EvidenceLedger.append_packet()` previously committed only 5 fields + digest and lost `security_checks`/`proofs`/`artifacts`/`metrics`?

**Authority elevation:** `POST_ROADMAP_ENGINEERING_AUDIT.md:129` and `POST_ROADMAP_HARDENING_IMPLEMENTATION.md:5` deferred F1 as DOCUMENTED FUTURE (“out of scope”). Re-investigation shows the gap is a **hardening defect**: DELIVERABLE’s “Verification Packets: Immutable evidence” + ledger as “authoritative store” + packet creation in `registry.py:367` (with full proofs) are AUTHORITATIVE. The ledger hash commits to `packet.digest()` but without the preimage the commitment is unverifiable — an auditor cannot reconstruct *why* a decision was VERIFIED. Using the existing `ArtifactStore` content-addressed primitive, this is a small, safe, architecture-consistent fix (no new infra, no PostgreSQL).

**Design (content-addressed, not embedded):** `VerificationPacket.to_dict()` → `canonical_json` → `sha3_hex` (packet.digest) → `ArtifactStore.put(canonical)` under `<home>/ledger/packets/<digest[:2]>/<digest>` → ledger entry `{type:verification_packet, packet_id, digest, objective, actor, decision}`; retrieval via `get_packet`/`get_packet_by_digest` digest-verified; `packet_id` unique (second append → `LedgerError` immutability); sensitive field names (`private_key`, `secret_key`, `hsm_pin`, `pin`, `passphrase`, `credential`) rejected fail-closed; `verify_chain` unchanged; old ledger entries remain readable (`get_packet` → `None`, `verify_packet` → “missing”).

**Entry baseline:** 400 collected (368 prior + 32 F1), partitioned green, `compileall` clean, `demo` SUCCESS, `verify_chain` intact, 26 guardrailed_residue renames staged.

**Exit state:** **400 collected, 32 new F1 tests, all partitions green, `compileall` clean, `demo` SUCCESS (30 entries), `verify_chain` intact, `audit-ledger-packets` all intact for new packets, API `GET /evidence/packet/{id}` + `GET /evidence/packets` + `GET /evidence/packet/by-digest/{d}` and CLI `show-packet`/`audit-ledger-packets` added.**

**Implemented:** `qsmlops/evidence/ledger.py` (packet store, `append_packet` store-before-ledger, `get_packet*`, `verify_packet`, `list_packet_ids`, sensitive check, `_path_for` tamper vs missing distinction), `qsmlops/config.py:32` + `core/settings.py:110` `packet_store_path`, `qsmlops/api/app.py:387` evidence packet routes (404 not 500), `qsmlops/cli.py:305` `show-packet`/`audit-ledger-packets`, `tests/test_evidence_packet_persistence.py` (32), `docs/EVIDENCE_PACKET_PERSISTENCE.md`.

**Tests:** 32 F1 (persistence 6, integrity 6, ledger 4, security 5, compatibility 2, integration 2, adversarial 7) — all green. No HSM regression.

**Final status: COMPLETE** — packet persistence is AUTHORITATIVE hardening, implemented, content-addressed, digest-bound, immutable, tamper-detected, backward compatible, no secret leakage, no duplicate authority. Full report: `docs/EVIDENCE_PACKET_PERSISTENCE.md`.
