import os
from pathlib import Path

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient

USERNAME = "test-user"
PASSWORD = "test-password"

os.environ["STATIC_DIR"] = str(Path(__file__).parent / "static")
os.environ["APP_USERNAME"] = USERNAME
os.environ["APP_PASSWORD_HASH"] = PasswordHasher().hash(PASSWORD)
os.environ["SESSION_SECRET"] = "test-secret-that-is-at-least-32-characters"

from app import db, main  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client backed by a fresh database file. Entering it runs startup."""
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "test.db")
    main.login_limiter.hits.clear()
    main.chat_limiter.hits.clear()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def logged_in(client):
    client.post("/api/login", json={"username": USERNAME, "password": PASSWORD})
    return client
