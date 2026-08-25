from fastapi.testclient import TestClient
from product.backend_api.app.main import app

client = TestClient(app)

def test_drift_events():
    response = client.get("/api/drift/events")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # We don't know if there are any drift events, but we can check the structure if the list is not empty
    if len(data) > 0:
        event = data[0]
        # We expect at least a timestamp and target
        assert "timestamp" in event
        assert "target" in event