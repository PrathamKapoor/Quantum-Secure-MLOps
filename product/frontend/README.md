# Guardrailed Agentic MLOps — Frontend Dashboard

Productization layer (Stages 2–3): a professional, read-only operator console
over the locked research pipeline for **Guardrailed Agentic MLOps for
Self-Adaptive Energy Forecasting in Renewable-Integrated Smart Grids**.

The dashboard presents the system as an industrial MLOps platform: system
health, locked forecasting evaluation, model registry state, drift monitoring,
a governance audit timeline, a bounded agent assistant with evidence
traceability, scripted demo scenarios, and the research report library.
It performs **no write operations** against the research system.

## Tech stack

| Concern      | Choice                                        |
| ------------ | --------------------------------------------- |
| Framework    | React 19 + TypeScript + Vite                  |
| Routing      | React Router                                  |
| Charts       | Recharts (interactive actual-vs-predicted)    |
| Styling      | Tailwind CSS v4 (`@tailwindcss/vite` plugin)  |
| HTTP         | Axios (typed service layer)                   |
| Tests        | Vitest + React Testing Library + jsdom        |

## Setup

```bash
cd product/frontend
npm install
```

## Running

```bash
# 1. Start the backend API (from project root)
uvicorn product.backend_api.app.main:app --port 8000

# 2. Start the dashboard dev server
npm run dev          # http://localhost:5173
```

Production build & preview:

```bash
npm run build        # outputs dist/
npm run preview
```

## API configuration

The service layer reads the backend base URL from `VITE_API_BASE_URL`,
defaulting to `http://localhost:8000` (create `.env.local` to override).

Consumed endpoints — all read-only except the agent explanation POST:

| Function                 | Method | Endpoint                    |
| ------------------------ | ------ | --------------------------- |
| `api.fetchHealth`        | GET    | `/health`                   |
| `api.fetchForecastStatus`| GET    | `/api/forecast/status`      |
| `api.fetchPredictions`   | GET    | `/api/forecast/predictions` |
| `api.fetchModels`        | GET    | `/api/models`               |
| `api.fetchDriftEvents`   | GET    | `/api/drift/events`         |
| `api.fetchGovernanceEvents` | GET | `/api/governance/events`    |
| `api.explain`            | POST   | `/api/agents/explain`       |
| `api.fetchReports`       | GET    | `/api/reports`              |

Report view/download resolves through `GET /api/reports/file?path=…`
(whitelist-restricted on the backend with traversal protection).

## Architecture

```
src/
├── components/     # Sidebar, UI primitives, chat components, context panel,
│                   # expandable EvidenceList, ErrorBoundary
├── pages/          # Overview / Forecasting / Models / Drift / Governance /
│                   # AgentAssistant / DemoMode / Reports
├── services/       # api.ts (typed Axios client), demoScenarios.ts (scripts)
├── hooks/          # useApi — shared loading/error/data hook
├── types/          # API response interfaces (incl. agent response contract)
├── tests/          # Vitest suites
└── assets/
```

Data flow: `page → useApi hook → services/api.ts → FastAPI backend →
research system (read-only)`.

### Pages

1. **Overview** — executive cards: system status, forecast targets (Load /
   Wind / PV), model health, governance counters incl. blocked actions,
   bounded agent status.
2. **Forecasting** — per-target interactive actual-vs-predicted charts from
   the locked final evaluation; client-computed MAE / RMSE / sMAPE; horizon H24.
3. **Models** — read-only registry table. No promote/retrain/rollback controls.
4. **Drift Monitoring** — severity-counted timeline and event cards.
5. **Governance** — operator audit timeline: clock time, event type badge
   (`MODEL_PROMOTION_BLOCKED`, `RETRAINING_APPROVED`, `ROLLBACK_COMPLETED`, …),
   actor, target, reason, ledger evidence reference; type filter chips.
6. **Agent Assistant** — bounded decision-support console (see below).
7. **Demo Mode** — six scripted walkthroughs (see below).
8. **Reports** — grouped phase reports, final evaluation artifacts, research
   package, with View / Download.

## Agent Assistant architecture

Two-column operator layout:

- **Main area** — conversation transcript. Each agent turn renders as either:
  - *Explanation*: ANSWER text, expandable EVIDENCE list (ledger references
    with actor/packet-id/digest details), RULE chip and SOURCE chip
    (e.g. `VERIFICATION_QUARANTINE`, `REGISTERED_REFERENCE`), plus a
    human-review flag and a "Request human review" action.
  - *Blocked action* (`kind: "blocked_action"`): a red **ACTION BLOCKED**
    card showing Reason, Authority ("Deterministic governance engine") and
    Recommended next step ("Request human review"). Never simulated success;
    no executable controls.
- **Context panel** — agent mode badge (**BOUNDED DECISION SUPPORT**), allowed
  capabilities (✓ explain / summarize / investigate / retrieve evidence /
  request review / generate reports) visually separated from restricted
  actions (✕ promote / roll back / retrain / change features / change policy /
  access final test). Restricted entries are plain list items — no buttons or
  links are ever attached to them.

Backend contract (`POST /api/agents/explain`) classifies protected-action
requests imperatively (only *requests*, not questions about past decisions)
and refuses them; all other answers are grounded in real evidence-ledger
records via read-only queries.

### Human review

"Request human review" records the request in-session and displays it under
**Human review requests**, explicitly labeled: *"recorded locally — no
lifecycle action executed."* No review endpoint is invented at the backend;
when one exists it can be wired into `requestReview` without UI changes.

### Evidence traceability

Every explanation carries:

```
ANSWER     grounded natural-language summary
EVIDENCE   expandable list of registered references
           [1b76e436aafb] QUARANTINE — verify model demo-model v3
             actor / packet_id / digest / ledger_seq
RULE       deterministic rule that produced the outcome
SOURCE     REGISTERED_REFERENCE | POLICY_BOUNDARY | SYSTEM
```

Empty evidence is rendered honestly (`No ledger evidence matched this
question.`); malformed responses render a dedicated alert; nothing crashes
the dashboard (top-level ErrorBoundary).

## Demo mode

Six controlled scenarios (`src/services/demoScenarios.ts`), each sending real
questions to the live agent endpoint — no fabricated metrics:

| Code | Scenario | Outcome shown |
| --- | --- | --- |
| DEMO 01 | Forecast degradation → drift investigation | Honest drift-evidence state from the ledger |
| DEMO 02 | Drift → retraining explanation | Real supervised-adaptation packets |
| DEMO 03 | Challenger → promotion rejection | Real QUARANTINE verification packet |
| DEMO 04 | Rollback decision explanation | ROLLBACK packet + ROLLED_BACK transition |
| DEMO 05 | Unsafe promotion request → blocked | ACTION BLOCKED refusal |
| DEMO 06 | Final-test retrieval request → blocked | ACTION BLOCKED refusal |

Scenarios can be launched from the Demo Mode page or jumped into directly
from the Agent Assistant sidebar card.

## Safety boundary

- The dashboard issues only GET requests plus the agent-explanation POST.
- The agent surface exposes no lifecycle mutations (guarded by a regression
  test asserting no promote/rollback/retrain/deploy functions exist).
- Protected-action phrasing is refused with authority attribution; explanatory
  questions about past decisions remain answerable.
- The final test set is sealed: any retrieval request is refused.
- The research pipeline stays locked; all displayed data derives from its
  immutable artifacts and tamper-evident ledger.

## Testing

```bash
npm test
```

Suites (42 tests): API service layer + error abstraction, navigation & registry
read-only checks (incl. registry roles), overview rendering & system story,
agent console behavior (rendering, evidence display/expansion, three blocked
flows, governance-boundary phrasing, human-review flow, friendly API-failure
handling, malformed response, restricted-actions non-executability), demo
scenario loading/running/reset, audit-timeline rendering with plain-language
decision blocks & filtering.

## Hardening notes (Stage 4)

- **API error abstraction** — `getApiErrorMessage()` maps network failures,
  timeouts and HTTP statuses to fixed user-safe messages ("Backend service is
  currently unavailable.", …); raw socket codes/stacks never reach the UI.
  Integrated in `useApi` and both agent/demo call paths.
- **Registry roles** — read-only role classification (Challenger /
  Promotion-eligible / Promotion-rejected / Blocked / Production champion)
  derived from lifecycle state; footnote states challengers are not production
  models.
- **Governance decision cards** — each audit event shows DECISION / REASON /
  POLICY / EVIDENCE / ACTOR / TIMESTAMP with a plain-language headline and
  "Deterministic governance policy (frozen)" attribution.
- **System story strip** on Overview: Forecasting → Drift monitoring →
  Deterministic governance → Challenger evaluation → Bounded agent
  (explain only — no execution).
- **Demo controls** — Reset demo / Clear conversation buttons, explicit
  "DEMONSTRATION SCENARIO" label.
- **Blocked-action phrasing** — refusals are captioned "Blocked by governance
  boundary."; agent-decision phrasing ("AI decided…") is absent by design and
  regression-tested.
- **Lint** — oxlint clean (0 warnings) after refactoring `useApi` to an
  idiomatic fetcher-in-deps pattern.

## Accessibility & responsiveness

Semantic landmarks and buttons, keyboard-operable chat (Enter submits,
Shift+Enter newline), visible focus rings, ARIA roles/labels, live regions for
busy status, non-color-only indicators (✓/✕ glyphs, dot + badge text),
sufficient contrast. Layout prioritizes desktop/laptop and collapses gracefully
to tablet widths.
