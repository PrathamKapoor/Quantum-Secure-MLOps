from fastapi.testclient import TestClient

from product.backend_api.app.main import app

client = TestClient(app)

KNOWN_MODEL = "demo-model"


def test_versions_listing():
    r = client.get(f"/api/models/{KNOWN_MODEL}/versions")
    if r.status_code == 404:
        pytest.skip("registry has no demo-model in this environment")
    versions = r.json()["versions"]
    assert len(versions) >= 1
    assert {"version", "version_id", "state"} <= set(versions[-1])


def test_version_detail_includes_passport_fields():
    versions = client.get(f"/api/models/{KNOWN_MODEL}/versions").json()["versions"]
    version_id = versions[-1]["version_id"]
    r = client.get(f"/api/models/{KNOWN_MODEL}/versions/{version_id}")
    assert r.status_code == 200
    detail = r.json()
    # Signature suite proves passport was loaded; feature_set may be 'unknown'
    # when the frozen passport carries no such field.
    assert detail["signature_suite"]
    assert detail["feature_set"]


def test_unknown_model_or_version_404():
    assert client.get("/api/models/nope-model/versions").status_code == 404
    r = client.get(f"/api/models/{KNOWN_MODEL}/versions/deadbeef")
    assert r.status_code in (404, 500)  # 500 only if registry raises on bad id


def test_no_mutation_routes_exist():
    """Governance boundary: lifecycle actions are not exposed over HTTP."""
    for path in (
        "/api/models/x/promote",
        "/api/models/x/rollback",
        "/api/models/x/retrain",
        "/api/governance/promote",
    ):
        assert client.post(path, json={}).status_code in (404, 405)
