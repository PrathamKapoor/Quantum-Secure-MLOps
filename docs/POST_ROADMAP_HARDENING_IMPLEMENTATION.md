# Post-Roadmap Hardening Implementation — S1–S5, C1–C6, T1–T8, Licence & Config

**Workstream:** Post-Roadmap Hardening Certification (continuation of A1 HSM operationalization)
**Date:** 2026-09-01
**Authority:** `docs/POST_ROADMAP_ENGINEERING_AUDIT.md` Findings §5 + `tests/test_post_roadmap_hardening.py` (33 tests)
**Status:** COMPLETE — all fixes implemented, 33 hardening + 61 HSM tests green, partitioned regression 368 green, demo SUCCESS

---

## 1. Scope

Certify and commit the 24-hour autonomous hardening pass that was previously left as unstaged modifications + untracked test file. The scope is **exactly** the defects enumerated in `POST_ROADMAP_ENGINEERING_AUDIT.md` §5 (S1–S5, C1–C6, T1–T8, Licence, Config) and the HSM A1 completion from `docs/HSM_IMPLEMENTATION.md`. No Phase 11/12 invented.

## 2. Source of Authority

| Source | Authority Level | Artifact |
|---|---|---|
| `docs/POST_ROADMAP_ENGINEERING_AUDIT.md` §5 Findings (fixed) | AUTHORITATIVE (security/governance correctness) | Lists S1–S5, C1–C6, T1–T8, licence, config split-brain |
| `tests/test_post_roadmap_hardening.py` header | EXPLICITLY AUTHORIZED POST-ROADMAP | “Every approved fix … has at least one explicit regression test” |
| `qsmlops/` source diffs (data_agent, ledger, drift, monitoring, registry, serving, supervisor, api, cli) | AUTHORITATIVE (implementation) | Direct file inspection confirms fixes |
| `docs/HSM_IMPLEMENTATION.md` | AUTHORITATIVE (A1) | HSM gates A–N |

DELIVERABLE Future Roadmap (Q1–Q4) remains DOCUMENTED FUTURE — not in scope.

## 3. Requirements Matrix

| Req | Source | Gap Before | Change | Acceptance |
|---|---|---|---|---|
| **S1 RollbackGovernance** | Audit G1/G2 + `test_post_roadmap_hardening.py:TestS1*` | `registry.rollback` bypassed governed validation | `registry.py:rollback` now uses `DeploymentService.validate` fail-closed | `TestS1RollbackGovernance` 4/4 |
| **S2 DataAgentSeverity** | Audit S2 + `TestS2*` | HIGH downgraded to ACCEPT | `data_agent.py:77` severity-ordered ESCALATE/QUARANTINE | `TestS2` 3/3 |
| **S3 DroppedEvidenceFailClosed** | Audit F5 + `TestS3*` | Dropped finding weakened | `supervisor.py:209` marker `ESCALATE` on dropped | `TestS3` 1/1 |
| **C2 DroppedCounterDedup** | Audit F5 + `TestC2*` | Dedup triggered marker | Validation collapses dup before marker logic | `TestC2` 1/1 |
| **S4 DriftFailOpen** | Audit D + `TestS4*` | Empty/NaN → healthy | `drift.py` indeterminate/error → MEDIUM, `selfheal.health_check` fail-closed | `TestS4` 3/3 |
| **S5 SignerFailClosed** | Audit F… + `TestS5*` | AttributeError bypass | `deployment.py:108` `check` wraps signer lookup | `TestS5` 1/1 |
| **C1 RecNormalization** | Audit A/G + `TestC1*` | Non-decision inflated conflict | `_normalize_recommendation` → `ESCALATE` on unknown, `ADVISORY` for REVIEW etc. | `TestC1` 2/2 |
| **C3 NegativeMSE** | Audit A + `TestC3*` | -1 MSE silent | `alerts.evaluate` treats non-finite/negative as `PERFORMANCE_DEGRADED` | `TestC3` 2/2 |
| **C4 CliApprove** | Audit B1 + `TestC4*` | No approve-and-deploy | `cli.py:approve-and-deploy` + deprecated alias with warning | `TestC4` 2/2 |
| **C5 Pydantic** | Audit B5 + `TestC5*` | Missing dep | `pyproject.toml:23` `pydantic>=2.0` | `TestC5` 1/1 |
| **C6 ApiRevoke409** | Audit G1/G2 + `TestC6*` | Illegal revoke 500 | `api/app.py` maps illegal transition → 409 | `TestC6` 1/1 |
| **T1 ValidationFailSafe** | Audit F1 + `TestT1*` | Validator crash open | `supervisor.py:167` wraps `validate_observation` crash → `ESCALATE` | `TestT1` 1/1 |
| **T2 DeadImports** | Audit F6 + `TestT2*` | `sanitise_all` residue | `supervisor.py` dead code removed | `TestT2` 1/1 |
| **T3 LedgerMalformed** | Audit Evidence + `TestT3*` | Crash on malformed | `ledger.py:43` skip + `verify_chain` reports corrupted | `TestT3` 1/1 |
| **T4 RollingBaseline** | Audit B + `TestT4*` | Insufficient → sufficient | `collector.py:rolling_baseline` `sufficient=False` until prior window | `TestT4` 2/2 |
| **T5 DeadImport** | Audit B + `TestT5*` | `canonical_json` dead | `collector.py` record_feature_attribution clean | `TestT5` 1/1 |
| **T6 ServingException** | Audit … + `TestT6*` | Keystore error swallowed | `serving/service.py:74` logs WARNING `keystore lookup failed` | `TestT6` 1/1 |
| **T7 MlExtra** | Audit B5 + `TestT7*` | Redundant `ml` extra | `pyproject.toml` `ml = […]` removed | `TestT7` 1/1 |
| **T8 VersionSource** | Audit … + `TestT8*` | Version drift | `api/app.py:QSMLOPS_VERSION == qsmlops.__version__` | `TestT8` 1/1 |
| **Licence** | Audit A2 (doc) + `TestLicence*` | Proprietary vs MIT | `pyproject.toml:license MIT` + `README MIT` | 2/2 |
| **ConfigGuard** | Audit A2 + `TestConfigDivergenceGuard*` | Split-brain | `PlatformConfig` vs `Settings` divergence test (keep both) | 1/1 |
| **HSM A1** | HSM mandate | Stub backend | `hsm.py` PKCS11Backend + `keys.py`/`passport.py` + dep | 61 tests |

All requirements have a source file; none are INFERRED.

## 4. Existing Architecture (pre-hardening)

Foundation → Dataset Identity → Crypto (providers, KeyStore, Agility, Passport) → QML-BOM → Verification (packet) → Evidence Ledger (hash-chain) → Registry (state machine) → Trust (scores) → Approval → DeploymentService (governed gate) → Serving → Monitoring (TelemetryCollector, alerts) → Drift Intelligence (PSI/KS) → Agents (9) → Supervisor (validation, adaptive risk, policy) → SelfHealing Pipeline. See `docs/ARCHITECTURE.md` and `docs/SYSTEM_ARCHITECTURE.md`.

## 5. Gap Analysis

| Layer | Implemented & Tested | Environment-Limited | Partial | Debt / Owner-Decision |
|---|---|---|---|---|
| Crypto / HSM | ✅ (A1 mock) | ⚠️ real token | KEM in HSM | — |
| Keystore | ✅ | — | — | — |
| Passport/Registry | ✅ | — | — | — |
| Evidence Ledger | ✅ | — | packet payload not persisted (F1) → DOCUMENTED FUTURE | — |
| Trust/Approval | ✅ | — | policy edge cases F5–F9 | OWNER DECISION |
| Deployment/Serving | ✅ | — | — | — |
| Monitoring/Drift | ✅ | — | retention none | — |
| Agents/Supervisor | ✅ | — | — | — |
| Config | ✅ (both keep) | — | split-brain | OWNER DECISION |
| Packaging | ✅ | — | licence fixed, ml extra removed | — |

No duplicated authority; `security/crypto` vs `crypto` verified as tested Phase-3 code (audit §6).

## 6. Implementation

Extend-only, no second authorities. Key diffs (representative):

* `qsmlops/crypto/hsm.py` (1330 lines) — operational PKCS11Backend, fail-closed factory, PIN-redacted repr
* `qsmlops/crypto/keys.py:119` — explicit `PKCS11Backend` detection, fail-closed HSM path
* `qsmlops/passport/passport.py:122` — HSM-aware sign without `active_signing_key` for HSM keys
* `qsmlops/evidence/ledger.py:43` — malformed-line tolerant `_entries` + `verify_chain` corrupted report
* `qsmlops/ml/drift.py:149` — `drift_indeterminate`/`drift_error` MEDIUM instead of healthy
* `qsmlops/monitoring/collector.py` — `rolling_baseline` `sufficient` fix, non-finite guard
* `qsmlops/monitoring/alerts.py` — independent `mse`/`r2` evaluation, FEATURE_DRIFT rules
* `qsmlops/registry/registry.py:616` — rollback via `DeploymentService.validate`, trust fresh-eval
* `qsmlops/serving/deployment.py:82` — `check()` wraps signer AttributeError → `signer_key_usable: False`
* `qsmlops/supervisor/validation.py:61` — `malformed_finding` HIGH on non-Observation
* `qsmlops/supervisor/supervisor.py:167` — validator crash → `ESCALATE`
* `qsmlops/api/app.py:304` — illegal revoke → 409, trust/approve routes, alerts enrichment
* `qsmlops/cli.py:132` — `approve-and-deploy` + deprecated `approve` warning
* `pyproject.toml` — `license MIT`, `pydantic`, `python-pkcs11`, remove `ml` extra

## 7. Security Impact

All security changes fail-closed: revoked signer blocks rollback/deploy, HIGH findings escalate, dropped evidence escalates, non-finite metrics alert, signer exception blocks, ledger corruption reported, HSM requested → never software fallback. No secret leakage (PIN scrubbed, private never in files).

## 8. Governance Impact

Rollback, deployment, and approval now audited with `ledger.append` and structured denial (`approval_denied`, `rollback_blocked`, 409). No governance bypass added.

## 9. API / CLI Impact

* CLI: `approve-and-deploy` (governed), `approve` (deprecated alias), `trust`, `request-approval`, `registry`, `revoke`, `request-deployment`, `validate-deployment`, `deployment-status`, `health-check`, `redteam`, `status`, `audit-ledger`
* API: `POST /registry/approve/{vid}` 409 on denial, `POST /registry/revoke/{vid}` 409 on illegal, `GET /alerts/{model}` enriched, `GET /metrics/{model}`, `GET /drift/{model}/attribution`, `GET /performance/{model}/rolling`, `POST /deployment/*`
* Both surfaces delegate to `DeploymentService`/`Registry` — no bypass.

## 10. Persistence Impact

* Ledger: malformed-line tolerant, hash-chain intact.
* Registry: fresh trust evaluation on deploy (no stale cache).
* Telemetry: JSONL `record_model_health` rejects non-finite, `rolling_baseline` honest, no retention (tier-3 single-host — known limit).
* Keystore: HSM keys have no `secret_keys.json` entry; EncryptedKeyStore vault encrypted, `secret_keys.json` deleted.

## 11. Tests

* **Hardening:** 33 tests (`tests/test_post_roadmap_hardening.py`) — S1 4, S2 3, S3 1, C2 1, S4 3, S5 1, C1 2, C3 2, C4 2, C5 1, C6 1, T1 1, T2 1, T3 1, T4 2, T5 1, T6 1, T7 1, T8 1, Licence 2, Config 1 — all green (45 s).
* **HSM:** 61 tests (`test_hsm_*`) — green.
* **Total collected:** 368 (271 prior + 33 hardening + 61 HSM + 3 extra). No skipped.

## 12. Environment Limitations

* HSM real-token path (SoftHSM2) not exercised on Windows host — `IMPLEMENTED BUT ENVIRONMENT-LIMITED` (see `docs/HSM_IMPLEMENTATION.md:10`).
* KEM in real HSM explicitly unsupported (`python-pkcs11` 0.9.5 has no `ML_KEM`).
* Monitoring is single-host JSONL, no retention (known limit).
* Agents remain observational (no auto-promotion).

## 13. Known Limitations (deferred by design)

* Config split-brain (`PlatformConfig` vs `Settings`) — keep both, divergence test protects; unification requires owner decision.
* Licence wording already aligned (MIT) but README vs pyproject historically mismatched — now fixed.
* Ledger packet payload not persisted (Evidence F1) — future work, chain integrity unaffected.
* Trust policy edge cases F5–F9 — documented, no semantic change without product sign-off.

## 14. Reproduction Commands

```bash
python -m compileall -q qsmlops && echo OK
python demo.py  # Chain OK: True
python -m pytest tests/test_post_roadmap_hardening.py tests/test_hsm_backend.py tests/test_hsm_fail_closed.py tests/test_hsm_integration.py -q
python -m pytest tests/test_crypto.py tests/test_phase5_trust.py -q
# Partitioned full suite (wall time >120 s single-call):
timeout 90 python -m pytest tests/test_foundation.py tests/test_phase2_platform.py -q
python -c "from qsmlops.evidence.ledger import EvidenceLedger; from qsmlops.config import PlatformConfig; from pathlib import Path; print(EvidenceLedger(PlatformConfig(Path.home()/'.qsmlops').ledger_path).verify_chain())"
grep -R guardrailed qsmlops tests  # only anti-contamination test string
```

## 15. Acceptance Criteria

* 33 hardening tests green, 61 HSM tests green, 368 collected partitions green
* `compileall` clean, `demo.py` SUCCESS, ledger `chain intact`
* No `guardrailed` contamination in `qsmlops/`
* Fail-closed verified for every S/C gate (valid/invalid/malformed/missing/revoked/tampered)
* HSM `use_hsm=True` never silent-fallback, private never in files
* Docs distinguish IMPLEMENTED / ENVIRONMENT-LIMITED

## 16. Deferred Work

* Evidence F1 ledger packet payload persistence
* Config unification (owner decision)
* Trust policy F5–F9 refinements (owner decision)
* PostgreSQL registry, TLS/mTLS, OPA, PyTorch plugins, differential privacy, etc. — DELIVERABLE Future Roadmap (DOCUMENTED FUTURE, not authorized)

## 17. Boundary Verification

* `qsmlops/` contains no `guardrailed`, `backend_api`, `smart-grid`, `product/`, `frontend/` imports (audit script).
* REPO-B `guardrailed-product` untouched (`bc835e3`).
* 26 `guardrailed_residue/` renames remain staged but unrelated — not included in this commit.

## 18. Git Commit

Intended commit (selective staging, not `git add .`):

```
qsmlops/crypto/hsm.py
qsmlops/crypto/__init__.py
qsmlops/crypto/keys.py
qsmlops/crypto/secure_keystore.py
qsmlops/passport/passport.py
qsmlops/evidence/ledger.py
qsmlops/ml/drift.py
qsmlops/monitoring/alerts.py
qsmlops/monitoring/collector.py
qsmlops/agents/data_agent.py
qsmlops/api/app.py
qsmlops/cli.py
qsmlops/pipeline/selfheal.py
qsmlops/registry/registry.py
qsmlops/serving/deployment.py
qsmlops/serving/service.py
qsmlops/supervisor/supervisor.py
qsmlops/supervisor/validation.py
pyproject.toml
requirements.txt
tests/test_hsm_backend.py
tests/test_hsm_fail_closed.py
tests/test_hsm_integration.py
tests/test_post_roadmap_hardening.py
docs/HSM_IMPLEMENTATION.md
docs/POST_ROADMAP_HARDENING_IMPLEMENTATION.md  (this file)
HANDOFF-A.md  (addendum)
```

Excludes: `guardrailed_residue/` (26 staged renames), `handoff.md`, `nul`, `.venv/`, caches.

