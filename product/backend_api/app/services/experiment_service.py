"""Read-only MLflow tracking-store adapter.

Answers product-relevant lineage questions (what experiments exist, which
runs produced them, what params/metrics were recorded) directly from the
MLflow SQLite store WITHOUT importing or executing MLflow, and WITHOUT ever
writing to it. The store is opened read-only; an absent or empty store is
reported honestly rather than fabricated.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

# Project root: product/backend_api/app/services/ -> up 4 levels.
PROJECT_ROOT = Path(__file__).resolve().parents[4]
MLFLOW_DB = PROJECT_ROOT / "mlflow.db"


def _connect_ro() -> sqlite3.Connection | None:
    if not MLFLOW_DB.is_file():
        return None
    uri = f"file:{MLFLOW_DB.as_posix()}?mode=ro"
    try:
        return sqlite3.connect(uri, uri=True)
    except sqlite3.Error:
        return None


def list_experiments() -> dict:
    conn = _connect_ro()
    if conn is None:
        return {
            "available": False,
            "experiments": [],
            "note": "MLflow tracking store not present.",
        }
    try:
        experiments = [
            {
                "experiment_id": str(row[0]),
                "name": row[1],
                "lifecycle_stage": row[2],
            }
            for row in conn.execute(
                "SELECT experiment_id, name, lifecycle_stage FROM experiments "
                "ORDER BY experiment_id"
            ).fetchall()
        ]
        counts = dict(
            conn.execute(
                "SELECT experiment_id, COUNT(*) FROM runs GROUP BY experiment_id"
            ).fetchall()
        )
        for exp in experiments:
            exp["run_count"] = int(counts.get(int(exp["experiment_id"]), 0))
        return {
            "available": True,
            "experiments": experiments,
            "note": (
                "Tracking store contains no recorded runs yet."
                if sum(exp["run_count"] for exp in experiments) == 0
                else ""
            ),
        }
    finally:
        conn.close()


def _runs_for(conn: sqlite3.Connection, experiment_id: int) -> list[dict]:
    runs: list[dict] = []
    rows = conn.execute(
        "SELECT run_uuid, name, status, start_time, end_time FROM runs "
        "WHERE experiment_id=? ORDER BY start_time",
        (experiment_id,),
    ).fetchall()
    for run_uuid, name, status, start_time, end_time in rows:
        params = {
            k: v
            for k, v in conn.execute(
                "SELECT key, value FROM params WHERE run_uuid=?", (run_uuid,)
            ).fetchall()
        }
        metrics = {
            k: v
            for k, v in conn.execute(
                "SELECT key, value FROM latest_metrics WHERE run_uuid=?",
                (run_uuid,),
            ).fetchall()
        }
        tags = {
            k: v
            for k, v in conn.execute(
                "SELECT key, value FROM tags WHERE run_uuid=?", (run_uuid,)
            ).fetchall()
        }
        # `mlflow.log-model` style links live in logged_models; surface the
        # artifact URI tag when present so lineage to a registry stays visible.
        runs.append(
            {
                "run_id": run_uuid,
                "name": name,
                "status": status,
                "start_time": start_time,
                "end_time": end_time,
                "params": params,
                "metrics": metrics,
                "tags": tags,
            }
        )
    return runs


def get_experiment(experiment_id: int) -> dict | None:
    conn = _connect_ro()
    if conn is None:
        return None
    try:
        row = conn.execute(
            "SELECT experiment_id, name, lifecycle_stage FROM experiments "
            "WHERE experiment_id=?",
            (experiment_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "available": True,
            "experiment": {
                "experiment_id": str(row[0]),
                "name": row[1],
                "lifecycle_stage": row[2],
            },
            "runs": _runs_for(conn, int(row[0])),
        }
    finally:
        conn.close()
