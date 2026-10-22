import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from app.board import DEFAULT_BOARD, Board, Card, Column

DATABASE_PATH = Path(
    os.environ.get("DATABASE_PATH", Path(__file__).parents[2] / "data" / "pm.db")
)

SCHEMA = """
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
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(username: str) -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect()) as conn, conn:
        conn.executescript(SCHEMA)
        conn.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))


def get_user_id(username: str) -> int:
    with closing(connect()) as conn:
        return conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()["id"]


def get_board(user_id: int) -> Board:
    with closing(connect()) as conn, conn:
        board_id = _get_or_create_board_id(conn, user_id)
        columns = conn.execute(
            "SELECT id, key, title FROM columns WHERE board_id = ? ORDER BY position",
            (board_id,),
        ).fetchall()
        cards = conn.execute(
            "SELECT cards.column_id, cards.key, cards.title, cards.details FROM cards"
            " JOIN columns ON columns.id = cards.column_id"
            " WHERE columns.board_id = ? ORDER BY cards.position",
            (board_id,),
        ).fetchall()
    return Board(
        columns=[
            Column(
                id=column["key"],
                title=column["title"],
                cardIds=[card["key"] for card in cards if card["column_id"] == column["id"]],
            )
            for column in columns
        ],
        cards={
            card["key"]: Card(id=card["key"], title=card["title"], details=card["details"])
            for card in cards
        },
    )


def save_board(user_id: int, board: Board) -> None:
    with closing(connect()) as conn, conn:
        board_id = _get_or_create_board_id(conn, user_id)
        for column in board.columns:
            conn.execute(
                "UPDATE columns SET title = ? WHERE board_id = ? AND key = ?",
                (column.title, board_id, column.id),
            )
        conn.execute(
            "DELETE FROM cards WHERE column_id IN (SELECT id FROM columns WHERE board_id = ?)",
            (board_id,),
        )
        _insert_cards(conn, board_id, board)
        conn.execute(
            "UPDATE boards SET updated_at = ? WHERE id = ?", (_now(), board_id)
        )


def _get_or_create_board_id(conn: sqlite3.Connection, user_id: int) -> int:
    row = conn.execute("SELECT id FROM boards WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        return row["id"]
    board_id = conn.execute(
        "INSERT INTO boards (user_id, updated_at) VALUES (?, ?)", (user_id, _now())
    ).lastrowid
    for position, column in enumerate(DEFAULT_BOARD.columns):
        conn.execute(
            "INSERT INTO columns (board_id, key, title, position) VALUES (?, ?, ?, ?)",
            (board_id, column.id, column.title, position),
        )
    _insert_cards(conn, board_id, DEFAULT_BOARD)
    return board_id


def _insert_cards(conn: sqlite3.Connection, board_id: int, board: Board) -> None:
    column_ids = {
        row["key"]: row["id"]
        for row in conn.execute("SELECT id, key FROM columns WHERE board_id = ?", (board_id,))
    }
    for column in board.columns:
        for position, card_id in enumerate(column.cardIds):
            card = board.cards[card_id]
            conn.execute(
                "INSERT INTO cards (column_id, key, title, details, position) VALUES (?, ?, ?, ?, ?)",
                (column_ids[column.id], card.id, card.title, card.details, position),
            )


def _now() -> str:
    return datetime.now(UTC).isoformat()
