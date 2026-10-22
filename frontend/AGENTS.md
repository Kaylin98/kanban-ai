# Frontend

A Next.js frontend for the Kanban board, built as a static export (`output: "export"` writes to `out/`), which the FastAPI backend serves at `/`. Sign in goes through the backend; the board state still lives in memory and resets on reload.

## Stack

- Next.js 16 (App Router), React 19, TypeScript
- Tailwind CSS 4, used through `@tailwindcss/postcss`
- @dnd-kit (core, sortable, utilities) for drag and drop
- Vitest + Testing Library (jsdom) for unit tests, Playwright for e2e

## Structure

- `src/app/layout.tsx`: root layout. Loads the Space Grotesk (display) and Manrope (body) fonts as CSS variables.
- `src/app/page.tsx`: calls `/api/me` on load, then shows `LoginForm` (no session) or `KanbanBoard` (with a logout handler). Renders nothing while checking.
- `src/lib/api.ts`: fetch helpers for the backend (`me`, `login`, `logout`).
- `src/components/LoginForm.tsx`: username/password form; shows an error when the credentials are rejected.
- `src/app/globals.css`: color scheme as CSS variables (`--accent-yellow`, `--primary-blue`, `--secondary-purple`, `--navy-dark`, `--gray-text`, plus surface, stroke and shadow tokens).
- `src/lib/kanban.ts`: the `Card`, `Column` and `BoardData` types, the seed `initialData` (5 columns, 8 cards), `moveCard` (pure function that reorders or moves cards) and `createId`.
- `src/components/KanbanBoard.tsx`: owns the board state and `DndContext`. Handles drag end, column rename, and add, edit and delete card. Takes an `onLogout` prop for the header's Log out button.
- `src/components/KanbanColumn.tsx`: droppable column with an inline title input for renaming, its sortable cards, and a `NewCardForm`.
- `src/components/KanbanCard.tsx`: sortable card with Edit and Remove buttons. Edit switches to an inline title/details form; drag attributes and listeners are not attached while editing.
- `src/components/KanbanCardPreview.tsx`: card shown in the `DragOverlay` while dragging.
- `src/components/NewCardForm.tsx`: toggleable form to add a card (title required, details optional).

## Data shape

```ts
BoardData = { columns: { id, title, cardIds[] }[], cards: Record<id, { id, title, details }> }
```

The columns are fixed (no adding or deleting), but they can be renamed. Card order is the order of `cardIds` in each column.

## Gaps

- No persistence: the board is not saved to the backend yet.

## Tests

- `src/lib/kanban.test.ts`: `moveCard` reordering and moving between columns.
- `src/components/KanbanBoard.test.tsx`: renders the columns, renames a column, adds and removes a card, edits a card, cancels an edit.
- `src/app/page.test.tsx`: login form without a session, board with a session, error on wrong credentials, sign in and out (fetch is stubbed).
- `tests/auth.spec.ts`: Playwright sign in, reload, sign out, and wrong credentials.
- `tests/kanban.spec.ts`: Playwright tests (signed in via `/api/login` in `beforeEach`) that load the board, add, edit and delete a card, rename a column, and drag a card between columns.
- Playwright needs the backend, so by default it runs `npm run build` and serves `out/` with uvicorn on port 8001 (requires uv). Set `BASE_URL=http://localhost:8000` to run against the container instead.

## Commands

- `npm run dev`: dev server (no backend, so sign in does not work there; use the backend or the container)
- `npm run build`: production build
- `npm run test:unit`: Vitest
- `npm run test:e2e`: Playwright
- `npm run lint`: ESLint
