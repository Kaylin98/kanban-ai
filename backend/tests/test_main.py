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
    assert "Test index" in response.text


def test_login_flow():
    client = TestClient(app)
    assert client.get("/api/me").status_code == 401

    response = client.post("/api/login", json={"username": "user", "password": "password"})
    assert response.status_code == 200
    assert client.get("/api/me").json() == {"username": "user"}

    assert client.post("/api/logout").status_code == 200
    assert client.get("/api/me").status_code == 401


def test_login_rejects_wrong_password():
    client = TestClient(app)
    response = client.post("/api/login", json={"username": "user", "password": "wrong"})
    assert response.status_code == 401
    assert client.get("/api/me").status_code == 401
