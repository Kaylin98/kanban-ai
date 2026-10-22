import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["STATIC_DIR"] = str(Path(__file__).parent / "static")

from app import db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client backed by a fresh database file. Entering it runs startup."""
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "test.db")
    with TestClient(app) as client:
        yield client


@pytest.fixture
def logged_in(client):
    client.post("/api/login", json={"username": "user", "password": "password"})
    return client
