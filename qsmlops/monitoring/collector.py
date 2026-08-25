"""Telemetry collection for the monitoring foundation (Phase 7).

A minimal, dependency-free time-series store: newline-delimited JSON records
appended under ``<home>/monitoring/telemetry.jsonl``. This is the Tier-3
development store described by the architecture document's database policy;
production deployments are expected to swap in a quantum-secured time-series
backend behind this same interface.

Records::

    {"ts": ..., "model_id": ..., "kind": "...", "name": "...",
     "value": ..., "source": "...", "detail": {...}}
"""
from __future__ import annotations

import json
import statistics
import threading
import time
from pathlib import Path


class TelemetryCollector:
    """Append-only telemetry store with query helpers."""

    def __init__(self, store_path: Path) -> None:
        self.path = Path(store_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def record(
        self,
        model_id: str,
        kind: str,
        name: str,
        value: float | None = None,
        source: str = "platform",
        detail: dict | None = None,
    ) -> dict:
        entry = {
            "ts": time.time(),
            "model_id": model_id,
            "kind": kind,
            "name": name,
            "value": value,
            "source": source,
            "detail": detail or {},
        }
        with self._lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def record_model_health(
        self,
        model_id: str,
        metrics: dict,
        source: str = "health_check",
        extra: dict | None = None,
    ) -> int:
        """Persist every numeric metric from a health observation."""
        n = 0
        for name, value in (metrics or {}).items():
            if isinstance(value, (int, float)):
                self.record(model_id, "metric", name, float(value), source,
                            detail=extra or {})
                n += 1
        return n

    def record_drift(self, model_id: str, drift_summary: dict | None) -> dict | None:
        if not drift_summary:
            return None
        return self.record(
            model_id,
            "drift",
            str(drift_summary.get("max_severity", "NONE")),
            float(drift_summary.get("drift_count", 0)),
            source="drift_engine",
            detail=dict(drift_summary),
        )

    # ------------------------------------------------------------------
    def _entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        continue
        return out

    def iter_entries(self, model_id: str | None = None, kind: str | None = None):
        for e in self._entries():
            if model_id is not None and e.get("model_id") != model_id:
                continue
            if kind is not None and e.get("kind") != kind:
                continue
            yield e

    def series(self, model_id: str, name: str) -> list[dict]:
        return [e for e in self.iter_entries(model_id, "metric")
                if e.get("name") == name]

    def latest(self, model_id: str, name: str) -> dict | None:
        s = self.series(model_id, name)
        return s[-1] if s else None

    def summary(self, model_id: str) -> dict:
        """Per-metric rolling summary over everything recorded."""
        by_name: dict[str, list[float]] = {}
        for e in self.iter_entries(model_id, "metric"):
            v = e.get("value")
            if isinstance(v, (int, float)):
                by_name.setdefault(e["name"], []).append(float(v))
        out = {}
        for name, values in sorted(by_name.items()):
            out[name] = {
                "count": len(values),
                "last": values[-1],
                "min": min(values),
                "max": max(values),
                "mean": round(statistics.fmean(values), 6),
            }
        return out

    def drift_history(self, model_id: str) -> list[dict]:
        return list(self.iter_entries(model_id, "drift"))
