from contextlib import closing

import pytest

from app import db
from app.board import DEFAULT_BOARD


def updated_board() -> dict:
    """The default board with a renamed column, an edited card, a new card,
    a deleted card, and cards moved and reordered across columns."""
    board = DEFAULT_BOARD.model_dump()
    board["columns"][0]["title"] = "Ideas"
    board["cards"]["card-1"]["title"] = "Edited title"
    board["cards"]["card-new"] = {"id": "card-new", "title": "New", "details": "Fresh"}
    del board["cards"]["card-6"]
    board["columns"][0]["cardIds"] = ["card-2", "card-new"]
    board["columns"][3]["cardIds"] = []
    board["columns"][4]["cardIds"] = ["card-8", "card-1", "card-7"]
    return board


def test_init_db_creates_file_and_tables(tmp_path, monkeypatch):
    path = tmp_path / "missing" / "pm.db"
    monkeypatch.setattr(db, "DATABASE_PATH", path)

    db.init_db("user")

    assert path.exists()
    with closing(db.connect()) as conn:
        tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        users = [row["username"] for row in conn.execute("SELECT username FROM users")]
    assert tables == {"users", "boards", "columns", "cards"}
    assert users == ["user"]


@pytest.mark.parametrize("method", ["get", "put"])
def test_board_requires_login(client, method):
    response = client.request(method, "/api/board", json=DEFAULT_BOARD.model_dump())
    assert response.status_code == 401


def test_first_get_returns_default_board(logged_in):
    response = logged_in.get("/api/board")
    assert response.status_code == 200
    assert response.json() == DEFAULT_BOARD.model_dump()


def test_put_then_get_returns_saved_board(logged_in):
    board = updated_board()

    response = logged_in.put("/api/board", json=board)
    assert response.status_code == 200
    assert response.json() == board
    assert logged_in.get("/api/board").json() == board


def test_put_before_get_saves_board(logged_in):
    board = updated_board()
    assert logged_in.put("/api/board", json=board).status_code == 200
    assert logged_in.get("/api/board").json() == board


def test_board_survives_restart(logged_in):
    board = updated_board()
    logged_in.put("/api/board", json=board)

    with logged_in:  # runs startup again against the same database file
        assert logged_in.get("/api/board").json() == board


def invalid_boards():
    missing_field = DEFAULT_BOARD.model_dump()
    del missing_field["cards"]["card-1"]["details"]

    unknown_card = DEFAULT_BOARD.model_dump()
    unknown_card["columns"][0]["cardIds"].append("card-missing")

    orphan_card = DEFAULT_BOARD.model_dump()
    orphan_card["columns"][0]["cardIds"].remove("card-1")

    duplicate_card = DEFAULT_BOARD.model_dump()
    duplicate_card["columns"][1]["cardIds"].append("card-1")

    wrong_columns = DEFAULT_BOARD.model_dump()
    wrong_columns["columns"].pop()

    mismatched_id = DEFAULT_BOARD.model_dump()
    mismatched_id["cards"]["card-1"]["id"] = "card-2"

    return [missing_field, unknown_card, orphan_card, duplicate_card, wrong_columns, mismatched_id]


@pytest.mark.parametrize("board", invalid_boards())
def test_invalid_board_is_rejected(logged_in, board):
    assert logged_in.put("/api/board", json=board).status_code == 422
    assert logged_in.get("/api/board").json() == DEFAULT_BOARD.model_dump()


def test_boards_are_isolated_per_user(client):
    with closing(db.connect()) as conn, conn:
        other_id = conn.execute("INSERT INTO users (username) VALUES ('other')").lastrowid
    user_id = db.get_user_id("user")

    board = updated_board()
    db.save_board(user_id, DEFAULT_BOARD.model_validate(board))

    assert db.get_board(other_id) == DEFAULT_BOARD
    assert db.get_board(user_id).model_dump() == board
