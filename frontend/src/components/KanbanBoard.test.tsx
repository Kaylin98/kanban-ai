import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { saveBoard, sendChat } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";
import { defaultBoard } from "@/test/board";

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  saveBoard: vi.fn(),
  sendChat: vi.fn(),
}));

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

const renderBoard = () =>
  render(<KanbanBoard initialBoard={defaultBoard} onLogout={() => {}} />);

const lastSaved = (): BoardData => vi.mocked(saveBoard).mock.lastCall![0];

afterEach(() => {
  vi.mocked(saveBoard).mockClear();
  localStorage.clear();
});

describe("KanbanBoard", () => {
  it("renders the board it is given without saving", () => {
    render(
      <KanbanBoard
        initialBoard={{
          ...defaultBoard,
          columns: defaultBoard.columns.map((column) => ({ ...column, title: `${column.title} X` })),
        }}
        onLogout={() => {}}
      />
    );
    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    expect(screen.getAllByLabelText("Column title")[0]).toHaveValue("Backlog X");
    expect(screen.getByText("Align roadmap themes")).toBeInTheDocument();
    expect(saveBoard).not.toHaveBeenCalled();
  });

  it("renames a column and saves it", async () => {
    renderBoard();
    const input = within(getFirstColumn()).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
    expect(lastSaved().columns[0].title).toBe("New Name");
  });

  it("adds and removes a card and saves each change", async () => {
    renderBoard();
    const column = getFirstColumn();
    await userEvent.click(within(column).getByRole("button", { name: /add a card/i }));
    await userEvent.type(within(column).getByPlaceholderText(/card title/i), "New card");
    await userEvent.type(within(column).getByPlaceholderText(/details/i), "Notes");
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(within(column).getByText("New card")).toBeInTheDocument();
    const added = lastSaved();
    const newId = added.columns[0].cardIds[2];
    expect(added.columns[0].cardIds).toEqual(["card-1", "card-2", newId]);
    expect(added.cards[newId]).toEqual({ id: newId, title: "New card", details: "Notes" });

    await userEvent.click(within(column).getByRole("button", { name: /delete new card/i }));

    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
    expect(lastSaved()).toEqual(defaultBoard);
  });

  it("edits a card and saves it", async () => {
    renderBoard();
    const card = screen.getByTestId("card-card-1");
    await userEvent.click(within(card).getByRole("button", { name: /edit align roadmap themes/i }));

    const titleInput = within(card).getByLabelText("Card title");
    const detailsInput = within(card).getByLabelText("Card details");
    expect(titleInput).toHaveValue("Align roadmap themes");
    await userEvent.clear(titleInput);
    await userEvent.type(titleInput, "Edited title");
    await userEvent.clear(detailsInput);
    await userEvent.type(detailsInput, "Edited details");
    await userEvent.click(within(card).getByRole("button", { name: /save/i }));

    expect(within(card).getByText("Edited title")).toBeInTheDocument();
    expect(within(card).getByText("Edited details")).toBeInTheDocument();
    expect(within(card).queryByLabelText("Card title")).not.toBeInTheDocument();
    expect(saveBoard).toHaveBeenCalledTimes(1);
    expect(lastSaved().cards["card-1"]).toEqual({
      id: "card-1",
      title: "Edited title",
      details: "Edited details",
    });
  });

  it("shows the board from an AI reply without saving it again", async () => {
    const aiBoard: BoardData = {
      columns: defaultBoard.columns.map((column) =>
        column.id === "col-backlog" ? { ...column, cardIds: [...column.cardIds, "card-ai"] } : column
      ),
      cards: { ...defaultBoard.cards, "card-ai": { id: "card-ai", title: "From AI", details: "" } },
    };
    vi.mocked(sendChat).mockResolvedValue({ reply: "Added it.", board: aiBoard });
    renderBoard();

    await userEvent.click(screen.getByRole("button", { name: "Open AI assistant" }));
    await userEvent.type(screen.getByLabelText("Message"), "Add a card");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await within(getFirstColumn()).findByText("From AI")).toBeInTheDocument();
    expect(screen.getByText("Added it.")).toBeInTheDocument();
    expect(saveBoard).not.toHaveBeenCalled();
  });

  it("cancels editing a card without changes or saving", async () => {
    renderBoard();
    const card = screen.getByTestId("card-card-1");
    await userEvent.click(within(card).getByRole("button", { name: /edit align roadmap themes/i }));

    const titleInput = within(card).getByLabelText("Card title");
    await userEvent.clear(titleInput);
    await userEvent.type(titleInput, "Discarded");
    await userEvent.click(within(card).getByRole("button", { name: /cancel/i }));

    expect(within(card).getByText("Align roadmap themes")).toBeInTheDocument();
    expect(within(card).queryByText("Discarded")).not.toBeInTheDocument();
    expect(saveBoard).not.toHaveBeenCalled();
  });
});
