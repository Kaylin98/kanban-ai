from pydantic import BaseModel, model_validator

# The columns are fixed: they can be renamed but not added, removed or reordered.
COLUMN_IDS = ["col-backlog", "col-discovery", "col-progress", "col-review", "col-done"]


class Card(BaseModel):
    id: str
    title: str
    details: str


class Column(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class Board(BaseModel):
    """Mirrors `BoardData` in frontend/src/lib/kanban.ts."""

    columns: list[Column]
    cards: dict[str, Card]

    @model_validator(mode="after")
    def check_consistency(self):
        if [column.id for column in self.columns] != COLUMN_IDS:
            raise ValueError(f"Columns must be {COLUMN_IDS} in that order")
        if any(key != card.id for key, card in self.cards.items()):
            raise ValueError("Each card must be stored under its own id")
        placed = [card_id for column in self.columns for card_id in column.cardIds]
        if len(placed) != len(set(placed)) or set(placed) != set(self.cards):
            raise ValueError("Every card must be in exactly one column")
        return self


def _card(id: str, title: str, details: str) -> Card:
    return Card(id=id, title=title, details=details)


DEFAULT_BOARD = Board(
    columns=[
        Column(id="col-backlog", title="Backlog", cardIds=["card-1", "card-2"]),
        Column(id="col-discovery", title="Discovery", cardIds=["card-3"]),
        Column(id="col-progress", title="In Progress", cardIds=["card-4", "card-5"]),
        Column(id="col-review", title="Review", cardIds=["card-6"]),
        Column(id="col-done", title="Done", cardIds=["card-7", "card-8"]),
    ],
    cards={
        card.id: card
        for card in [
            _card("card-1", "Align roadmap themes", "Draft quarterly themes with impact statements and metrics."),
            _card("card-2", "Gather customer signals", "Review support tags, sales notes, and churn feedback."),
            _card("card-3", "Prototype analytics view", "Sketch initial dashboard layout and key drill-downs."),
            _card("card-4", "Refine status language", "Standardize column labels and tone across the board."),
            _card("card-5", "Design card layout", "Add hierarchy and spacing for scanning dense lists."),
            _card("card-6", "QA micro-interactions", "Verify hover, focus, and loading states."),
            _card("card-7", "Ship marketing page", "Final copy approved and asset pack delivered."),
            _card("card-8", "Close onboarding sprint", "Document release notes and share internally."),
        ]
    },
)
