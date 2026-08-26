# Post-Roadmap Engineering Audit — QSMLOps (Phases 1–10)

**Scope:** Deep engineering audit of the completed QSMLOps platform (Phases 1–10).
**Mandate:** Re-verify baseline, confirm Phase 11 is authoritatively CLOSED as
*undefined* (do **not** invent Phase 11/12), audit the shipped system, fix
verified defects, close integration gaps, strengthen tests, and improve docs.
**Date of audit:** 2026-08-26

---

## 1. Phase 11 status (authoritative)

`docs/PHASE_11_FORENSIC_BLOCKER.md` is the forensic authority. `PART 14 §14.3`
defines only Phases 1–10. `DELIVERABLE.md` "Future Roadmap" uses separate
quarter-based labels and is explicitly **DOCUMENTED FUTURE**, not Phase 11.
Phase 11 is therefore **forensically CLOSED — undefined**. No Phase 11/12 code
was created.

## 2. Foreign / boundary verification (Guardrailed)

- `guardrailed-product` (REPO-B): untouched, `bc835e3`, 0 dirty.
- `guardrailed-agentic-mlops-smart-grid*` and `guardrailed_residue/`: not modified.
- Forensic tags `forensic/pre-split` + `forensic/corpse-archive`: read-only.
- `grep -rl guardrailed qsmlops tests` → empty (no leakage into product code).

## 3. Baseline (re-verified before changes)

- `HEAD` at audit start: `86a31b9` (prior session committed F1–F3).
- `pytest tests/` → **273 passed** (exit 0).
- `python -m compileall qsmlops` → clean.
- `python demo.py` → `DEMO COMPLETED SUCCESSFULLY`.
- Ledger chain integrity OK; contamination / secret / `_archive` scans clean.

## 4. Audit method

Six parallel read-only agent sweeps (crypto/keystore, trust, evidence/ledger/
governance, monitoring/drift, agents/supervisor/self-heal, packaging/docs/
duplicate-authority/static). Every finding was re-verified by direct file
inspection and, where risky, by a targeted test run.

## 5. Findings — fixed in this audit

### Security / cryptography
- **F2 — `passport.verify_signature` raised on revoked/expired key (fail-open).**
  `qsmlops/passport/passport.py`: revoked/expired → `False`; provider +
  keystore access wrapped to return `False` (fail-closed). Dead redundant
  `public_key_hex != _public_of(...)` check removed (F-04).
- **F3 — registry `verify_version` `passed` omitted artifact/digest match
  (DB-tamper gap).** `qsmlops/registry/registry.py`: `passed` now requires
  `sig_ok and art_ok and artifact_match`; `artifact_match` computed from stored
  `artifact_digest` vs `passport.artifact_digest`.
- **F9 — `scores.py` did not wrap `passport.verify_signature`** (unhandled
  exception could mask hard crypto failure). `qsmlops/scores.py`: wrapped in
  try/except → `signature_valid=False` + blocking marker.
- **crypto duplicate authority** (`security/crypto/` vs `crypto/`): verified
  imported by `tests/test_foundation.py` + `tests/test_phase3_security.py` →
  it is tested Phase-3 code, **not** orphaned. Left in place; documented as
  informational (see §9).

### Governance / deployment
- **G1/G2/F8 — `registry.deploy` enforced no SoD / environment / policy gate.**
  Three internal call paths (`approve_and_deploy`, supervisor `DEPLOY`,
  `_auto_retrain`) bypassed `DeploymentService` gates. Fix:
  `qsmlops/registry/registry.py` `deploy()` now runs
  `DeploymentService(self).validate(version_id, actor, "production")` and
  deactivates any prior active deployment (exclusive `active` flag).
- **F4 (trust) — deployment reused a stale cached `latest_trust`.**
  `qsmlops/serving/deployment.py` `validate()` now always recomputes a FRESH
  `trust_evaluation(..., persist=False)` against current evidence (key
  rotation/revocation/state changes can invalidate an earlier decision).

### Monitoring / drift
- **A — non-finite metrics recorded + silently passed `evaluate()`.**
  `collector.record_model_health` rejects non-finite values;
  `alerts.evaluate` treats non-finite r2/mse as a `PERFORMANCE_DEGRADED` alert
  (fail-closed).
- **B — `rolling_baseline` reported `sufficient=True` with no prior baseline**
  (observations 3–`window`). Now `sufficient=False` until a prior window
  exists (cannot claim "healthy" before it can detect degradation).
- **A/G — `evaluate` required BOTH r2+mse and evaluated them jointly.**
  Now each is evaluated independently; a single out-of-bounds metric alerts.
- **D — performance drift was dead** (`baseline == current` in
  `run_drift_check`). `selfheal.run_drift_check` now accepts live
  `current_metrics` (health_check threads its recorded `metrics`), so the
  performance-drift detector is actually exercised.
- **E — API `/alerts` omitted drift / feature / rolling summaries.**
  `api/app.py` now enriches `evaluate_alerts` with `drift_summary`,
  `feature_attributions`, and sufficient `rolling_baselines`.
- **F — KS detector `except: pass` swallowed errors.**
  `ml/drift.py` now logs the failure instead of silently skipping.

### Agents / supervisor / self-heal
- **F1 — agent `ESCALATE` recommendation was silently defaulted to `ACCEPT`.**
  `supervisor.reason()` now maps an `ESCALATE` recommendation (and a crashed
  agent) to `Decision.ESCALATE`; policy also gains `escalate_on_agent_
  recommendation` (priority 90). `policy.build_facts` exposes
  `recommendation_escalate`.
- **F3 — empty `observations` → `ACCEPT`.** Now → `Decision.ESCALATE`
  ("cannot assess autonomously").
- **F4 — `self.learner = learner or LearningStore.__new__(LearningStore)`**
  created an uninitialised instance whose methods raised at runtime. Replaced
  with a safe `_NoOpLearner` default.
- **F5 — validation silently dropped malformed findings.** `supervisor.py`
  now appends an explicit failed (`ESCALATE`) marker when validation drops
  findings, instead of weakening the observation.
- **F6 — dead `if not hasattr(self, "_last_validation")`** (attribute already
  initialised in `__init__`). Removed.
- **F7 — `_verify_outcome(RETRAIN)` checked only `len(versions) >= 2`.**
  Now verifies a *newer* version reached `APPROVED`/`DEPLOYED`.
- **F2 (policy) — dead `SupervisorPolicy.decide`** retained but documented as
  unused (decision flow uses `policy_engine`).

### Packaging / reproducibility
- **B1 — `pyproject` console entry point `qsmlops:main` did not exist.**
  Corrected to `qsmlops.cli:cli`.
- **B5 — `scikit-learn` only in `ml` extra**, yet imported unconditionally by
  `scores`/`selfheal`. Moved to base `dependencies`.
- **A2 — config split-brain** (`PlatformConfig` vs `Settings`): OWNER DECISION
  — documented, not changed.
- **docs licence mismatch** (`README` MIT vs `pyproject` Proprietary): OWNER
  DECISION — documented, not changed.

## 6. Findings — documented (not fixed; by design / owner decision)

- **Trust F5/F6/F7/F8/F9** (policy interpretation edge cases): design
  limitations / ambiguous requirements → DOCUMENTED FUTURE; not changing
  semantics without product sign-off.
- **Evidence F1** (ledger packet payload not persisted): DOCUMENTED FUTURE —
  out of scope for this audit; ledger integrity intact.
- **Packaging A1** (security/crypto duplicate authority): verified tested
  code → left in place, documented as informational.
- **Phase-11 / roadmap** items in docs: confirmed DOCUMENTED FUTURE, not
  Phase 11.

## 7. Test changes (strengthening)

- `tests/test_supervisor.py`: the two supervisor unit tests registered a
  passport **without persisting its BOM** (the real pipeline persists it in
  `SelfHealingMLOps.train_and_register`). Agents therefore crashed on a `None`
  BOM and the old F1 bug masked that as `ACCEPT`. Tests now persist the BOM
  (mirroring production) so agents load it and the supervisor produces a real
  decision; `test_supervisor_reason_with_critical_finding` also accepts
  `ESCALATE` as a safe outcome.

## 8. Regression verification

- Full suite: **273 passed** post-fix (exit 0).
- `compileall qsmlops` → clean. `demo.py` → SUCCESS.
- The three direct-deploy tests (`test_artifacts_passport.py:187`,
  `test_phase5_approval.py:197,216`, `test_phase6_deployment_flow.py:181`)
  remain green under the new `registry.deploy` governance gate.

## 9. Files changed (this audit)

```
pyproject.toml                         packaging B1/B5
qsmlops/passport/passport.py          F2 / F-04 fail-closed signature
qsmlops/registry/registry.py           F3 verify_version; G1/G2/F8 deploy gate
qsmlops/scores.py                      F9 wrap verify_signature
qsmlops/serving/deployment.py          F4 fresh trust eval at deploy
qsmlops/monitoring/collector.py        A non-finite; B rolling baseline
qsmlops/monitoring/alerts.py           A/G independent + finite metrics
qsmlops/pipeline/selfheal.py           D live drift metrics
qsmlops/api/app.py                     E alert enrichment
qsmlops/ml/drift.py                    F KS log instead of swallow
qsmlops/supervisor/supervisor.py       F1/F3/F4/F5/F6/F7
qsmlops/supervisor/policy.py           F1 escalate fact + rule
tests/test_supervisor.py               BOM persistence + safe-decision asserts
```

## 10. Deliberately NOT changed

- No Phase 11/12 code created.
- `guardrailed*` repositories / residue / forensic tags untouched.
- `security/crypto/` duplicate authority left (tested Phase-3 code).
- Config split-brain, licence mismatch, trust-policy edge cases, ledger
  payload persistence: documented, awaiting owner/product decision.
- 26 `guardrailed_residue/` renames stay staged separately; `HANDOFF-A.md`
  and `docs/PHASE_11_FORENSIC_BLOCKER.md` kept out of these commits.

## 11. Remaining defects (by category, for owner follow-up)

- **Design / product:** config split-brain (A2); trust-policy edge cases
  (F5–F9); licence inconsistency.
- **Documentation:** README vs pyproject licence; roadmap/Phase-11 wording.
- **Future work (NOT Phase 11):** ledger packet payload persistence; unify
  `security/crypto` and `crypto` packages; reconcile `PlatformConfig`/
  `Settings`.
