"""Settings from the environment. The app refuses to start when a required one is missing."""

import os

ENV = os.environ.get("ENV", "development")
if ENV not in ("development", "production"):
    raise SystemExit(f"ENV must be 'development' or 'production', not {ENV!r}.")
PRODUCTION = ENV == "production"

missing = [
    name
    for name in ("APP_USERNAME", "APP_PASSWORD_HASH", "SESSION_SECRET")
    if not os.environ.get(name)
]
if missing:
    raise SystemExit(
        f"Missing required environment variables: {', '.join(missing)}. See .env.example."
    )

APP_USERNAME = os.environ["APP_USERNAME"]
APP_PASSWORD_HASH = os.environ["APP_PASSWORD_HASH"]
SESSION_SECRET = os.environ["SESSION_SECRET"]

if not APP_PASSWORD_HASH.startswith("$argon2"):
    raise SystemExit(
        "APP_PASSWORD_HASH must be an argon2 hash. Generate one with scripts/hash_password.py."
    )
if len(SESSION_SECRET) < 32:
    raise SystemExit(
        "SESSION_SECRET must be at least 32 characters. Generate one with: "
        'python -c "import secrets; print(secrets.token_urlsafe(32))"'
    )
