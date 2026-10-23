import json
import os
from types import SimpleNamespace

import httpx2
import pytest
from openai import APIConnectionError, LengthFinishReasonError
from pydantic import ValidationError

from app import ai
from app.board import DEFAULT_BOARD

HISTORY = [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help?"},
]


@pytest.fixture
def fake_ai(monkeypatch):
    """Replaces the AI call. Set `.responses` to the AIResponse dicts to return (or
    exceptions to raise), one per call (the last one repeats); `.calls` records the
    messages sent on each call."""

    class Fake:
        responses = [{"reply": "Done.", "operations": []}]
        calls = []

    def parse(messages, schema):
        Fake.calls.append(list(messages))
        response = Fake.responses[min(len(Fake.calls), len(Fake.responses)) - 1]
        if isinstance(response, Exception):
            raise response
        return schema.model_validate(response)

    monkeypatch.setattr(ai, "parse", parse)
    return Fake


def send(client, message="Hello"):
    return client.post("/api/chat", json={"message": message, "history": HISTORY})


def test_chat_requires_login(client, fake_ai):
    assert send(client).status_code == 401


def test_prompt_has_board_history_and_message(logged_in, fake_ai):
    send(logged_in, "What is in Review?")

    [messages] = fake_ai.calls
    system, *history, last = messages
    assert system["role"] == "system"
    board_json = system["content"].split("The current board:\n")[1]
    assert json.loads(board_json) == DEFAULT_BOARD.model_dump()
    assert history == HISTORY
    assert last == {"role": "user", "content": "What is in Review?"}


def test_reply_only_leaves_board_unchanged(logged_in, fake_ai):
    fake_ai.responses = [{"reply": "You have 8 cards.", "operations": []}]

    response = send(logged_in)

    assert response.json() == {"reply": "You have 8 cards.", "board": None}
    assert logged_in.get("/api/board").json() == DEFAULT_BOARD.model_dump()


def test_operations_update_and_save_board(logged_in, fake_ai):
    fake_ai.responses = [{
        "reply": "Updated.",
        "operations": [
            {"action": "create", "column_id": "col-review", "title": "New", "details": "Fresh"},
            {"action": "update", "card_id": "card-1", "title": "Edited", "details": "Changed"},
            {"action": "move", "card_id": "card-8", "column_id": "col-backlog", "position": 0},
            {"action": "move", "card_id": "card-5", "column_id": "col-progress", "position": 0},
            {"action": "delete", "card_id": "card-6"},
        ],
    }]

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
        {"action": "update", "card_id": "card-missing", "title": "X", "details": ""},
        {"action": "move", "card_id": "card-missing", "column_id": "col-done", "position": 0},
        {"action": "move", "card_id": "card-1", "column_id": "col-missing", "position": 0},
        {"action": "create", "column_id": "col-missing", "title": "X", "details": ""},
        {"action": "delete", "card_id": "card-missing"},
        {"action": "create", "column_id": "col-done", "title": "gather customer signals", "details": ""},
    ],
)
def test_invalid_operation_twice_leaves_board_unchanged(logged_in, fake_ai, operation, caplog):
    valid = {"action": "delete", "card_id": "card-1"}
    fake_ai.responses = [{"reply": "Done.", "operations": [valid, operation]}]

    assert send(logged_in).status_code == 502
    assert len(fake_ai.calls) == 2
    assert logged_in.get("/api/board").json() == DEFAULT_BOARD.model_dump()
    assert "Rejected AI operations on attempt 2" in caplog.text
    assert repr(operation["action"]) in caplog.text


def test_move_all_cards_to_done_moves_instead_of_copying(logged_in, fake_ai):
    # The model first copies every card into Done (the bug), then moves them on the retry.
    cards = DEFAULT_BOARD.cards.values()
    fake_ai.responses = [
        {
            "reply": "Moved everything to Done.",
            "operations": [
                {"action": "create", "column_id": "col-done", "title": card.title, "details": card.details}
                for card in cards
            ],
        },
        {
            "reply": "Moved everything to Done.",
            "operations": [
                {"action": "move", "card_id": card.id, "column_id": "col-done", "position": 0}
                for card in cards
            ],
        },
    ]

    board = send(logged_in, "Move all cards to Done").json()["board"]

    correction = fake_ai.calls[1][-1]["content"]
    assert "already exists as card-1" in correction
    assert "use a move operation" in correction
    assert board["cards"] == DEFAULT_BOARD.model_dump()["cards"]
    columns = {column["id"]: column["cardIds"] for column in board["columns"]}
    assert sorted(columns.pop("col-done")) == sorted(DEFAULT_BOARD.cards)
    assert all(card_ids == [] for card_ids in columns.values())


def test_invalid_operation_is_corrected_on_retry(logged_in, fake_ai):
    create = {"action": "create", "column_id": "col-done", "title": "New", "details": ""}
    invalid = {"action": "move", "card_id": "new-card-1", "column_id": "col-done", "position": 0}
    fake_ai.responses = [
        {"reply": "Added.", "operations": [create, invalid]},
        {"reply": "Added.", "operations": [create]},
    ]

    response = send(logged_in).json()

    first, retry = fake_ai.calls
    rejected, correction = retry[len(first):]
    assert json.loads(rejected["content"]) == fake_ai.responses[0]
    assert "card new-card-1 does not exist" in correction["content"]
    done = next(column for column in response["board"]["columns"] if column["id"] == "col-done")
    assert done["cardIds"][:2] == ["card-7", "card-8"]
    assert len(done["cardIds"]) == 3
    assert logged_in.get("/api/board").json() == response["board"]


@pytest.mark.parametrize(
    "error",
    [
        LengthFinishReasonError(completion=SimpleNamespace(usage=None)),
        APIConnectionError(request=httpx2.Request("POST", "https://openrouter.ai/api/v1")),
        ValidationError.from_exception_data("AIResponse", []),
    ],
    ids=["cut-off", "connection", "invalid-json"],
)
def test_ai_failure_returns_502(logged_in, fake_ai, error, caplog):
    fake_ai.responses = [error]

    response = send(logged_in)

    assert response.status_code == 502
    assert len(fake_ai.calls) == 1
    assert logged_in.get("/api/board").json() == DEFAULT_BOARD.model_dump()
    assert "AI call failed" in caplog.text


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


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set"
)
def test_live_rename_card(logged_in):
    response = send(logged_in, 'Rename the "Align roadmap themes" card to "Roadmap themes v2".')

    assert response.status_code == 200
    card = logged_in.get("/api/board").json()["cards"]["card-1"]
    assert card["title"] == "Roadmap themes v2"
