import base64
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config, db
from app.main import app
from conftest import PASSWORD, USERNAME


def login(client, username=USERNAME, password=PASSWORD, **kwargs):
    return client.post("/api/login", json={"username": username, "password": password}, **kwargs)


def run_app(code: str, **env) -> subprocess.CompletedProcess:
    """Imports the app in a fresh interpreter with `env` (None removes a variable) and runs `code`."""
    environ = {**os.environ, **env}
    for name in [name for name, value in env.items() if value is None]:
        del environ[name]
    return subprocess.run(
        [sys.executable, "-c", f"from app.main import app\n{code}"],
        cwd=Path(__file__).parents[1],
        env=environ,
        capture_output=True,
        text=True,
    )


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Test index" in response.text


def test_login_flow(client):
    assert client.get("/api/me").status_code == 401

    response = login(client)
    assert response.status_code == 200
    assert client.get("/api/me").json() == {"username": USERNAME}

    assert client.post("/api/logout").status_code == 200
    assert client.get("/api/me").status_code == 401


def test_wrong_username_and_wrong_password_look_the_same(client):
    wrong_password = login(client, password="wrong")
    wrong_username = login(client, username="someone")

    assert wrong_password.status_code == wrong_username.status_code == 401
    assert wrong_password.json() == wrong_username.json() == {"detail": "Invalid username or password"}
    assert client.get("/api/me").status_code == 401


def test_session_cookie_attributes(client):
    cookie = login(client).headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert f"max-age={7 * 24 * 60 * 60}" in cookie
    # Local development is plain HTTP; production is checked in test_production_mode.
    assert "secure" not in cookie


def test_login_is_rate_limited_per_ip(client):
    for _ in range(5):
        assert login(client, password="wrong").status_code == 401

    # Even the right password is refused until the window passes.
    response = login(client)
    assert response.status_code == 429
    # Outside production there is no proxy, so X-Forwarded-For is ignored.
    assert login(client, headers={"X-Forwarded-For": "203.0.113.9"}).status_code == 429


def test_successful_logins_are_not_rate_limited(client):
    for _ in range(10):
        assert login(client).status_code == 200


def test_production_rate_limits_by_last_forwarded_ip(client, monkeypatch):
    monkeypatch.setattr(config, "PRODUCTION", True)
    for attempt in range(5):
        # The client controls everything before the last entry, the one Render adds.
        headers = {"X-Forwarded-For": f"10.0.0.{attempt}, 198.51.100.7"}
        assert login(client, password="wrong", headers=headers).status_code == 401

    spoofed = {"X-Forwarded-For": "10.0.0.99, 198.51.100.7"}
    assert login(client, headers=spoofed).status_code == 429
    other_client = {"X-Forwarded-For": "198.51.100.8"}
    assert login(client, headers=other_client).status_code == 200


def test_security_headers(client):
    response = client.get("/")
    csp = response.headers["content-security-policy"]
    inline = base64.b64encode(hashlib.sha256(b"window.inline = 1").digest()).decode()

    assert f"script-src 'self' 'sha256-{inline}'" in csp
    assert "frame-ancestors 'none'" in csp
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert client.get("/api/health").headers["x-frame-options"] == "DENY"


def test_server_errors_hide_details(client, monkeypatch):
    def fail(user_id):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(db, "get_board", fail)
    login(client)
    raw = TestClient(app, raise_server_exceptions=False, cookies=client.cookies)

    response = raw.get("/api/board")

    assert response.status_code == 500
    assert response.text == "Internal Server Error"


def test_docs_are_served_in_development(client):
    assert client.get("/openapi.json").status_code == 200


def test_production_mode(tmp_path):
    result = run_app(
        "from fastapi.testclient import TestClient\n"
        "with TestClient(app) as c:\n"
        "    print([c.get(p).status_code for p in ('/docs', '/redoc', '/openapi.json')])\n"
        f"    print(c.post('/api/login', json={{'username': {USERNAME!r}, 'password': {PASSWORD!r}}})"
        ".headers['set-cookie'])\n",
        ENV="production",
        DATABASE_PATH=str(tmp_path / "test.db"),
    )

    assert result.returncode == 0, result.stderr
    docs, cookie = result.stdout.splitlines()
    assert docs == "[404, 404, 404]"
    assert "secure" in cookie.lower()


@pytest.mark.parametrize(
    "env, error",
    [
        ({"APP_USERNAME": None, "SESSION_SECRET": None}, "Missing required environment variables: APP_USERNAME, SESSION_SECRET"),
        ({"APP_PASSWORD_HASH": ""}, "Missing required environment variables: APP_PASSWORD_HASH"),
        ({"APP_PASSWORD_HASH": "password"}, "APP_PASSWORD_HASH must be an argon2 hash"),
        ({"SESSION_SECRET": "short"}, "SESSION_SECRET must be at least 32 characters"),
        ({"ENV": "prod"}, "ENV must be 'development' or 'production'"),
    ],
)
def test_refuses_to_start_with_bad_config(env, error):
    result = run_app("", **env)
    assert result.returncode == 1
    assert error in result.stderr
