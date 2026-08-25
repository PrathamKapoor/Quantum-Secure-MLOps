"""Research-immutability proof for the product API.

Exercises every read endpoint plus safe and unsafe agent requests, and
verifies that protected research artifacts are byte-for-byte unchanged.

Protected set (per docs/productization/research_boundary.md, mapped to what
exists in this repository):
  - artifacts/final_evaluation   (final evaluation outputs)
  - artifacts/research_tables    (released result tables)
  - configs/                     (frozen protocol/settings files)
  - identity/                    (trust anchors / key material metadata)

Bytecode caches are excluded; hashing is content-only.
"""
from __future__ import annotations

import hashlib
import os

import pytest
from fastapi.testclient import TestClient

from product.backend_api.app.main import app

PROTECTED_ROOTS = [
    "artifacts/final_evaluation",
    "artifacts/research_tables",
    "configs",
    "identity",
]

client = TestClient(app)


def _tree_digest(root: str) -> str:
    h = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in sorted(dirnames) if d != "__pycache__"]
        for name in sorted(filenames):
            if name.endswith(".pyc"):
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, "rb") as fh:
                    while chunk := fh.read(65536):
                        h.update(chunk)
            except OSError:
                pass
            h.update(path.encode())
    return h.hexdigest()


def _snapshot() -> dict[str, str]:
    return {root: _tree_digest(root) for root in PROTECTED_ROOTS}


def test_api_reads_and_agent_calls_do_not_mutate_research_artifacts():
    before = _snapshot()

    # Every read endpoint, including list + detail variants.
    read_paths = [
        "/health",
        "/api/forecast/status",
        "/api/forecast/predictions",
        "/api/forecast/predictions?limit=5",
        "/api/forecast/predictions/PV",
        "/api/forecast/summary/LOAD",
        "/api/models",
        "/api/experiments",
        "/api/experiments/0",
        "/api/drift/events",
        "/api/governance/events",
        "/api/governance/decisions",
        "/api/reports",
    ]
    for path in read_paths:
        r = client.get(path)
        assert r.status_code == 200, path

    # Detail endpoints that may legitimately 404 must still not mutate.
    for path in (
        "/api/models/nope/versions",
        "/api/drift/events/doesnotexist",
        "/api/experiments/424242",
    ):
        assert client.get(path).status_code in (200, 404), path

    # Agent surface: grounded question AND refused unsafe commands — neither
    # may write anywhere (the refusal path is especially sensitive).
    for query in (
        "Why was this model rejected?",
        "Promote model X",
        "Rollback model X",
        "Retrain model X",
        "Change governance policy",
        "Modify feature set",
        "Show me the final test results.",
    ):
        r = client.post("/api/agents/explain", json={"query": query})
        assert r.status_code == 200, query

    after = _snapshot()
    changed = {k: (v, after[k]) for k, v in before.items() if after[k] != v}
    assert not changed, f"Research artifacts mutated via API: {changed}"


def test_final_evaluation_artifact_untouched_after_forecast_reads():
    """Targeted check on the single most scientifically critical file."""
    pred_file = "artifacts/final_evaluation/final_predictions.csv"
    with open(pred_file, "rb") as fh:
        before = hashlib.sha256(fh.read()).hexdigest()

    rows = client.get("/api/forecast/predictions").json()
    assert len(rows) > 0

    with open(pred_file, "rb") as fh:
        after = hashlib.sha256(fh.read()).hexdigest()
    assert before == after
