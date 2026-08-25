"""Read-only access to the frozen final-evaluation forecast artifacts.

Serves rows exactly as recorded by the research pipeline (CSV), applying only
optional filters. Never recomputes metrics and never touches final-test data
beyond what the released evaluation artifact already contains.
"""
from __future__ import annotations

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]

VALID_TARGETS = ("LOAD", "WIND", "PV")
HORIZON = "H24"

_PREDICTION_PATHS = [
    PROJECT_ROOT / "artifacts" / "final_evaluation" / "final_predictions.csv",
    PROJECT_ROOT / "artifacts" / "final_release" / "final_results_tables" / "final_predictions.csv",
]


def _prediction_file() -> Path | None:
    for path in _PREDICTION_PATHS:
        if path.is_file():
            return path
    return None


def get_forecast_status() -> dict:
    return {
        "targets": [t.lower() for t in VALID_TARGETS],
        "horizon": HORIZON,
        "models_locked": True,
    }


def get_predictions(target: str | None = None, limit: int = 0) -> list[dict]:
    """Rows from the frozen predictions CSV, optionally filtered.

    target: case-insensitive LOAD/WIND/PV filter (invalid values yield []).
    limit: optional cap on returned rows (0 = no cap).
    """
    path = _prediction_file()
    if path is None:
        return []
    wanted = target.upper() if target else None
    if wanted is not None and wanted not in VALID_TARGETS:
        return []

    rows: list[dict] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if wanted is not None and row.get("target", "").upper() != wanted:
                continue
            rows.append(row)
            if limit and len(rows) >= limit:
                break
    return rows


def get_target_summary(target: str) -> dict | None:
    """Aggregate metadata for one target, derived read-only from the CSV."""
    if target not in VALID_TARGETS:
        return None
    path = _prediction_file()
    if path is None:
        return {k: None for k in ("target", "horizon", "model", "count")}
    count = 0
    models: set[str] = set()
    abs_err_sum = 0.0
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("target", "").upper() != target:
                continue
            count += 1
            models.add(row.get("model", ""))
            try:
                abs_err_sum += float(row.get("absolute_error", 0) or 0)
            except ValueError:
                pass
    mae = round(abs_err_sum / count, 6) if count else None
    model_label = ", ".join(sorted(m for m in models if m)) or None
    return {
        "target": target.lower(),
        "horizon": HORIZON,
        "model": model_label,
        "count": count,
        "mae_from_absolute_errors": mae,
    }
