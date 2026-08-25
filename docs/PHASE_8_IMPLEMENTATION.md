# Phase 8 Implementation: Advanced Drift Intelligence

> Specification: architecture document PART 14 §14.3 (PHASE 8 / Advanced Drift
> Intelligence), PART 21 STAGE 8; alert semantics reuse Phase-7 conventions.

## Objective

Attribute drift to individual features, build rolling performance baselines
from existing telemetry, produce deterministic drift interpretation, persist
everything through the single telemetry store, extend (not replace) the alert
framework, and expose the results via API.

## What already existed (reconstruction finding)

`DriftDetectionEngine` **already computed per-feature statistics** — PSI and
KS detectors emit one `DriftReport` per feature with scores, thresholds,
p-values, and severity (`ml/drift.py:81–153`) — but `get_summary()` collapsed
them into counts, and `health_check` persisted only that summary. Phase 8 is
therefore surfacing + interpretation, not new statistics.

## Implemented

1. **`build_feature_attribution(reports, reference_data, current_data,
   feature_names)`** (`ml/drift.py`): merges PSI/KS/prediction reports into
   one row per feature — detectors hit, worst severity, dominant score,
   detector statistics, baseline/current means computed from real arrays when
   supplied (else `UNAVAILABLE`, never fabricated), sample counts, rank by
   severity→score.
2. **`classify_drift(...)`** (`ml/drift.py`): deterministic interpretation →
   exactly one of `NO_DRIFT | ISOLATED_FEATURE_DRIFT | BROAD_FEATURE_DRIFT |
   PERFORMANCE_DEGRADATION | DRIFT_WITH_PERFORMANCE_DEGRADATION |
   INSUFFICIENT_HISTORY`. Broad = drifting features ≥ max(2, fraction × total).
3. **Telemetry persistence** (single store, no new files): new
   `record_feature_attribution` writes kind=`feature_drift` rows stamped with
   a shared `check_ts`; `feature_history` / `latest_feature_attribution`
   reconstruct any check.
4. **Rolling baselines**: `TelemetryCollector.rolling_baseline(metric,
   window, min_history)` compares recent-window mean vs prior mean from the
   same series (worse-direction auto-detected from metric name); returns
   sufficient/insufficient explicitly.
5. **Alert extensions** (backward-compatible kwargs on `evaluate`):
   `FEATURE_DRIFT_CRITICAL` (per-feature CRITICAL), `FEATURE_DRIFT_BROAD`
   (interpretation == broad), `SUSTAINED_PERFORMANCE_DEGRADATION` (rolling
   baseline degraded ≥15%). Existing levels untouched; healthy cycles quiet.
6. **Wiring**: `run_drift_check` embeds attribution+intelligence in its
   summary; `health_check` persists attribution, computes rolling baselines
   for mse/r2 from recorded telemetry, extends alerts, and returns
   `feature_attribution` / `rolling_baseline` / `drift_intelligence`.
7. **API**: `GET /drift/{model}/attribution`,
   `GET /performance/{model}/rolling?window=N`.

## Configuration

`MONITORING_ROLLING_WINDOW=10`, `MONITORING_MIN_HISTORY=3`,
`DRIFT_BROAD_FEATURE_FRACTION=0.5` (config.py; platform-wide, not forked).

## Verification

| Suite | Result |
|---|---|
| New `tests/test_phase8_drift_intelligence.py` | 18/18 |
| Full core suite | **239 passed** (221 prior + 18) |
| compileall | clean |
| demo.py | SUCCESS (chain OK) |

## Non-goals (explicit)

No LLM explanations, no external drift vendors, no second telemetry/alert
store, no archived-module resurrection, no Guardrailed changes.
