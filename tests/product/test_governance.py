from fastapi.testclient import TestClient
from product.backend_api.app.main import app

client = TestClient(app)

def test_governance_events():
    response = client.get("/api/governance/events")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # We don't know if there are any structure, but we can check that it's a list