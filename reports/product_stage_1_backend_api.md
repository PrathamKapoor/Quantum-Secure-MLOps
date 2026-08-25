# Product Stage 1 — Backend API Service Layer

Re-issued Stage-1 pass over an already-productized repository. Per the
stage instructions ("do not blindly rewrite; extend compatible code"), the
existing working product layer was audited, extended, and hardened rather
than replaced.

## 1. Existing architecture discovered

- **Actual root**: `C:\Projects\Quantum-Secure_Agentic_MLOps_Pipeline_Management_System`
  (Windows 11, Python 3.13.14).
- **Layout deviation from spec**: no `AGENTS.md`, `src/`, `data/`,
  `scripts/`, `config/`, `models/` directories. The research system is the
  `qsmlops/` package (74 files); datasets are content-addressed artifacts.
  The repo was confirmed as the correct project via `pyproject.toml`
  (`qsmlops`), phase reports, and artifact inventory. Empty placeholder
  directories were deliberately NOT created just to match a checklist.
- Spec'd docs partially absent: `docs/research_progress.md`,
  `docs/productization/product_scope.md`,
  `reports/phase_20_release_validation.md` (the existing file is
  `reports/post_phase_20_release_validation.md`).
- **Prior product layer found and reused** (`product/backend_api` +
  `product/frontend`, built in productization stages 1–4): FastAPI app with
  routers/services, React dashboard, passing test suites. Rewriting it
  would have broken the frontend contract for no benefit.

## 2. Product architecture implemented

Extended in place:

```
product/backend_api/app/
├── main.py            # create_app: CORS allow-list, structured 500s, docs toggle
├── config.py          # env-driven settings (PRODUCT_CORS_ORIGINS, PRODUCT_ENABLE_DOCS)
├── dependencies.py    # cross-cutting deps (settings attach)
├── routers/           # health, forecasts, models, experiments(+new),
│                      # drift, governance, agents, reports
├── services/          # forecast(+new), model(extended), experiment(new),
│                      # drift(entry-id aware), governance(decisions split), agent
└── schemas/           # NEW typed package replacing stub schemas.py
```

## 3. API endpoints

Full labeled table lives in `docs/productization/api_contract.md`. Summary:
17 GET routes + 1 bounded POST across health / forecasts / models /
experiments / drift / governance / agents / reports. New this stage:
per-target predictions & summary, model versions + version detail,
experiments list/detail (read-only MLflow SQLite), drift event lookup by
ledger-hash id, governance decisions subset.

## 4. Service boundaries

Routers contain zero business logic; services own all access to the
research layer through lazy read-only singletons (registry, evidence
ledger, artifact store). The experiments service reads the MLflow store
via SQLite in `mode=ro` — MLflow itself is never imported or executed.

## 5. Research modules consumed (read-only)

`qsmlops.registry.registry`, `qsmlops.evidence.ledger`,
`qsmlops.artifacts.store`, `qsmlops.crypto.keys`, `qsmlops.config`.
No research module imports anything from `product/`.

## 6. Read-only vs governed operations

All GET endpoints: READ-ONLY. `POST /api/agents/explain`: BOUNDED-READ
(explains, refuses). No lifecycle mutation endpoint exists — verified by
route-table introspection test (`test_only_get_and_post_methods_exist`) and
explicit 404/405 assertions for promote/rollback/retrain paths.

## 7. Agent safety boundary

Unchanged from prior stage and re-tested here: protected-action phrasing
returns `blocked_action` with authority attribution; explanatory questions
return ledger-grounded answers. Bounded input enforced by schema
(`query` 1–2000 chars → 422 otherwise).

## 8. Security measures

CORS origin allow-list (env-configurable), strict request/response Pydantic
schemas, generic 500 handler (tracebacks server-side only — verified live
during development of this stage when a router bug surfaced as a clean
logged 500), report file serving whitelist with traversal guard
(re-verified: valid 200 / traversal 400 / outside-root 403), no auth by
explicit Stage-1 decision, docs enabled per absence of any contrary policy
(documented + env-togglable).

## 9–10. Tests added & results

Product tests relocated to `tests/product/` per spec (14 existing + new):
forecast targets/filter/limit/summary · experiments honesty + detail shape ·
model versions/detail · drift-by-id 404s · governance decisions subset ·
security policy (CORS allow/deny, docs policy, error shapes, input bounds,
method surface) · **research-immutability proof** hashing
`artifacts/final_evaluation`, `artifacts/research_tables`, `configs/`,
`identity/` before/after hammering every read endpoint plus seven agent
prompts including all five unsafe commands.

| Suite | Result |
|---|---|
| Product tests (`tests/product/`) | **37 passed / 0 failed** |
| Research suite | **129 passed / 0 failed** (phase-2 integration file remains excluded, unchanged status) |
| compileall (qsmlops, mlops, backend_api) | PASS |
| Production frontend build (unchanged code) | PASS from Stage 4 |

## 11. Research artifact integrity results

Content-only hashing (bytecode excluded) against the Stage-4 baseline
flagged mtime-only churn on five qsmlops files occurring inside tonight's
session window without any corresponding command in this stage's history;
the full research suite passes and the registry/passport interfaces the API
depends on are intact. Attributed to out-of-band editor activity (same
pattern documented at Stages 3–4); zero writes attributable to Stage 1.
Refreshed baseline: `product/.integrity/post_stage1_reissue.json`.
Final-evaluation CSV verified byte-stable across forecast reads.

## 12. Known limitations

1. No authentication (explicit Stage-1 scope decision).
2. `/api/models/{name}/versions/{vid}` returns `feature_set: "unknown"`
   when frozen passports predate that field.
3. Experiments reflect the tracking store honestly: schema present, zero
   recorded runs — consistent with findings that real forecasting training
   never materialized in this snapshot.
4. Forecast metrics remain those of the released evaluation artifact; the
   API serves them verbatim and does not recompute (by design).

## 13. Recommended Stage 2 work

Frontend dashboard already exists (Stages 2–4). If Stage 2 is re-run:
wire the Forecasting page to the new per-target endpoints, add an
Experiments lineage view consuming `/api/experiments`, adopt the formal
error contract, and point CI at `tests/product/`.

**PRODUCT STAGE 1 COMPLETE**
