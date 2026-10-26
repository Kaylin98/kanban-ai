# Frontend

A Next.js frontend for the Kanban board, built as a static export (`output: "export"` writes to `out/`), which the FastAPI backend serves at `/`. Sign in goes through the backend, and the board is loaded from and saved to the backend.

## Stack

- Next.js 16 (App Router), React 19, TypeScript
- Tailwind CSS 4, used through `@tailwindcss/postcss`
- @dnd-kit (core, sortable, utilities) for drag and drop
- Vitest + Testing Library (jsdom) for unit tests, Playwright for e2e

## Structure

- `src/app/layout.tsx`: root layout. Loads the Space Grotesk (display) and Manrope (body) fonts as CSS variables.
- `src/app/page.tsx`: calls `/api/me` on load, then shows `LoginForm` (no session) or loads the board with `getBoard` and shows `KanbanBoard` (with a logout handler). Renders nothing while checking the session and "Loading board..." while loading the board.
- `src/lib/api.ts`: fetch helpers for the backend (`me`, `login`, `logout`, `getBoard`, `saveBoard`, `sendChat`). `saveBoard` queues saves so they reach the server in order. `sendChat` waits for queued saves, posts `{message, history}` to `/api/chat` and returns `{reply, board}` (`board` is null when the AI changed nothing); it sends only the last 20 history messages (the server's cap) and throws `ChatRequestError` (with the HTTP `status`) if the request fails. `login` returns the HTTP status (200, 401, or 429 when rate limited). `MAX_MESSAGE_LENGTH` (2000) matches the server's cap and limits the chat input.
- `src/components/LoginForm.tsx`: username/password form; shows "Invalid username or password." for a 401 and a too-many-attempts message for a 429.
- `src/app/globals.css`: color scheme as CSS variables (`--accent-yellow`, `--primary-blue`, `--secondary-purple`, `--navy-dark`, `--gray-text`, plus surface, stroke and shadow tokens).
- `src/lib/kanban.ts`: the `Card`, `Column` and `BoardData` types, `moveCard` (pure function that reorders or moves cards) and `createId`.
- `src/components/KanbanBoard.tsx`: owns the board state (starting from the `initialBoard` prop) and `DndContext`. Handles drag end, column rename, and add, edit and delete card. An effect saves the board with `saveBoard` after every change, skipping the intermediate states while a card is dragged. Takes an `onLogout` prop for the header's Log out button. The columns are at least 260px wide; when they don't fit, the column area scrolls sideways (the page itself never does). The column chips in the header are hidden on phones. Renders the `ChatWidget`; a board from the AI replaces the state and is marked saved, because the server has already saved it.
- `src/components/ChatWidget.tsx`: the AI chat, a purple bubble fixed to the bottom right that opens a panel floating over the board. It starts minimized and saves open/minimized in localStorage (`chat-open`). Keeps the history in state only (lost on refresh, kept while minimized) and sends it with each message. Enter sends, Shift+Enter adds a line. Shows "Thinking..." while waiting, and calls `onBoardUpdate` when the reply includes a board. On failure it shows an error ("The assistant had trouble, try again." for a 502) and puts the message back in the input.- `src/components/KanbanColumn.tsx`: droppable column with an inline title input for renaming, its sortable cards, and a `NewCardForm`.
- `src/components/KanbanCard.tsx`: sortable card: title, details, then a row with Edit and Remove buttons, so title and details use the full card width. Edit switches to an inline title/details form; drag attributes and listeners are not attached while editing.
- `src/components/KanbanCardPreview.tsx`: card shown in the `DragOverlay` while dragging.
- `src/components/NewCardForm.tsx`: toggleable form to add a card (title required, details optional).

## Data shape

```ts
BoardData = { columns: { id, title, cardIds[] }[], cards: Record<id, { id, title, details }> }
```

The columns are fixed (no adding or deleting), but they can be renamed. Card order is the order of `cardIds` in each column.

## Tests

- `src/lib/kanban.test.ts`: `moveCard` reordering and moving between columns.
- `src/lib/api.test.ts`: `sendChat` sends only the last 20 history messages.
- `src/test/board.ts`: `defaultBoard`, matching the backend's `DEFAULT_BOARD`. Used by the unit tests and to reset the board in the e2e tests.
- `src/components/KanbanBoard.test.tsx`: renders the given board, and checks what `saveBoard` (mocked) receives when renaming a column, adding, removing and editing a card, and that cancelling an edit saves nothing. Also that a board from an AI reply is shown and not saved again.
- `src/components/ChatWidget.test.tsx`: starts minimized and remembers open/minimized, keeps the conversation while minimized, message and reply, history sent with the next message, loading state, `onBoardUpdate`, and the error messages for a 502, a 429 (hourly limit) and other failures (`sendChat` is mocked).
- `src/app/page.test.tsx`: login form without a session, loading state then the board from the API, error on wrong credentials, the rate-limit message, sign in and out (fetch is stubbed).
- `tests/auth.spec.ts`: Playwright sign in, reload, sign out, and wrong credentials.
- `tests/kanban.spec.ts`: Playwright tests that load the board, add, edit and delete a card, rename a column, drag a card between columns, and check that every type of change survives a reload. `beforeEach` signs in via `/api/login` and resets the board to `defaultBoard`.
- `tests/chat.spec.ts`: Playwright with `/api/chat` mocked: send a message, see the reply and the board update, and check the request body.
- Playwright runs one worker, because every spec resets the same user's board. It needs the backend, so by default it runs `npm run build` and serves `out/` with uvicorn on port 8001 (requires uv), with the database in the temp directory (`pm-e2e.db`). The local server gets test-only credentials (`test-user` / `test-password`, hash in `playwright.config.ts`); specs read them from `tests/credentials.ts`. Set `BASE_URL=http://localhost:8000` with `E2E_USERNAME` and `E2E_PASSWORD` to run against the container instead; that resets the container user's board.

## Commands

- `npm run dev`: dev server (no backend, so sign in does not work there; use the backend or the container)
- `npm run build`: production build
- `npm run test:unit`: Vitest
- `npm run test:e2e`: Playwright
- `npm run lint`: ESLint
