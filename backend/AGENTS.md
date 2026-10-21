# Backend

FastAPI app managed with uv (Python 3.14). It serves the API under `/api` and static files from `static/` at `/`.

## Structure

- `app/main.py`: FastAPI app. `GET /api/health` returns `{"status": "ok"}`. Everything else is served from `static/`.
- `static/`: files served at `/`. It currently holds a hello world `index.html` that calls `/api/health`.
- `tests/`: pytest tests that use FastAPI's `TestClient`.

## Commands (run from `backend/`)

- `uv sync`: install dependencies
- `uv run uvicorn app.main:app --reload`: dev server on port 8000
- `uv run pytest`: run the tests

## Docker

The root `Dockerfile` installs the locked dependencies with uv and runs uvicorn on port 8000. The scripts in `scripts/` build and run it.
