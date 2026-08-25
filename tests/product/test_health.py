from fastapi.testclient import TestClient
from product.backend_api.app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["research_pipeline"] == "locked"
    assert data["product_api"] == "running"