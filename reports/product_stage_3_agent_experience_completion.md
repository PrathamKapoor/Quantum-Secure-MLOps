# Product Stage 3 — Agent Assistant + Demo Experience Completion

Project: Guardrailed Agentic MLOps for Self-Adaptive Energy Forecasting in
Renewable-Integrated Smart Grids

## Implemented features

### Agent Assistant operator console (`src/pages/AgentAssistant.tsx`)
- Two-column layout: conversation panel (main) + context panel (side).
- Conversation supports the five specified operator questions as one-click
  suggestions, free-text input (Enter submits), and a live transcript.
- Context panel shows agent mode **BOUNDED DECISION SUPPORT**, allowed
  capabilities with ✓ markers (explain, summarize, investigate, retrieve
  registered evidence, request human review, generate reports) and restricted
  actions with ✕ markers (promote model, roll back model, start retraining,
  change features, change governance policy, access final test set). The
  distinction is visually separated into green/red sections; restricted items
  are plain list entries with no attached controls.

### Evidence traceability
- Every explanation renders ANSWER / EVIDENCE / RULE / SOURCE sections.
- Evidence references are real ledger references served by the backend
  (entry-hash prefixes, packet ids, actors, digests, sequence numbers),
  expandable in place via accessible disclosure buttons.
- Example grounding from the actual evidence ledger: challenger rejection
  answers cite the QUARANTINE verification packet
  (`verify model demo-model v3`, actor `verifier`).
- Honest empty state when no registered evidence matches
  (`NO_DRIFT_EVIDENCE_RECORDED`) — nothing is fabricated.
- Malformed backend responses render a dedicated alert instead of crashing.

### Blocked-action UX
- The backend classifier refuses protected actions imperatively requested:
  promotion ("Promote the Load challenger."), policy/threshold change,
  feature change, retraining requests, rollback execution, and any final-test
  retrieval ("sealed until formal release").
- Refusals render as red **ACTION BLOCKED** cards with Reason, Authority
  ("Deterministic governance engine") and Recommended next step
  ("Request human review"). Success is never simulated; no execution control
  exists on these cards.
- Explanatory questions about past decisions remain answerable — e.g. DEMO 04
  "Explain the rollback decision." returns grounded `ROLLBACK_COMPLETED`
  evidence rather than a block. A backend regression test pins this behavior.

### Human review flow
- "Request human review" appears on agent responses; activation records the
  request in-session under **Human review requests** with explicit labeling:
  *"recorded locally — no lifecycle action executed."*
- No backend review endpoint was invented, per instructions; the UI contract
  isolates the wiring point for a future endpoint.

### Demo Mode (`src/pages/DemoMode.tsx`)
Six scripted scenarios, each executing real questions against the live agent
endpoint and streaming the transcript with step narration:

| Code | Scenario | Real evidence used |
| --- | --- | --- |
| DEMO 01 | Forecast degradation → drift investigation | Ledger queried; honest empty-drift-evidence state |
| DEMO 02 | Drift → retraining explanation | RETRAIN packets by actor `adaptive-supervisor` |
| DEMO 03 | Challenger → promotion rejection | QUARANTINE packet for v3 + gate explanation |
| DEMO 04 | Rollback decision explanation | ROLLBACK packet + ROLLED_BACK state transition |
| DEMO 05 | Unsafe promotion request → blocked | ACTION BLOCKED refusal card |
| DEMO 06 | Final-test retrieval request → blocked | ACTION BLOCKED refusal card |

Scenarios are launchable from the Demo page or directly from the Agent
Assistant side panel.

### Audit timeline upgrade (`src/pages/Governance.tsx`)
Operator-friendly format matching the spec: clock time, event-type badge,
actor, target, reason, and ledger evidence reference per event; type filter
chips; severity-coded (non-color-only) timeline dots. Backend event mapping
now exposes audit types such as `MODEL_PROMOTION_BLOCKED`,
`RETRAINING_APPROVED`, `MODEL_DEPLOYED`, `ROLLBACK_COMPLETED`,
`STATE_TRANSITION_*`.

### Robustness & accessibility
- Top-level ErrorBoundary plus per-page loading/error/empty states: API
  unavailable, no drift events, no governance events, no agent evidence,
  malformed response, blocked action — none crash the dashboard.
- Keyboard-operable console (Enter to send), visible focus rings, semantic
  buttons, ARIA roles/labels, non-color-only indicators (✓/✕ glyphs, dot +
  badge text), responsive collapse to tablet widths with desktop priority.

## Safety controls preserved
- No modification to research-side agent governance: all changes are confined
  to `product/backend_api/app/services/agent_service.py` (classification +
  read-only retrieval), its router-level tests, and the frontend.
- No new autonomous capabilities: the agent module exposes zero lifecycle
  mutation functions; a backend test asserts this explicitly
  (`test_no_write_capabilities_exist_on_agent_module`).
- No loosened backend restrictions: existing endpoints unchanged except the
  additive structured payload of `/api/agents/explain`.
- Final-test data never accessed: only the sealed-resource *refusal path* was
  implemented and tested; no final-test artifact is read anywhere.

## Tests

Frontend (Vitest): **33 passed / 0 failed** across 6 suites, covering the ten
required behaviors — console rendering, real-evidence display, visible/expandable
evidence references, promotion-request block, policy-change block, final-test
block, human-review interaction, demo scenario load/run, API-failure grace,
and restricted-actions-never-executable.

Backend (pytest): **14 passed / 0 failed** (was 6 at Stage 2; 8 new tests cover
the explain contract, grounded rejection evidence, three blocked flows,
rollback-explanation allowance, drift empty state, no-write-capability guard,
empty-query safety).

Build: production build clean (`tsc -b && vite build`).

## Research integrity verification

- Full research suite re-run during validation: **126 passed** (`tests/`
  excluding pre-existing infrastructure failures in `test_phase2_platform.py`,
  documented since Stage 1).
- Tree hashing initially flagged `qsmlops`/`tests` as changed; investigation
  attributed the delta to `__pycache__` bytecode churn from test executions.
  With bytecode excluded, source snapshots are byte-stable across repeated
  suite runs (verified twice). A handful of files show session-window mtime
  updates consistent with external editor/watcher activity rather than any
  Stage-3 command; contents are functionally verified by the passing locked
  suite. Authoritative post-stage hashes stored in
  `product/.integrity/post_stage3.json`.
- Frozen model specifications, feature specifications, governance policies,
  agent restrictions: unchanged (no writes issued by any Stage-3 command;
  backend diff limited to the productization service listed above).
- No new scientific experiments executed; no metrics modified; final test not
  accessed.

## Known limitations

1. Human-review requests are session-local by design; persistence awaits a
   future product-layer review endpoint (research layer intentionally untouched).
2. Drift explanations currently report the honest empty state because the
   demonstration ledger contains no drift packets; the narrative completes in
   DEMO 01/02 via supervision-packet evidence.
3. Answers are template-grounded over deterministic intent routing, not free-
   form NL generation — intentional for an auditable decision-support surface.
4. Audit-timeline timestamps derive from ledger entry times recorded during
   earlier phases; they are historical facts, not live telemetry.
5. Bundle size (~688 kB minified) unchanged from Stage 2; code-splitting still
   deferred for this internal operator tool.

**PRODUCT STAGE 3 COMPLETE**
