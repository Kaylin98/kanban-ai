# High level steps for project

Each part has a checklist of substeps, the tests to write, and success criteria. Check off items as they are completed. Do not start a part until the previous part's success criteria are met.

## Decisions

- Auth: backend cookie session. FastAPI checks the hardcoded credentials (`user` / `password`) and sets a signed session cookie. The board API identifies the user from the cookie.
- Database: SQLite with `users`, `boards`, `columns` and `cards` tables (see `docs/DATABASE.md`). The API sends and receives the board in the `BoardData` shape the frontend uses (`frontend/src/lib/kanban.ts`); the backend maps between rows and that shape.
- Testing: aim for around 80% coverage where that is sensible, but only write tests that add real value. Falling short of 80% is fine; never add tests just to hit the number. This applies wherever a part below asks for "comprehensive" or "thorough" tests.
- AI updates: the Structured Output returns a list of card operations (create / update / move / delete), decided at Part 9.
- Chat history: frontend state only, sent with each `/api/chat` request and lost on refresh. No database table for the MVP (decided at Part 10).

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

Status: complete. Approved by the user. pytest 18 passed. In the container, a renamed column survived `docker restart`, and the database file is at `/app/data/pm.db` on the `pm-data` volume. `Board` also rejects boards whose columns are not the fixed five, or whose cards are not each in exactly one column, so invalid AI updates in Part 9 get the same 422.

## Part 7: Frontend + Backend

Now have the frontend actually use the backend API, so that the app is a proper persistent Kanban board. Test very throughly.

- [x] `frontend/src/lib/api.ts`: small fetch helpers (`getBoard`, `saveBoard`, login, logout, me)
- [x] The board is loaded from `GET /api/board` after login, with a simple loading state (done in `page.tsx`, which passes it to `KanbanBoard` as `initialBoard`)
- [x] Every change (move, rename, add, edit, delete) updates local state and saves it with `PUT /api/board`
- [x] Remove the use of `initialData` from the frontend; the backend owns the default board (a copy stays as a test fixture in `src/test/board.ts`)

Tests:
- Vitest: the board renders from a mocked API response; each change type calls `saveBoard` with the expected board
- Playwright: log in, make each type of change, reload, and confirm the changes are still there
- Manual check: stop and start the container, and the changes are still there

Success criteria: the board persists across reloads and container restarts, and all tests pass.

Status: complete. Approved by the user. Vitest 12, Playwright 13 (locally, in parallel and with one worker, and against the container), pytest 18. A change saved before `scripts/stop` was still there after `scripts/start` recreated the container. Notes:
- The move-card unit test is not in Vitest, because dnd-kit drags don't work in jsdom. The Playwright reload test covers it.
- Saves are queued in `saveBoard`. The backend handles requests concurrently, so the per-keystroke saves while renaming a column could otherwise finish out of order.
- Local Playwright runs use a database in the temp directory. Against the container (`BASE_URL`), the tests reset that user's board.

## Part 8: AI connectivity

Now allow the backend to make an AI call via OpenRouter. Test connectivity with a simple "2+2" test and ensure the AI call is working.

- [x] Add the `openai` Python SDK, configured with `base_url="https://openrouter.ai/api/v1"` and `OPENROUTER_API_KEY` from the environment
- [x] `backend/app/ai.py`: a function that sends messages to the model in `OPENROUTER_MODEL` (default `dots-studio/dots-3-note-preview:free`, with `nvidia/nemotron-3-super-120b-a12b:free` as fallback) and returns the response
- [x] A connectivity test that asks "What is 2+2?"
- [x] Check whether this model on OpenRouter supports Structured Outputs (`response_format` with a JSON schema), and note any rate limits. Report back before Part 9.

Tests:
- pytest (live, skipped when `OPENROUTER_API_KEY` is not set): the response to "2+2" contains "4"

Success criteria: the live test passes from inside the container, and Structured Outputs support is confirmed (or a workaround is agreed with the user).

Status: complete. The live "2+2" check passes inside the container. Notes:
- `openai/gpt-oss-120b:free` was withdrawn (OpenRouter returns 404 and points to the paid slug). The user first chose `nvidia/nemotron-3-super-120b-a12b:free`, but its only provider (Nvidia) was down throughout (status -5, 0% uptime, provider 404).
- `openrouter/free` worked for "2+2", but in Part 9 it routed to small models that returned invalid updates and once generated 65,536 tokens. The model is now `dots-studio/dots-3-note-preview:free` (`OPENROUTER_MODEL` in `.env`), with Nemotron as OpenRouter's fallback (`models`), a 60 second timeout, and `max_tokens` 2000. The live "2+2" test passed locally.
- Structured Outputs: all three models list `structured_outputs` and `response_format`. Three live `chat.completions.parse` calls with a Pydantic schema all returned valid parsed objects. Part 9 sends `provider.require_parameters` so OpenRouter only routes to providers that support the schema.
- Rate limits: the key is on the free tier, with 50 free-model requests per day (1000 with $10 of credits) and a $1 spending cap.
- In the container, calls failed TLS verification because Norton re-signs HTTPS traffic ("generated by Norton Antivirus for SSL"), and the exclusions could not be relied on. The container now trusts Norton's root: `scripts/start` copies the file in `NODE_EXTRA_CA_CERTS` to `certs/extra-ca.pem` (gitignored), and the Dockerfile sets `SSL_CERT_FILE` to the system CAs plus any `certs/*.pem`. Without the file, the bundle is just the system CAs. The bundle uses the system CAs rather than certifi because the `openai` SDK's client (`httpx2`) uses the system store on Linux and certifi is not installed. Verified in the container: a Norton-re-signed host (github.com) returns 200 with the bundle and fails `CERTIFICATE_VERIFY_FAILED` without it. Check with `docker exec pm-app python -c "from app import ai; print(ai.complete([{'role': 'user', 'content': 'What is 2+2?'}]))"`.

## Part 9: AI with the Kanban board

Now extend the backend call so that it always calls the AI with the JSON of the Kanban board, plus the user's question (and conversation history). The AI should respond with Structured Outputs that includes the response to the user and optionally an update to the Kanban. Test thoroughly.

- [x] Decide with the user: full replacement board or a list of operations in the Structured Output (decided: a list of operations)
- [x] `POST /api/chat`: takes the user's message and the conversation history, and requires a session
- [x] Build the prompt: a system prompt explaining the board and the rules (columns are fixed, card ids must be unique), the current board JSON, the history and the new message
- [x] Define the Pydantic response schema: `reply` (string) plus a list of create / update / move / delete operations, and pass it as the Structured Output schema
- [x] Validate any update, save it, and return `{reply, board}` where `board` is the updated board or null
- [x] One self-correction retry: if an operation is rejected, send the model its response and the exact error and ask for a corrected list. If the retry also fails, return 502

Tests:
- pytest with the AI call mocked: a reply-only response leaves the board unchanged; an update response saves the board; an invalid update that is corrected on the retry is saved; an update that is invalid twice is rejected and the board is left unchanged; 401 without a session
- pytest (live, skippable): asking it to "add a card called X to Backlog" results in a saved board containing X in Backlog

Success criteria: all tests pass, and a live request can create, edit and move cards.

Status: complete, approved by the user. pytest 28 passed (2 live tests skipped without a key). Notes:
- The server assigns ids to created cards. Unknown card or column ids reject the whole update, and the rejected operations are logged. The model then gets one retry with the error (e.g. "card new-card-1 does not exist. Use a create operation to add a new card..."). If the retry is also invalid, the response is 502 and the board stays unchanged.
- Live, with dots: a three-message conversation created a card, renamed a card and moved two cards (one to the top of Backlog), all correctly.
- The live add-card test is flaky: it failed on 2 of its last 4 runs. Each time dots returned an operation for a made-up id ("new-card-1") instead of a create. The logs showed that every rejection came from the model, not from id handling. Two prompt rules fixed the most common mistakes: never refer to a new card in another operation, and return operations only for the latest message.
- After adding the retry, the live add-card test passed 4 of 4 runs. None of the runs needed the retry (no rejections were logged), so the retry has not yet been exercised live.

## Part 10: AI chat sidebar

Now add a beautiful sidebar widget to the UI supporting full AI chat, and allowing the LLM (as it determines) to update the Kanban based on its Structured Outputs. If the AI updates the Kanban, then the UI should refresh automatically.

- [x] Decide with the user where chat history lives (decided: frontend state only, sent with each `/api/chat` request and lost on refresh; no database table for the MVP)
- [ ] `ChatSidebar` component: message list, input, send button (purple), loading state, using the project color scheme
- [ ] Sending posts to `/api/chat` with the history, and appends the reply
- [ ] When the response includes a board, replace the board state so the UI refreshes
- [ ] Layout: the sidebar sits beside the board without breaking drag and drop

Tests:
- Vitest: sending a message shows the user message and the reply; a response with a board updates the rendered board; the loading state shows while waiting
- Playwright with `/api/chat` mocked: send a message, see the reply, see the board update
- Manual check in the container with the live model: ask it to create, edit and move cards

Success criteria: chat works end to end in the container, AI changes show up on the board without a reload, and all tests pass.
