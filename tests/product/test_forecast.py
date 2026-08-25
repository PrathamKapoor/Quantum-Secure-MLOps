from fastapi.testclient import TestClient
from product.backend_api.app.main import app

client = TestClient(app)

def test_forecast_status():
    response = client.get("/api/forecast/status")
    assert response.status_code == 200
    data = response.json()
    assert "targets" in data
    assert "horizon" in data
    assert "models_locked" in data
    assert isinstance(data["targets"], list)
    assert "load" in data["targets"]
    assert "wind" in data["targets"]
    assert "pv" in data["targets"]
    assert data["horizon"] == "H24"
    assert data["models_locked"] is True