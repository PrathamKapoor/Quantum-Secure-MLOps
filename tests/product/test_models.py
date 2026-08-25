from fastapi.testclient import TestClient
from product.backend_api.app.main import app

client = TestClient(app)

def test_models():
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # We don't know how many models are registered, but we can check the structure if the list is not empty
    if len(data) > 0:
        model = data[0]
        assert "target" in model
        assert "model_name" in model
        assert "feature_set" in model
        assert "fingerprint" in model
        assert "lifecycle_state" in model