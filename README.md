# Kanban Studio

A single-board Kanban app with an AI assistant that can create, edit, move and delete cards for you. Built with a Next.js static frontend, a FastAPI backend, SQLite, and free models on OpenRouter, all in one Docker container.

- Drag-and-drop board with five renameable columns, autosaved to SQLite
- AI chat that edits the board through validated Structured Outputs, with a self-correction retry
- Tested with pytest, Vitest and Playwright

## Quick start

Requires Docker. Put `OPENROUTER_API_KEY` in `.env` in the project root, then:

```bash
./scripts/start.sh                                         # Mac / Linux
powershell -ExecutionPolicy Bypass -File scripts\start.ps1 # Windows
```

Open http://localhost:8000 and sign in with `user` / `password`. Stop with `scripts/stop.sh` or `scripts\stop.ps1`.

## Documentation

- [docs/OVERVIEW.md](docs/OVERVIEW.md): features, architecture, API, AI integration, running, testing, limitations, deployment and roadmap
- [docs/DATABASE.md](docs/DATABASE.md): database schema and mapping
- [docs/PLAN.md](docs/PLAN.md): the build plan and decision log
