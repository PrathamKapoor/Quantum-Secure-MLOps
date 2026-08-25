from fastapi.testclient import TestClient

from product.backend_api.app.main import app

client = TestClient(app)


def test_experiments_listing_is_honest_about_empty_store():
    r = client.get("/api/experiments")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["available"], bool)
    assert isinstance(data["experiments"], list)
    if not any(e["run_count"] for e in data["experiments"]):
        assert "no recorded runs" in data["note"].lower()


def test_unknown_experiment_returns_404():
    assert client.get("/api/experiments/999999").status_code == 404


def test_experiment_detail_shape_when_present():
    listing = client.get("/api/experiments").json()
    if not listing["experiments"]:
        pytest.skip("tracking store has no experiments")
    eid = int(listing["experiments"][0]["experiment_id"])
    detail = client.get(f"/api/experiments/{eid}").json()
    assert "experiment" in detail and "runs" in detail
    for run in detail["runs"]:
        assert {"run_id", "params", "metrics", "tags"} <= set(run)
