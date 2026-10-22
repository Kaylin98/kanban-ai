# High level steps for project

Each part has a checklist of substeps, the tests to write, and success criteria. Check off items as they are completed. Do not start a part until the previous part's success criteria are met.

## Decisions

- Auth: backend cookie session. FastAPI checks the hardcoded credentials (`user` / `password`) and sets a signed session cookie. The board API identifies the user from the cookie.
- Database: SQLite with `users`, `boards`, `columns` and `cards` tables (see `docs/DATABASE.md`). The API sends and receives the board in the `BoardData` shape the frontend uses (`frontend/src/lib/kanban.ts`); the backend maps between rows and that shape.
- Testing: aim for around 80% coverage where that is sensible, but only write tests that add real value. Falling short of 80% is fine; never add tests just to hit the number. This applies wherever a part below asks for "comprehensive" or "thorough" tests.
- Open, to decide at Part 9: whether the AI's Structured Output returns a full replacement board or a list of operations. A list of operations maps naturally onto the tables; a full replacement board reuses the `PUT /api/board` write path.
- Open, to decide at Part 10: where chat history lives (frontend state or the database).

## Part 1: Plan

Enrich this document to plan out each of these parts in detail, with substeps listed out as a checklist to be checked off by the agent, and with tests and success criteria for each. Also create an AGENTS.md file inside the frontend directory that describes the existing code there. Ensure the user checks and approves the plan.

- [x] Review AGENTS.md, this plan and the existing frontend code
- [x] Enrich this document with substeps, tests and success criteria for each part
- [x] Create `frontend/AGENTS.md` describing the existing frontend code
- [x] User reviews and approves this plan

Success criteria: the user has approved this document and `frontend/AGENTS.md` exists.

## Part 2: Scaffolding

Set up the Docker infrastructure, the backend in backend/ with FastAPI, and write the start and stop scripts in the scripts/ directory. This should serve example static HTML to confirm that a 'hello world' example works running locally and also make an API call.

- [x] Create a uv project in `backend/` (`pyproject.toml`, `uv.lock`) with `fastapi` and `uvicorn`, plus `pytest` and `httpx2` as dev dependencies (Starlette's test client now prefers `httpx2` over `httpx`)
- [x] `backend/app/main.py`: FastAPI app with `GET /api/health` returning `{"status": "ok"}`, and static files served from `backend/static` at `/`
- [x] `backend/static/index.html`: a hello world page that calls `/api/health` and shows the result
- [x] `Dockerfile` in the project root: a Python image with uv, which installs dependencies and runs uvicorn on port 8000
- [x] `.dockerignore` excluding `node_modules`, `.next`, `out`, `.venv`, `.git`, `.env` and test output
- [x] `scripts/start.sh` and `scripts/stop.sh` (Mac and Linux), `scripts/start.ps1` and `scripts/stop.ps1` (PC). Start builds the image and runs the container with `--env-file .env`, port 8000, and a named volume for the database. Stop stops and removes the container.
- [x] Add `node_modules/`, `.next/`, `out/`, `test-results/`, `playwright-report/` and `*.db` to `.gitignore`
- [x] Update `backend/AGENTS.md` and `scripts/AGENTS.md`

Tests:
- pytest: `GET /api/health` returns 200 and `{"status": "ok"}`
- pytest: `GET /` returns the hello world HTML

Success criteria:
- `scripts/start` brings up the container. At http://localhost:8000 the hello world page loads and shows the result of the API call.
- `scripts/stop` stops it cleanly.
- `uv run pytest` passes.

Status: complete. All success criteria verified, including the scripts on Mac/Linux (confirmed by the user).

## Part 3: Add in Frontend

Now update so that the frontend is statically built and served, so that the app has the demo Kanban board displayed at /. Comprehensive unit and integration tests.

- [x] Set `output: "export"` in `frontend/next.config.ts`
- [x] Make the Dockerfile multi-stage: a Node stage runs `npm ci` and `npm run build`, and the Python stage copies `frontend/out` into the static directory the backend serves (on machines with Norton, HTTPS scanning must exclude `registry.npmjs.org` and `fonts.googleapis.com`, or the build fails TLS verification)
- [x] Remove the hello world page
- [x] Add card editing, which the requirements ask for and the demo lacks: edit a card's title and details inline, and save or cancel
- [x] Point Playwright at the running container (http://localhost:8000) as an option, while keeping the dev server as the default (`BASE_URL` env var)

Tests:
- Vitest: edit a card's title and details, cancel an edit
- Vitest: the existing tests for `moveCard` and `KanbanBoard` still pass
- Playwright: load the board, add, edit and delete a card, rename a column, drag a card between columns
- pytest: `GET /` serves the built `index.html`

Success criteria:
- After `scripts/start`, the Kanban board works at http://localhost:8000.
- All unit and e2e tests pass.

Status: complete. Approved by the user.

## Part 4: Add in a fake user sign in experience

Now update so that on first hitting /, you need to log in with dummy credentials ("user", "password") in order to see the Kanban, and you can log out. Comprehensive tests.

- [x] Backend: `POST /api/login` checks the credentials and sets a signed session cookie (Starlette `SessionMiddleware`). The secret key comes from an env var, with a dev default.
- [x] Backend: `POST /api/logout` clears the session. `GET /api/me` returns the username, or 401.
- [x] Frontend: on load, call `/api/me`. Show a login form if there is no session, otherwise show the board.
- [x] Frontend: logout button in the header
- [x] Frontend: show an error message for wrong credentials
- [x] Use the color scheme: purple for the submit button, navy for headings
- [x] Playwright now needs the backend, so by default it builds the frontend and runs uvicorn locally (port 8001) instead of `npm run dev`; `BASE_URL` still targets the container

Tests:
- pytest: login works with the correct credentials and fails with wrong ones; `/api/me` returns 401 before login and 200 after; logout clears the session
- Vitest: login form renders, an error shows on failure, the board shows on success, logout returns to the login form (fetch mocked)
- Playwright: visit `/`, see the login form, log in, see the board, log out, see the login form again

Success criteria: the board can't be seen without logging in. Login and logout work in the container, and all tests pass.

Status: complete. Approved by the user. All tests pass (pytest 4, Vitest 12, Playwright 12 locally and against the container). Known environment issue: when several Playwright workers load the same page at once, Chrome's requests sometimes stall in 10 second steps and tests time out. The server answers every request in under 200 ms, curl and Node requests are unaffected, and it happens against both local uvicorn and the container, so the suspect is Norton 360 inspecting Chrome's traffic. With `--workers=1` it never happens.

## Part 5: Database modeling

Now propose a database schema for the Kanban, saving it as JSON. Document the database approach in docs/ and get user sign off.

- [x] Write `docs/DATABASE.md` covering:
  - `users`: `id` (integer primary key), `username` (unique text)
  - `boards`: `id` (integer primary key), `user_id` (unique foreign key to users, so one board per user for the MVP), `updated_at`
  - `columns`: `id`, `board_id`, `key` (the frontend id), `title`, `position`
  - `cards`: `id`, `column_id`, `key` (the frontend id), `title`, `details`, `position`
  - Sample rows and the `BoardData` JSON the API returns for them
  - How rows map to and from `BoardData` on read, write and create
  - Lifecycle: create the db file and tables on startup if they are missing; seed the `user` row; create a user's board from the default board on first access
  - Location: database file at a path set by an env var, on the Docker volume
- [x] User reviews and approves the schema

Status: complete. Approved by the user.

Success criteria: the user has approved `docs/DATABASE.md`.

## Part 6: Backend

Now add API routes to allow the backend to read and change the Kanban for a given user; test this thoroughly with backend unit tests. The database should be created if it doesn't exist.

- [x] `backend/app/db.py`: SQLite connection (standard library `sqlite3`), table creation on startup, user seeding
- [x] `get_board(user_id)` and `save_board(user_id, board)` in `db.py`, mapping between rows and `BoardData` as described in `docs/DATABASE.md`
- [x] Pydantic models that mirror `BoardData` (`Card`, `Column`, `Board`)
- [x] `GET /api/board`: returns the session user's board, creating it from the default board on first access
- [x] `PUT /api/board`: validates and saves the full board for the session user
- [x] Both routes return 401 without a session

Tests (pytest, with a temporary database file for each test):
- The database and tables are created when the file doesn't exist
- 401 without login
- The first GET returns the default board
- PUT then GET returns the saved board, with column and card order preserved
- An invalid payload returns 422
- Each user's board is isolated from other users' boards (test with a second user inserted directly)

Success criteria: all backend tests pass, and board data survives a container restart.

Status: implemented, awaiting user review. pytest 18 passed. In the container, a renamed column survived `docker restart`, and the database file is at `/app/data/pm.db` on the `pm-data` volume. `Board` also rejects boards whose columns are not the fixed five, or whose cards are not each in exactly one column, so invalid AI updates in Part 9 get the same 422.

## Part 7: Frontend + Backend

Now have the frontend actually use the backend API, so that the app is a proper persistent Kanban board. Test very throughly.

- [ ] `frontend/src/lib/api.ts`: small fetch helpers (`getBoard`, `saveBoard`, login, logout, me)
- [ ] `KanbanBoard` loads the board from `GET /api/board` after login, with a simple loading state
- [ ] Every change (move, rename, add, edit, delete) updates local state and saves it with `PUT /api/board`
- [ ] Remove the use of `initialData` from the frontend; the backend owns the default board

Tests:
- Vitest: the board renders from a mocked API response; each change type calls `saveBoard` with the expected board
- Playwright: log in, make each type of change, reload, and confirm the changes are still there
- Manual check: stop and start the container, and the changes are still there

Success criteria: the board persists across reloads and container restarts, and all tests pass.

## Part 8: AI connectivity

Now allow the backend to make an AI call via OpenRouter. Test connectivity with a simple "2+2" test and ensure the AI call is working.

- [ ] Add the `openai` Python SDK, configured with `base_url="https://openrouter.ai/api/v1"` and `OPENROUTER_API_KEY` from the environment
- [ ] `backend/app/ai.py`: a function that sends messages to `openai/gpt-oss-120b:free` and returns the response
- [ ] A connectivity test that asks "What is 2+2?"
- [ ] Check whether this model on OpenRouter supports Structured Outputs (`response_format` with a JSON schema), and note any rate limits. Report back before Part 9.

Tests:
- pytest (live, skipped when `OPENROUTER_API_KEY` is not set): the response to "2+2" contains "4"

Success criteria: the live test passes from inside the container, and Structured Outputs support is confirmed (or a workaround is agreed with the user).

## Part 9: AI with the Kanban board

Now extend the backend call so that it always calls the AI with the JSON of the Kanban board, plus the user's question (and conversation history). The AI should respond with Structured Outputs that includes the response to the user and optionally an update to the Kanban. Test thoroughly.

- [ ] Decide with the user: full replacement board or a list of operations in the Structured Output
- [ ] `POST /api/chat`: takes the user's message and the conversation history, and requires a session
- [ ] Build the prompt: a system prompt explaining the board and the rules (columns are fixed, card ids must be unique), the current board JSON, the history and the new message
- [ ] Define the Pydantic response schema: `reply` (string) plus the optional board update, and pass it as the Structured Output schema
- [ ] Validate any update, save it, and return `{reply, board}` where `board` is the updated board or null

Tests:
- pytest with the AI call mocked: a reply-only response leaves the board unchanged; an update response saves the board; an invalid update is rejected and the board is left unchanged; 401 without a session
- pytest (live, skippable): asking it to "add a card called X to Backlog" results in a saved board containing X in Backlog

Success criteria: all tests pass, and a live request can create, edit and move cards.

## Part 10: AI chat sidebar

Now add a beautiful sidebar widget to the UI supporting full AI chat, and allowing the LLM (as it determines) to update the Kanban based on its Structured Outputs. If the AI updates the Kanban, then the UI should refresh automatically.

- [ ] Decide with the user where chat history lives
- [ ] `ChatSidebar` component: message list, input, send button (purple), loading state, using the project color scheme
- [ ] Sending posts to `/api/chat` with the history, and appends the reply
- [ ] When the response includes a board, replace the board state so the UI refreshes
- [ ] Layout: the sidebar sits beside the board without breaking drag and drop

Tests:
- Vitest: sending a message shows the user message and the reply; a response with a board updates the rendered board; the loading state shows while waiting
- Playwright with `/api/chat` mocked: send a message, see the reply, see the board update
- Manual check in the container with the live model: ask it to create, edit and move cards

Success criteria: chat works end to end in the container, AI changes show up on the board without a reload, and all tests pass.
