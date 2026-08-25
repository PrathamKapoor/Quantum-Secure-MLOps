import pytest
from fastapi.testclient import TestClient

from product.backend_api.app.main import app

client = TestClient(app)


@pytest.mark.parametrize("target", ["LOAD", "WIND", "PV", "load", "wind"])
def test_per_target_predictions(target):
    r = client.get(f"/api/forecast/predictions/{target}")
    assert r.status_code == 200
    data = r.json()
    assert data["target"] == target.lower()
    assert isinstance(data["predictions"], list)
    for row in data["predictions"][:5]:
        assert row["target"].upper() == target.upper()
        assert {"timestamp", "prediction", "actual"} <= set(row)


def test_invalid_target_returns_404_with_guidance():
    r = client.get("/api/forecast/predictions/SOLAR")
    assert r.status_code == 404
    assert "LOAD, WIND, PV" in r.json()["detail"]


def test_predictions_filter_and_limit():
    all_rows = client.get("/api/forecast/predictions?limit=10").json()
    assert len(all_rows) == 10
    wind = client.get("/api/forecast/predictions", params={"target": "WIND", "limit": 5}).json()
    assert len(wind) == 5 and all(r["target"] == "WIND" for r in wind)


def test_target_summary_reports_artifact_derived_fields():
    s = client.get("/api/forecast/summary/LOAD").json()
    assert s["horizon"] == "H24"
    assert s["count"] and s["model"]
