from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "Hello World" in response.text
