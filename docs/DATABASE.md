# Database

SQLite, accessed with the Python standard library `sqlite3`. Four tables: `users`, `boards`, `columns` and `cards`.

## Approach

Columns and cards are stored as rows in their own tables. The API still sends and receives the board in the `BoardData` shape the frontend uses (`frontend/src/lib/kanban.ts`), so the backend converts between rows and that shape. The frontend is unaware of the tables. Validation happens in Pydantic models that mirror `BoardData` before anything is written.

## Schema

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS boards (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS columns (
    id INTEGER PRIMARY KEY,
    board_id INTEGER NOT NULL REFERENCES boards(id),
    key TEXT NOT NULL,
    title TEXT NOT NULL,
    position INTEGER NOT NULL,
    UNIQUE (board_id, key)
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY,
    column_id INTEGER NOT NULL REFERENCES columns(id),
    key TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT NOT NULL,
    position INTEGER NOT NULL
);
```

- `users` has no password column. Credentials stay hardcoded for the MVP; the table exists so boards belong to a user and more users can be added later.
- `boards.user_id` is unique, so each user has at most one board. Dropping that constraint is all it takes to allow several boards per user later.
- `boards.updated_at` is an ISO 8601 UTC timestamp, set on every save.
- `key` holds the id the frontend uses (`col-backlog`, `card-1`). Every user's default board has the same keys, so keys can't be primary keys. The integer `id` is internal and never leaves the backend.
- `position` sets the order: column order on the board, and card order within a column.
- Card keys must be unique within a board. The Pydantic board model checks this before saving.
- Every connection runs `PRAGMA foreign_keys = ON`, since SQLite doesn't enforce foreign keys by default.

## Example

Rows for a board with `boards.id = 1`:

`columns`

| id | board_id | key           | title       | position |
|----|----------|---------------|-------------|----------|
| 1  | 1        | col-backlog   | Backlog     | 0        |
| 2  | 1        | col-discovery | Discovery   | 1        |
| 3  | 1        | col-progress  | In Progress | 2        |
| 4  | 1        | col-review    | Review      | 3        |
| 5  | 1        | col-done      | Done        | 4        |

`cards`

| id | column_id | key    | title                    | details                                                    | position |
|----|-----------|--------|--------------------------|------------------------------------------------------------|----------|
| 1  | 1         | card-1 | Align roadmap themes     | Draft quarterly themes with impact statements and metrics. | 0        |
| 2  | 1         | card-2 | Gather customer signals  | Review support tags, sales notes, and churn feedback.      | 1        |
| 3  | 2         | card-3 | Prototype analytics view | Sketch initial dashboard layout and key drill-downs.       | 0        |

The `BoardData` the API returns for those rows:

```json
{
  "columns": [
    { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"] },
    { "id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"] },
    { "id": "col-progress", "title": "In Progress", "cardIds": [] },
    { "id": "col-review", "title": "Review", "cardIds": [] },
    { "id": "col-done", "title": "Done", "cardIds": [] }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Align roadmap themes",
      "details": "Draft quarterly themes with impact statements and metrics."
    },
    "card-2": {
      "id": "card-2",
      "title": "Gather customer signals",
      "details": "Review support tags, sales notes, and churn feedback."
    },
    "card-3": {
      "id": "card-3",
      "title": "Prototype analytics view",
      "details": "Sketch initial dashboard layout and key drill-downs."
    }
  }
}
```

## Mapping

- **Read**: select the board's columns ordered by `position`, then their cards ordered by `position`. Each column's `cardIds` comes from its cards, and every card goes into the `cards` dict.
- **Write** (`PUT /api/board`, in one transaction): update column titles by `key`, delete all of the board's cards, and insert the cards again with `column_id` and `position` taken from the payload. Then set `boards.updated_at`. Columns are fixed, so after the board is created they are only renamed, never added or removed.
- **Create**: insert the `boards` row, the 5 default columns and the default cards.

## Lifecycle

1. On startup the backend creates the database file and its parent directory if they are missing, then runs the `CREATE TABLE IF NOT EXISTS` statements.
2. It inserts the `user` row if it isn't there (`INSERT OR IGNORE`).
3. On a user's first `GET /api/board`, if they have no board, the backend creates one from the default board. The default board moves from the frontend's `initialData` to the backend in Part 7.
4. `PUT /api/board` validates the board and writes it as described under Mapping.

## Location

The file path comes from the `DATABASE_PATH` env var, defaulting to `data/pm.db` in the project root. In the container the project root is `/app`, so the default resolves to `/app/data/pm.db`, which is on the `pm-data` volume that the start scripts mount. Board data therefore survives container restarts with no extra configuration. Tests set `DATABASE_PATH` to a temporary file.
