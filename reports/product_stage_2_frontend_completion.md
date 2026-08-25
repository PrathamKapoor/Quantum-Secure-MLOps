# Product Stage 2 — Frontend Dashboard Completion

Project: Guardrailed Agentic MLOps for Self-Adaptive Energy Forecasting in
Renewable-Integrated Smart Grids

## Scope delivered

A production-grade React + Vite + TypeScript dashboard in `product/frontend/`
presenting the locked research system as an industrial MLOps platform. The
dashboard is strictly read-only: the only mutating call it can issue is the
agent explanation request, which itself performs no system changes.

## Pages created (7)

| Page | File | Contents |
| --- | --- | --- |
| Overview | `src/pages/Overview.tsx` | System status (API + locked pipeline), forecast targets (Load/Wind/PV), model health counters, governance counters incl. blocked actions, bounded agent status card |
| Forecasting | `src/pages/Forecasting.tsx` | Per-target interactive actual-vs-predicted Recharts line charts from `/api/forecast/predictions`, client-computed MAE / RMSE / sMAPE metric tiles, horizon H24 header, target tabs, series downsampling for responsiveness |
| Model Registry | `src/pages/Models.tsx` | Read-only table: Target, Model, Feature Set, Fingerprint, Lifecycle State. Explicit "read-only" notice; no promote/retrain/rollback controls exist anywhere in the component tree |
| Drift Monitoring | `src/pages/DriftMonitoring.tsx` | Severity summary tiles (HIGH/MEDIUM/LOW), vertical timeline with severity-coded dots and event cards (severity badge, target, timestamp, drift type, score, evidence reference) |
| Governance | `src/pages/Governance.tsx` | Audit timeline of ledger events (`MODEL_PROMOTION_BLOCKED`, approvals, completions) with decision classification badges, policy-decision summaries, actor, evidence reference and timestamp |
| Agent Assistant | `src/pages/AgentAssistant.tsx` | Chat-style Q&A. Persistent safety banner: "Agents provide explanation only … cannot approve … or change any model." Responses render Explanation / Evidence / Governance rule sections with human-review flag |
| Reports | `src/pages/Reports.tsx` | Reports grouped by type (phase reports, final evaluation, research tables, research package) with View and Download links |

## Components

- `components/Sidebar.tsx` — 7-item navigation, active-route highlighting,
  persistent "Research pipeline locked" indicator.
- `components/ui.tsx` — design-system primitives: `Card`, `PageHeader`,
  `MetricTile`, `LoadingState`, `ErrorState`, `EmptyState`, `SeverityBadge`.
- `components/AgentChat.tsx` — chat primitives (`AgentSafetyBanner`,
  `ChatTranscript`, `SuggestionChips`, `useAgentChat`) enforcing the
  explanation-only rendering rules.
- `hooks/useApi.ts` — shared async data hook (loading/error/cancellation).

## API integration

Typed service layer `src/services/api.ts` (single Axios client,
`VITE_API_BASE_URL` configurable) covering every required endpoint:
`/health`, `/api/forecast/status`, `/api/models`, `/api/drift/events`,
`/api/governance/events`, `/api/agents/explain` (POST), `/api/reports`, plus
`/api/forecast/predictions` for chart data.

One additive backend endpoint was added to support View/Download:
`GET /api/reports/file?path=…` (`product/backend_api/app/routers/reports.py`)
— serves files only from whitelisted project roots (`reports/`, `artifacts/`,
`docs/`) with traversal protection (verified: 200 valid, 400 traversal,
403 outside whitelist). Report paths are now returned project-relative POSIX
so they are stable regardless of server working directory.

## Tests

Vitest + React Testing Library + jsdom. **20 tests, all passing** across 4 suites:

- `App.test.tsx` (3): all seven nav sections present; navigation to Models
  renders registry with read-only notice and asserts promote/retrain/rollback
  buttons do not exist; sidebar lock indicator visible.
- `Overview.test.tsx` (4): rendering of health/targets/model-health/governance/
  bounded-agent cards against mocked API.
- `AgentSafety.test.tsx` (4): explanation-only banner always shown; "AI approved"
  / "AI changed" language absent; question POSTed correctly; transcript labels
  responses as bounded-mode explanations only.
- `api.test.ts` (9): correct URL/method per endpoint, explain POST body,
  base URL default, no mutation-style helpers exposed.

Validation commands run:

- `npm run build` — clean production build (tsc + vite).
- `npm test` — 20/20 passed, 0 failed.

## Cross-cutting validation

- Research test suite unchanged: **97 passed** (`tests/` excluding the
  pre-existing `test_phase2_platform.py` infrastructure failures documented at
  Stage 1).
- Backend API suite: **6 passed** (health, forecast, models, drift, governance,
  agents tests still green after the additive report-file endpoint).
- No file under `qsmlops/`, `mlops/`, `artifacts/`, or other research modules
  was modified by this stage.
- Stray npm artifacts accidentally created at the repository root during an
  earlier aborted attempt (root `package.json`, `node_modules`,
  `postcss.config.js`, `tailwind.config.js`) were removed; frontend resolves
  exclusively through `product/frontend/package.json`.

## Limitations

1. Forecast accuracy metrics are computed client-side from the served
   prediction rows rather than read from a dedicated metrics endpoint; values
   match the locked evaluation data but are recomputed per request.
2. Governance event details render the most useful fields (decision class,
   actor, evidence ref); full raw packets remain accessible via reports.
3. Agent explanations depend on the current placeholder backend
   implementation; the UI contract is final but richer grounded answers await
   the Stage 3 assistant work.
4. No authentication/authorization layer yet on either API or dashboard;
   recommended before any shared deployment.
5. Data refreshes on navigation/mount only; no polling or WebSocket streaming.
6. Bundle exceeds 500 kB minified (Recharts + React); acceptable for an
   internal console, code-splitting deferred.

## Conclusion

Stage 2 delivers the complete dashboard surface over the existing API with the
guardrail contract enforced end to end: read-only data access, explicit agent
boundaries, and zero reachability into research-side mutations.

**PRODUCT STAGE 2 COMPLETE**
