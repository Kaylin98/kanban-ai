# Backend

FastAPI app managed with uv (Python 3.14). It serves the API under `/api` and the static frontend build at `/`.

## Structure

- `app/main.py`: FastAPI app. `GET /api/health` returns `{"status": "ok"}`. Everything else is served from `STATIC_DIR` (default `../frontend/out`, the Next.js static export).
- Auth: `POST /api/login` checks the hardcoded credentials (`user` / `password`) and stores the username in a signed session cookie (Starlette `SessionMiddleware`, secret from `SESSION_SECRET`, default `dev-secret`). `POST /api/logout` clears it. `GET /api/me` returns `{"username"}` or 401. Use the `current_user` dependency to require a session on other routes.
- `app/board.py`: Pydantic models (`Card`, `Column`, `Board`) that mirror the frontend's `BoardData`. `Board` rejects boards whose columns aren't the fixed `COLUMN_IDS` or whose cards aren't each in exactly one column. `DEFAULT_BOARD` is the board every user starts with.
- `app/db.py`: SQLite via `sqlite3`, schema and approach in `docs/DATABASE.md`. File at `DATABASE_PATH` (default `../data/pm.db`, which is `/app/data/pm.db` on the Docker volume). `init_db` runs at startup: it creates the file and tables and seeds the `user` row. `get_board` / `save_board` map between rows and `Board`, creating the default board on first use.
- Board API: `GET /api/board` returns the session user's board, `PUT /api/board` validates and saves a full board (422 if invalid). Both return 401 without a session.
- `app/ai.py`: OpenRouter calls through the `openai` SDK. `complete(messages)` returns the reply text. The key comes from `OPENROUTER_API_KEY` and the model from `OPENROUTER_MODEL` (default `dots-studio/dots-3-note-preview:free`). OpenRouter falls back to `FALLBACK_MODELS` if it fails. Calls time out after 60 seconds and are capped at 2000 tokens.
- `tests/`: pytest tests that use FastAPI's `TestClient`. `conftest.py` points `STATIC_DIR` at `tests/static` so the tests don't need a frontend build. Its `client` fixture uses a fresh temporary database for each test and runs startup; `logged_in` is the same client after logging in.

## Commands (run from `backend/`)

- `uv sync`: install dependencies
- `uv run uvicorn app.main:app --reload`: dev server on port 8000 (run `npm run build` in `frontend/` first)
- `uv run pytest`: run the tests (the live AI test is skipped without `OPENROUTER_API_KEY`; `uv run --env-file ../.env pytest` includes it)

## Docker

The root `Dockerfile` builds the frontend in a Node stage, then installs the locked Python dependencies with uv and copies the build to `/app/frontend/out`. It runs uvicorn on port 8000. The scripts in `scripts/` build and run it.
