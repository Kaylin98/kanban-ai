import json
import os

import pytest

from app import ai
from app.board import DEFAULT_BOARD

HISTORY = [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help?"},
]


@pytest.fixture
def fake_ai(monkeypatch):
    """Replaces the AI call. Set `.response` to the AIResponse dict to return;
    `.messages` records what was sent."""

    class Fake:
        response = {"reply": "Done.", "operations": []}
        messages = None

    def parse(messages, schema):
        Fake.messages = messages
        return schema.model_validate(Fake.response)

    monkeypatch.setattr(ai, "parse", parse)
    return Fake


def send(client, message="Hello"):
    return client.post("/api/chat", json={"message": message, "history": HISTORY})


def test_chat_requires_login(client, fake_ai):
    assert send(client).status_code == 401


def test_prompt_has_board_history_and_message(logged_in, fake_ai):
    send(logged_in, "What is in Review?")

    system, *history, last = fake_ai.messages
    assert system["role"] == "system"
    board_json = system["content"].split("The current board:\n")[1]
    assert json.loads(board_json) == DEFAULT_BOARD.model_dump()
    assert history == HISTORY
    assert last == {"role": "user", "content": "What is in Review?"}


def test_reply_only_leaves_board_unchanged(logged_in, fake_ai):
    fake_ai.response = {"reply": "You have 8 cards.", "operations": []}

    response = send(logged_in)

    assert response.json() == {"reply": "You have 8 cards.", "board": None}
    assert logged_in.get("/api/board").json() == DEFAULT_BOARD.model_dump()


def test_operations_update_and_save_board(logged_in, fake_ai):
    fake_ai.response = {
        "reply": "Updated.",
        "operations": [
            {"type": "create", "column_id": "col-review", "title": "New", "details": "Fresh"},
            {"type": "update", "card_id": "card-1", "title": "Edited", "details": "Changed"},
            {"type": "move", "card_id": "card-8", "column_id": "col-backlog", "position": 0},
            {"type": "move", "card_id": "card-5", "column_id": "col-progress", "position": 0},
            {"type": "delete", "card_id": "card-6"},
        ],
    }

    response = send(logged_in).json()

    board = response["board"]
    columns = {column["id"]: column["cardIds"] for column in board["columns"]}
    [new_id] = columns["col-review"]
    assert board["cards"][new_id] == {"id": new_id, "title": "New", "details": "Fresh"}
    assert board["cards"]["card-1"] == {"id": "card-1", "title": "Edited", "details": "Changed"}
    assert columns["col-backlog"] == ["card-8", "card-1", "card-2"]
    assert columns["col-progress"] == ["card-5", "card-4"]
    assert columns["col-done"] == ["card-7"]
    assert "card-6" not in board["cards"]
    assert response["reply"] == "Updated."
    assert logged_in.get("/api/board").json() == board


@pytest.mark.parametrize(
    "operation",
    [
        {"type": "update", "card_id": "card-missing", "title": "X", "details": ""},
        {"type": "move", "card_id": "card-missing", "column_id": "col-done", "position": 0},
        {"type": "move", "card_id": "card-1", "column_id": "col-missing", "position": 0},
        {"type": "create", "column_id": "col-missing", "title": "X", "details": ""},
        {"type": "delete", "card_id": "card-missing"},
    ],
)
def test_invalid_operation_leaves_board_unchanged(logged_in, fake_ai, operation, caplog):
    valid = {"type": "delete", "card_id": "card-1"}
    fake_ai.response = {"reply": "Done.", "operations": [valid, operation]}

    assert send(logged_in).status_code == 502
    assert logged_in.get("/api/board").json() == DEFAULT_BOARD.model_dump()
    assert "Rejected AI operations" in caplog.text
    assert repr(operation["type"]) in caplog.text


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set"
)
def test_live_add_card(logged_in):
    response = send(logged_in, 'Add a card called "Write release notes" to Backlog.')

    assert response.status_code == 200
    board = logged_in.get("/api/board").json()
    backlog = next(column for column in board["columns"] if column["id"] == "col-backlog")
    titles = [board["cards"][card_id]["title"] for card_id in backlog["cardIds"]]
    assert "Write release notes" in titles
