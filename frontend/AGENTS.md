# Frontend

A Next.js frontend for the Kanban board. Right now it is a client-only demo: all state lives in memory, there is no backend, and the board resets on reload.

## Stack

- Next.js 16 (App Router), React 19, TypeScript
- Tailwind CSS 4, used through `@tailwindcss/postcss`
- @dnd-kit (core, sortable, utilities) for drag and drop
- Vitest + Testing Library (jsdom) for unit tests, Playwright for e2e

## Structure

- `src/app/layout.tsx`: root layout. Loads the Space Grotesk (display) and Manrope (body) fonts as CSS variables.
- `src/app/page.tsx`: renders `KanbanBoard`.
- `src/app/globals.css`: color scheme as CSS variables (`--accent-yellow`, `--primary-blue`, `--secondary-purple`, `--navy-dark`, `--gray-text`, plus surface, stroke and shadow tokens).
- `src/lib/kanban.ts`: the `Card`, `Column` and `BoardData` types, the seed `initialData` (5 columns, 8 cards), `moveCard` (pure function that reorders or moves cards) and `createId`.
- `src/components/KanbanBoard.tsx`: owns the board state and `DndContext`. Handles drag end, column rename, add card and delete card.
- `src/components/KanbanColumn.tsx`: droppable column with an inline title input for renaming, its sortable cards, and a `NewCardForm`.
- `src/components/KanbanCard.tsx`: sortable card with a Remove button.
- `src/components/KanbanCardPreview.tsx`: card shown in the `DragOverlay` while dragging.
- `src/components/NewCardForm.tsx`: toggleable form to add a card (title required, details optional).

## Data shape

```ts
BoardData = { columns: { id, title, cardIds[] }[], cards: Record<id, { id, title, details }> }
```

The columns are fixed (no adding or deleting), but they can be renamed. Card order is the order of `cardIds` in each column.

## Gaps

- Cards cannot be edited yet, only added and deleted.
- No persistence, auth or API calls.

## Tests

- `src/lib/kanban.test.ts`: `moveCard` reordering and moving between columns.
- `src/components/KanbanBoard.test.tsx`: renders the columns, renames a column, adds and removes a card.
- `tests/kanban.spec.ts`: Playwright tests that load the board, add a card and drag a card between columns. They run against `npm run dev` on port 3000.

## Commands

- `npm run dev`: dev server
- `npm run build`: production build
- `npm run test:unit`: Vitest
- `npm run test:e2e`: Playwright
- `npm run lint`: ESLint
