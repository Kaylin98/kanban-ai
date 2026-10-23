from typing import Literal
from uuid import uuid4

from pydantic import BaseModel

from app.board import Board, Card


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message]


# Each operation's discriminator is `action` because it sorts before the other keys.
# Providers can generate Structured Output keys in alphabetical order, and a later
# discriminator (it was `type`) let the key order pick the operation: an update
# that started with "card_id" could only continue as a delete.
class CreateCard(BaseModel):
    action: Literal["create"]
    column_id: str
    title: str
    details: str


class UpdateCard(BaseModel):
    action: Literal["update"]
    card_id: str
    title: str
    details: str


class MoveCard(BaseModel):
    action: Literal["move"]
    card_id: str
    column_id: str
    position: int


class DeleteCard(BaseModel):
    action: Literal["delete"]
    card_id: str


class AIResponse(BaseModel):
    reply: str
    operations: list[CreateCard | UpdateCard | MoveCard | DeleteCard]


SYSTEM_PROMPT = """You are the assistant for a Kanban board app. You help the user plan and \
manage their project, and you can change cards on their board.

The board is JSON: "columns" is the ordered list of columns, each with an id, a title and \
"cardIds" (the cards in it, top to bottom). "cards" maps each card id to its title and details. \
The columns are fixed: you cannot add, remove or rename them.

To change the board, return operations, applied in order:
- create: add a new card at the bottom of column_id. The server assigns its id, so never \
refer to a new card in another operation
- update: set a card's title and details (repeat the current value for any you keep)
- move: move a card to column_id at position (0 is the top)
- delete: remove a card
To change a card's column, always use move with the existing card id, never create a copy. \
Use the exact column and card ids from the board below. Return operations only for the \
user's latest message: earlier messages are already applied to the board below. Never repeat \
an operation. Return an empty operations list when the user does not ask for a change. \
Always write a short reply to the user saying what you did, in plain text: no Markdown, \
so no **bold**, headings or tables.

The current board:
{board}"""


def build_messages(board: Board, request: ChatRequest) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT.format(board=board.model_dump_json())},
        *(message.model_dump() for message in request.history),
        {"role": "user", "content": request.message},
    ]


def correction_messages(response: AIResponse, error: ValueError) -> list[dict]:
    """Messages that show the model its rejected response and ask it to correct it."""
    return [
        {"role": "assistant", "content": response.model_dump_json()},
        {
            "role": "user",
            "content": f"Your operations were rejected, so nothing was applied: {error}. "
            "Return the full corrected list of operations for my previous message.",
        },
    ]


def apply_operations(board: Board, operations: list) -> Board:
    """Returns a new board with the operations applied. Raises ValueError for unknown ids."""
    data = board.model_dump()
    cards = data["cards"]

    def check_card(card_id: str) -> None:
        if card_id not in cards:
            raise ValueError(
                f"card {card_id} does not exist. Use a create operation to add a new card, "
                "and never refer to a new card in another operation"
            )

    def card_ids(column_id: str) -> list[str]:
        for column in data["columns"]:
            if column["id"] == column_id:
                return column["cardIds"]
        column_ids = ", ".join(column["id"] for column in data["columns"])
        raise ValueError(f"column {column_id} does not exist. The columns are {column_ids}")

    def take_card(card_id: str) -> None:
        check_card(card_id)
        for column in data["columns"]:
            if card_id in column["cardIds"]:
                column["cardIds"].remove(card_id)

    for op in operations:
        match op:
            case CreateCard():
                # Catches the model copying cards into a column instead of moving them.
                for existing in cards.values():
                    if existing["title"].casefold() == op.title.casefold():
                        raise ValueError(
                            f'card "{op.title}" already exists as {existing["id"]}. To put an '
                            "existing card in another column, use a move operation with its "
                            "card_id; never create a copy"
                        )
                card = Card(id=f"card-{uuid4().hex[:12]}", title=op.title, details=op.details)
                card_ids(op.column_id).append(card.id)
                cards[card.id] = card.model_dump()
            case UpdateCard():
                check_card(op.card_id)
                cards[op.card_id].update(title=op.title, details=op.details)
            case MoveCard():
                target = card_ids(op.column_id)
                take_card(op.card_id)
                target.insert(op.position, op.card_id)
            case DeleteCard():
                take_card(op.card_id)
                del cards[op.card_id]
    return Board.model_validate(data)
