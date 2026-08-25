# Frontend Requirements

## Overview
This document outlines the requirements for the frontend dashboard that will interact with the Guardrailed Agentic MLOps API. The frontend must adhere to the security boundary: it cannot directly execute model promotion, rollback, retraining, policy changes, or feature changes. All such actions must be requested via the API, which enforces governance checks.

## Technology Stack
- Framework: React with Vite (or Next.js) - choice to be made based on team expertise and project needs.
- Language: TypeScript for type safety.
- State Management: Redux Toolkit or React Query (for server state) and Context API or Zustand (for client state).
- Styling: Tailwind CSS or Material-UI (MUI) for rapid development and responsive design.
- Visualization: Plotly.js (via react-plotly.js) and Recharts for charts; D3.js for custom visualizations if needed.
- HTTP Client: Axios or Fetch API with interceptors for auth and error handling.
- Testing: Jest and React Testing Library for unit tests; Cypress for end-to-end tests.
- Code Quality: ESLint, Prettier, and TypeScript strict mode.

## Required Screens

### 1. Executive Dashboard
**Purpose:** High-level grid intelligence for operators and managers.

**Components:**
- **System Status Overview:** 
  - Overall system health (healthy/degraded/unhealthy) based on governance decisions and agent findings.
  - Active alerts and warnings count.
  - Last system update timestamp.
- **Forecasting Status:**
  - Current forecast horizon (H24/H1) for each target (LOAD, WIND, PV).
  - Data freshness (time since last actual values update).
  - Model status (deployed version, age).
- **Renewable Integration Status:**
  - Percentage of load met by wind and PV (if actuals available).
  - Forecast vs actual for renewable generation (wind and PV).
- **Drift State Summary:**
  - Current drift severity (worst across all targets).
  - Number of new drift reports in the last 24 hours.
- **System Reliability Indicators:**
  - Uptime percentage (last 30 days).
  - Mean time between interventions (MTBI).
  - Number of governance actions in the last week (retrains, rollbacks, quarantines).

**Data Requirements:**
- Calls to `/governance/decisions`, `/drift/summary`, `/forecasting/errors/{target}`, `/models`, `/governance/audit`.

### 2. Forecast Dashboard
**Purpose:** Detailed view of forecasting performance and actuals vs predictions.

**Components (per target: LOAD, WIND, PV):**
- **Actual vs Prediction Plot:**
  - Interactive time series chart showing actual values and predictions for the selected horizon.
  - Ability to zoom and pan.
  - Toggle to show/hide confidence intervals.
  - Toggle between actuals and predictions for different horizons.
- **Error Metrics Panel:**
  - Display MAE, RMSE, sMAPE, nMAE, nRMSE for the selected time range.
  - Comparison to baseline (if available via API, else show N/A).
- **Historical Trends:**
  - Chart showing error metrics over time (e.g., daily MAE).
  - Ability to select different metrics to view.
- **Forecast Horizon Selector:**
  - Dropdown to switch between H24 and H1 (and other horizons if available).
- **Data Table:**
  - Tabular view of timestamps, actuals, predictions, errors (optional, can be collapsed).

**Data Requirements:**
- Calls to `/forecasting/predictions/{target}`, `/forecasting/actuals/{target}`, `/forecasting/errors/{target}` with appropriate time range parameters.

### 3. Model Registry Dashboard
**Purpose:** View-only exploration of model lineage and metadata.

**Components:**
- **Model List Table:**
  - Columns: Model Name, Type, Feature Set, Latest Version, Status, Last Updated.
  - Search and filter by model name, type, status.
  - Clicking a row opens the model version history.
- **Model Version History:**
  - For selected model, list of versions with:
    - Version Number
    - Status (REGISTERED, VERIFIED, APPROVED, DEPLOYED, QUARANTINED, ROLLED_BACK)
    - Artifact Digest (truncated)
    - Created At
    - Creator (producer/verifier)
    - Key Metrics (MAE, RMSE)
  - Clicking a version opens the lineage view.
- **Lineage View:**
  - Display of the model passport and QML-BOM information:
    - Model details (name, version, type, feature set)
    - Dataset digest and origin
    - Preprocessing steps (if any)
    - Training details (framework, hyperparameters)
    - Artifact digest and size
    - Passport details (signature validity, signer, timestamp)
    - BOM entries (dataset, code, artifact, framework)
  - Visual representation of the lineage (optional, using a simple graph).
- **Audit Trail for Model:**
  - List of governance decisions related to this model (from `/governance/decisions?model_name=...`).

**Data Requirements:**
- Calls to `/models`, `/models/{model_name}/versions`, `/models/{model_name}/versions/{version_id}/lineage`, `/governance/decisions`.

**Note:** All actions are view-only. No buttons for promotion, rollback, etc.

### 4. Drift Monitoring Dashboard
**Purpose:** Monitor and investigate drift events.

**Components:**
- **Drift Events Timeline:**
  - Interactive timeline (e.g., using a vis.js timeline or a simple scatter plot) showing drift events over time.
  - X-axis: time, Y-axis: target or drift type.
  - Color-coded by severity (LOW: green, MEDIUM: yellow, HIGH: orange, CRITICAL: red).
  - Hover tooltip shows details (score, affected features, description).
  - Clicking an event opens the drift detail view.
- **Drift Summary Panel:**
  - Total drift events in selected time range.
  - Breakdown by severity (pie chart or bar chart).
  - Breakdown by target (pie chart or bar chart).
  - Breakdown by drift type (if available).
- **Drift Detail View (modal or side panel):**
  - All fields from the drift report: target, timestamp, drift_type, severity, score, threshold, affected_features, description.
  - Additional context: 
    - Link to the model version that was active at the time.
    - Actual vs prediction chart for the target around the event time.
    - Feature distribution comparison (if available from research system).
- **Filters:**
  - Time range picker (last 24h, last 7d, last 30d, custom).
  - Target filter (LOAD, WIND, PV, all).
  - Severity filter (multi-select).
  - Drift type filter (if available).

**Data Requirements:**
- Calls to `/drift/reports`, `/drift/summary`, `/models/{model_name}/versions/{version_id}` (for context), `/forecasting/predictions/{target}` and `/forecasting/actuals/{target}` for charting.

### 5. Governance Dashboard
**Purpose:** Monitor governance decisions, policy checks, and system audits.

**Components:**
- **Decisions Timeline:**
  - Similar to drift timeline but for governance decisions.
  - X-axis: time, Y-axis: decision type (ACCEPT, RETRAIN, QUARANTINE, etc.) or model name.
  - Color-coded by decision type or risk score.
  - Hover tooltip shows model, version, reasoning, risk score.
  - Clicking opens the decision detail view.
- **Decisions Summary Panel:**
  - Total decisions in selected time range.
  - Breakdown by decision type (pie chart).
  - Breakdown by model (bar chart).
  - Average risk score.
  - Count of actions taken (RETRAIN, QUARANTINE, etc.).
- **Policy Checks Panel:**
  - List of active governance policies with description and priority.
  - Indication of which policies have been triggered recently.
- **Audit Trail Viewer:**
  - Paginated list of evidence ledger entries.
  - Filter by entry type (serving_load, inference, verification_packet, etc.).
  - Search by model name, version ID, or custom text.
  - Export to CSV (optional).
- **Decision Detail View (modal or side panel):**
  - All fields from the governance decision: decision_id, model_name, version_id, decision, timestamp, reasoning, risk_score, policy_rules_triggered.
  - Agent findings related to the decision (if available via `/agents/explain/{decision_id}`).
  - Links to the model version lineage and artifact details.

**Data Requirements:**
- Calls to `/governance/decisions`, `/governance/policies`, `/governance/audit`, `/agents/explain/{decision_id}`.

### 6. Agent Assistant Interface
**Purpose:** Provide explanations for system decisions and model behavior.

**Components:**
- **Explanation Request Form:**
  - Dropdown to select a recent governance decision (or input a decision ID).
  - Button to "Get Explanation".
- **Explanation Display:**
  - Summary explanation in plain language.
  - Agent findings section:
    - For each agent that contributed: agent name, finding name, passed status, severity, description, confidence.
  - Governance reasoning section:
    - Which policy rules were triggered and why.
  - Confidence score for the explanation.
  - Suggested actions (if any, but note: the agent cannot suggest actions that bypass governance; it can only suggest actions that are within policy, like "collect more data" or "wait for next evaluation").
- **Alternative: Chat-like Interface:**
  - User can ask questions like:
    - "Why was model LOAD version 1.0.0 not promoted?"
    - "What caused the drift alert for WIND at 2026-08-23T00:00:00Z?"
    - "Show me the evidence for the last retraining decision."
  - The assistant responds with evidence-based answers, citing agent findings, governance rules, and data.

**Data Requirements:**
- Calls to `/agents/explain/{decision_id}`, `/agents/findings`, `/governance/decisions`, `/models/{model_name}/versions/{version_id}/lineage`.

## Non-Functional Requirements

### Performance
- Page load time: < 3 seconds for initial load (cached).
- Dashboard updates: < 1 second for data refresh (via WebSocket or polling interval of 5-10 seconds).
- Chart rendering: Smooth interaction with up to 10,000 data points (using virtualization or downsampling for large datasets).

### Security
- All communication with API over HTTPS.
- Authentication tokens stored securely (in memory or secure HTTP-only cookies).
- No sensitive data (like model artifacts or keys) exposed in the frontend.
- Content Security Policy (CSP) to prevent XSS.

### Accessibility
- WCAG 2.1 AA compliance.
- Keyboard navigation support.
- ARIA labels for interactive elements.
- Sufficient color contrast.

### Responsiveness
- Mobile-first design: dashboards should be usable on tablets and mobile devices (though some complex views may be better suited for desktop).
- Collapsible sidebars and responsive grids.

### Internationalization
- Support for English (en-US) as primary; structure in place for future i18n.

## Deployment
- Built as static assets (HTML, CSS, JS) served by a web server (NGINX, Apache, or the FastAPI server itself via static file mounting).
- Environment-specific configuration (API URL) via environment variables at build time or runtime.

## Testing
- Unit tests for components and hooks (Jest + React Testing Library).
- End-to-end tests for critical user flows (Cypress).
- Visual regression testing (optional, with Storybook and Chromatic).
- Linting and formatting enforced via pre-commit hooks.

## Future Extensibility
- The frontend should be designed to easily add new panels or dashboards as new research capabilities become available (e.g., adding a new agent type or a new kind of drift detection).
- Modular architecture: each dashboard section is a self-contained module that can be enabled/disabled via feature flags.

## Restrictions (Reiterated)
The frontend MUST NOT:
- Directly call any research system internal functions or access internal databases.
- Attempt to modify models, datasets, features, or evaluation results.
- Execute lifecycle operations (train, promote, rollback, retire) without going through the API and governance engine.
- Expose or leak sensitive information such as model artifact bytes, cryptographic keys, or raw evidence ledger entries with sensitive data.
- Bypass authentication or authorization checks.