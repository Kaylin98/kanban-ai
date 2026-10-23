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
- `src/lib/api.ts`: fetch helpers for the backend (`me`, `login`, `logout`, `getBoard`, `saveBoard`). `saveBoard` queues saves so they reach the server in order.
- `src/components/LoginForm.tsx`: username/password form; shows an error when the credentials are rejected.
- `src/app/globals.css`: color scheme as CSS variables (`--accent-yellow`, `--primary-blue`, `--secondary-purple`, `--navy-dark`, `--gray-text`, plus surface, stroke and shadow tokens).
- `src/lib/kanban.ts`: the `Card`, `Column` and `BoardData` types, `moveCard` (pure function that reorders or moves cards) and `createId`.
- `src/components/KanbanBoard.tsx`: owns the board state (starting from the `initialBoard` prop) and `DndContext`. Handles drag end, column rename, and add, edit and delete card. An effect saves the board with `saveBoard` after every change, skipping the intermediate states while a card is dragged. Takes an `onLogout` prop for the header's Log out button.
- `src/components/KanbanColumn.tsx`: droppable column with an inline title input for renaming, its sortable cards, and a `NewCardForm`.
- `src/components/KanbanCard.tsx`: sortable card with Edit and Remove buttons. Edit switches to an inline title/details form; drag attributes and listeners are not attached while editing.
- `src/components/KanbanCardPreview.tsx`: card shown in the `DragOverlay` while dragging.
- `src/components/NewCardForm.tsx`: toggleable form to add a card (title required, details optional).

## Data shape

```ts
BoardData = { columns: { id, title, cardIds[] }[], cards: Record<id, { id, title, details }> }
```

The columns are fixed (no adding or deleting), but they can be renamed. Card order is the order of `cardIds` in each column.

## Tests

- `src/lib/kanban.test.ts`: `moveCard` reordering and moving between columns.
- `src/test/board.ts`: `defaultBoard`, matching the backend's `DEFAULT_BOARD`. Used by the unit tests and to reset the board in the e2e tests.
- `src/components/KanbanBoard.test.tsx`: renders the given board, and checks what `saveBoard` (mocked) receives when renaming a column, adding, removing and editing a card, and that cancelling an edit saves nothing.
- `src/app/page.test.tsx`: login form without a session, loading state then the board from the API, error on wrong credentials, sign in and out (fetch is stubbed).
- `tests/auth.spec.ts`: Playwright sign in, reload, sign out, and wrong credentials.
- `tests/kanban.spec.ts`: Playwright tests that load the board, add, edit and delete a card, rename a column, drag a card between columns, and check that every type of change survives a reload. `beforeEach` signs in via `/api/login` and resets the board to `defaultBoard`.
- Playwright needs the backend, so by default it runs `npm run build` and serves `out/` with uvicorn on port 8001 (requires uv), with the database in the temp directory (`pm-e2e.db`). Set `BASE_URL=http://localhost:8000` to run against the container instead; that resets the container user's board.

## Commands

- `npm run dev`: dev server (no backend, so sign in does not work there; use the backend or the container)
- `npm run build`: production build
- `npm run test:unit`: Vitest
- `npm run test:e2e`: Playwright
- `npm run lint`: ESLint
