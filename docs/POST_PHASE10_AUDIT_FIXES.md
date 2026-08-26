# Post-Phase-10 Audit & Hardening (24-hour forensic-closure window)

**Scope decision (authoritative):** Phase 11 was forensically closed as *undefined* in
`docs/PHASE_11_FORENSIC_BLOCKER.md` (PART 14 §14.3 defines only Phases 1–10; no
Phase 11/Stage 11 exists in any authoritative source; the only "Phase 11" material is
FOREIGN Guardrailed research numbering, off-limits per §0/§12). Per the mandate, this
window did **not** invent a Phase 11/12. Instead it performed the mandated high-value
repository work: boundary protection, baseline verification, a deep system audit, and
fixing only *verified* defects.

## Baseline (verified at window start)
- HEAD `3e494da` (Phase 10 committed). Foreign repo `guardrailed-product` @ `bc835e3`, 0 dirty (untouched).
- `compileall` clean; full suite **271 passed**; `demo.py` SUCCESS; ledger chain OK.
- Contamination scan: zero `guardrailed`/`backend_api`/`frontend`/`product/` references in `qsmlops/` source.

## Audit method
Traced the full lifecycle (config→identity→dataset→training→passport→QML-BOM→store→
signing→verification→ledger→registry→trust→approval→deployment→serving→monitoring→
drift→agents→supervisor→policy→retraining) with emphasis on §4 / §17 risks:
API↔CLI parity, trust/approval/deployment gate enforcement, evidence completeness,
duplicate/orphaned authorities, and foreign contamination.

## Findings & fixes (all evidence-based, none invent new scope)

### F1 — CLI `deploy` was broken AND bypassed the governed deployment path (§17A/§17C)
`qsmlops/cli.py:deploy` called `registry.deploy(active["version_id"], "cli")` on the
*currently active* (already-DEPLOYED) version, which `registry.deploy` rejects (it
requires APPROVED state). The command could never deploy a newly approved model, and it
skipped the governed `DeploymentService` (identity, SoD, crypto, trust eligibility,
environment, policy gates) that the REST API's `/deployment/request` enforces.
**Fix:** `deploy` now routes through `pipeline.request_deployment(model_name=…, actor="cli")`,
resolving the latest APPROVED version and running every gate — identical to the API path.

### F2 — Dead/duplicate method definitions in `SelfHealingMLOps` (§4)
`request_deployment` and `validate_deployment` were defined twice in `qsmlops/pipeline/selfheal.py`
(lines 121/138 and 675/694). In Python the later definitions silently overrode the earlier
identical ones — dead code that creates drift risk if one copy is edited.
**Fix:** removed the duplicate trailing definitions; originals retained.

### F3 — Orphaned Guardrailed bytecode in `tests/product/` (boundary protection)
`tests/product/` contained only untracked, package-less `__pycache__/*.pyc` referencing
`test_forecast` / `test_forecast_targets` / `forecast_status` — Guardrailed smart-grid
forecasting concepts, not QSMLOps. No `.py`, no `__init__.py`, not git-tracked, not
collected by pytest. Inert, but a boundary violation.
**Fix:** removed `tests/product/` entirely.

## Verification after fixes
- `compileall` clean.
- New regression tests added (`tests/test_phase5_cli.py::TestDeployCli`): deploy succeeds
  for the latest APPROVED version; deploy is DENIED (structured) when no APPROVED version exists.
- Full suite: **273 passed** (271 + 2 new).
- `demo.py`: SUCCESS (demo-model v2/v3 DEPLOYED); ledger chain OK.

## What was deliberately NOT done
- No Phase 11/12 implementation (undefined per forensic closure).
- No HSM/KMS, Kubernetes, or external-integration features (out of authoritative scope;
  `DELIVERABLE.md` Future Roadmap items are a separate-label DOCUMENTED FUTURE backlog, not Phase 11).
- No modification of `guardrailed-product`, `guardrailed_residue/`, or forensic git tags (read-only).
- No commit of the 26 pre-existing staged residue renames or the Phase-11 blocker doc
  (those belong to separate prior tasks and remain intentionally uncommitted here).
