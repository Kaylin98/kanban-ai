# Backend

FastAPI app managed with uv (Python 3.14). It serves the API under `/api` and the static frontend build at `/`.

## Structure

- `app/main.py`: FastAPI app. `GET /api/health` returns `{"status": "ok"}`. Everything else is served from `STATIC_DIR` (default `../frontend/out`, the Next.js static export).
- Auth: `POST /api/login` checks the hardcoded credentials (`user` / `password`) and stores the username in a signed session cookie (Starlette `SessionMiddleware`, secret from `SESSION_SECRET`, default `dev-secret`). `POST /api/logout` clears it. `GET /api/me` returns `{"username"}` or 401. Use the `current_user` dependency to require a session on other routes.
- `tests/`: pytest tests that use FastAPI's `TestClient`. `conftest.py` points `STATIC_DIR` at `tests/static` so the tests don't need a frontend build.

## Commands (run from `backend/`)

- `uv sync`: install dependencies
- `uv run uvicorn app.main:app --reload`: dev server on port 8000 (run `npm run build` in `frontend/` first)
- `uv run pytest`: run the tests

## Docker

The root `Dockerfile` builds the frontend in a Node stage, then installs the locked Python dependencies with uv and copies the build to `/app/frontend/out`. It runs uvicorn on port 8000. The scripts in `scripts/` build and run it.
