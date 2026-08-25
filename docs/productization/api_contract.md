# API Contract — Product Backend (IMPLEMENTED)

Status: **Stage 1 implemented and verified.** This document describes the
API as actually built and tested. It supersedes the earlier aspirational
design in this file (`/api/v1` prefix, JWT auth), which was never
implemented; see "Deviations from the original design" below.

Base URL: `http://localhost:8000` (configurable via frontend
`VITE_API_BASE_URL`).

## Design rules

1. The product API is an **adapter** over the locked research system.
   It never mutates research state; automated tests enforce this via
   artifact hashing (`tests/product/test_immutability.py`).
2. Lifecycle mutations (promote / rollback / retrain / policy change) are
   **not exposed as routes at all**. They remain inside the research-side
   governance engine.
3. The single POST endpoint is the bounded agent explainer: it reads,
   explains, and refuses unsafe requests — it cannot execute anything.
4. Every endpoint below is labeled:
   - **READ-ONLY** — no state change of any kind.
   - **BOUNDED-READ** — reads + refuses unsafe intent; no lifecycle effect.

## Authentication

None in Stage 1, by explicit decision ("do not over-engineer authentication
at this stage"). CORS is restricted to the dashboard origins via
`PRODUCT_CORS_ORIGINS`. Adding JWT later is an additive middleware change.

## Interactive documentation

`/docs`, `/redoc`, `/openapi.json` are enabled. No repository security
policy disables them today. Disable in deployment with
`PRODUCT_ENABLE_DOCS=false`.

## Endpoints

| Method | Route | Purpose | Classification |
|---|---|---|---|
| GET | `/health` | Liveness + research-lock status | READ-ONLY |
| GET | `/api/forecast/status` | Targets (load/wind/pv), horizon H24, lock flag | READ-ONLY |
| GET | `/api/forecast/predictions` | Frozen evaluation rows; `?target=LOAD\|WIND\|PV`, `?limit=N` | READ-ONLY |
| GET | `/api/forecast/predictions/{target}` | Per-target rows (+ summary fields) | READ-ONLY |
| GET | `/api/forecast/summary/{target}` | Count, model(s), MAE-from-artifact | READ-ONLY |
| GET | `/api/models` | Flattened registry view (target, model, feature set, fingerprint, state) | READ-ONLY |
| GET | `/api/models/{name}/versions` | All versions of a model | READ-ONLY |
| GET | `/api/models/{name}/versions/{vid}` | Version detail incl. passport signature suite | READ-ONLY |
| GET | `/api/experiments` | MLflow experiments + run counts (read-only SQLite) | READ-ONLY |
| GET | `/api/experiments/{id}` | Experiment detail with runs/params/metrics/tags | READ-ONLY |
| GET | `/api/drift/events` | Drift timeline (empty honestly if none recorded) | READ-ONLY |
| GET | `/api/drift/events/{event_id}` | Single drift event by ledger-hash id | READ-ONLY |
| GET | `/api/governance/events` | Full audit timeline (decisions + transitions) | READ-ONLY |
| GET | `/api/governance/decisions` | Decision/packet records only | READ-ONLY |
| POST | `/api/agents/explain` | Bounded explanation; body `{"query": str(1..2000)}` | BOUNDED-READ |
| GET | `/api/reports` | Available reports by type | READ-ONLY |
| GET | `/api/reports/file?path=` | Whitelisted report download (traversal-guarded) | READ-ONLY |

### Agent safety contract

`POST /api/agents/explain` classifies protected-action requests
(promote / rollback / retrain / feature change / policy change /
final-test access). Such requests return:

```json
{
  "kind": "blocked_action",
  "reason": "...",
  "authority": "Deterministic governance engine",
  "recommended_next_step": "Request human review.",
  "requires_human_review": true
}
```

Refusals are returned — never executed — and explanatory questions about
past decisions remain answerable with real ledger evidence.

## Error behavior

- 404 with `{"detail": "..."}` for unknown targets/models/experiments/events.
- 422 for schema violations (e.g., missing/oversized agent query).
- 500 returns `{"detail": "Internal server error."}` — tracebacks are logged
  server-side only.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `PRODUCT_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed browser origins |
| `PRODUCT_ENABLE_DOCS` | `true` | Toggle interactive docs |

## Deviations from the original aspirational contract

1. No `/api/v1` version prefix — shipped contract (Stages 2–4 frontend)
   uses `/api/*`; renaming would break a working consumer for zero gain.
2. No JWT/auth layer in this stage, per Stage-1 instruction to avoid
   premature auth infrastructure.
3. Route names follow implemented reality (`/api/governance/events` etc.)
   rather than the draft's `/governance/audit`; capability coverage is equal.
