# Kanban Studio

A single-board Kanban app with an AI assistant that can create, edit, move and delete cards for you. Built with a Next.js static frontend, a FastAPI backend, SQLite, and free models on OpenRouter, all in one Docker container.

- Drag-and-drop board with five renameable columns, autosaved to SQLite
- AI chat that edits the board through validated Structured Outputs, with a self-correction retry
- Tested with pytest, Vitest and Playwright

## Quick start

Requires Docker and [uv](https://docs.astral.sh/uv/). Copy `.env.example` to `.env` and fill it in:

```bash
uv run scripts/hash_password.py                                # value for APP_PASSWORD_HASH
python -c "import secrets; print(secrets.token_urlsafe(32))"   # value for SESSION_SECRET
```

Paste the hash into `.env` without quotes. Then:

```bash
./scripts/start.sh                                         # Mac / Linux
powershell -ExecutionPolicy Bypass -File scripts\start.ps1 # Windows
```

Open http://localhost:8000 and sign in with your username and password. Stop with `scripts/stop.sh` or `scripts\stop.ps1`. If the page doesn't load, `docker logs pm-app` names any missing variable.

## Environment variables

| Name | Required | Purpose |
|---|---|---|
| `APP_USERNAME` | Yes | Sign-in username |
| `APP_PASSWORD_HASH` | Yes | Argon2 hash of the password, from `scripts/hash_password.py` |
| `SESSION_SECRET` | Yes | Signs session cookies; at least 32 characters |
| `ENV` | No | `production` for Secure cookies, no API docs, and client IPs from Render's proxy. Default `development` |
| `OPENROUTER_API_KEY` | For chat | OpenRouter API key |
| `OPENROUTER_MODEL` | No | Default `dots-studio/dots-3-note-preview:free` |
| `PORT` | No | Default `8000` |

The app refuses to start if a required variable is missing or invalid.

## Deploying to Render

1. Push to GitHub. Secrets stay out: `.env*` and `certs/` are gitignored and excluded from the Docker image.
2. Create a Render **Web Service** from the repo, runtime **Docker**, instance type **Free**.
3. Set `ENV=production`, `APP_USERNAME`, `APP_PASSWORD_HASH` (unquoted), `SESSION_SECRET` and `OPENROUTER_API_KEY` in the dashboard. Don't set `PORT`; Render provides it.
4. Set the health check path to `/api/health`.

The free tier has no persistent disk, so the board resets to the default on every deploy, restart and spin-down. See [docs/OVERVIEW.md](docs/OVERVIEW.md#13-deploying-to-render) for post-deploy checks.

## Documentation

- [docs/OVERVIEW.md](docs/OVERVIEW.md): features, architecture, API, security, running, testing, limitations, deployment and roadmap
- [docs/DATABASE.md](docs/DATABASE.md): database schema and mapping
- [docs/PLAN.md](docs/PLAN.md): the build plan and decision log
