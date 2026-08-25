"""API security hygiene: CORS allow-list, docs policy, error shapes,
no mutation routes, bounded agent input."""
from fastapi.testclient import TestClient

from product.backend_api.app.main import app

client = TestClient(app)

ALLOWED_ORIGIN = "http://localhost:5173"
FOREIGN_ORIGIN = "https://evil.example.com"


def test_cors_allows_configured_origin():
    r = client.get("/health", headers={"Origin": ALLOWED_ORIGIN})
    assert r.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN


def test_cors_rejects_foreign_origin():
    r = client.get("/health", headers={"Origin": FOREIGN_ORIGIN})
    assert r.headers.get("access-control-allow-origin") != FOREIGN_ORIGIN


def test_interactive_docs_available_per_policy():
    # No repository policy disables docs today; contract documents this.
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_error_shapes_are_structured():
    r404 = client.get("/api/models/nope-model/versions")
    body404 = r404.json()
    assert r404.status_code == 404 and "detail" in body404

    r422 = client.post("/api/agents/explain", json={})  # missing query
    assert r422.status_code == 422
    assert "detail" in r422.json()


def test_agent_input_is_bounded():
    huge = "x" * 5000
    assert client.post("/api/agents/explain", json={"query": huge}).status_code == 422


def test_only_get_and_post_methods_exist():
    methods = set()
    for route in app.routes:
        methods |= set(getattr(route, "methods", []) or [])
    assert methods <= {"GET", "POST", "HEAD", "OPTIONS"}
