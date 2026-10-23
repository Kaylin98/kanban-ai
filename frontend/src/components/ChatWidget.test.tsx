import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatWidget } from "@/components/ChatWidget";
import { ChatRequestError, sendChat } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  sendChat: vi.fn(),
}));

const toggle = (name: string) => userEvent.click(screen.getByRole("button", { name }));

const renderOpen = async (onBoardUpdate: (board: BoardData) => void) => {
  render(<ChatWidget onBoardUpdate={onBoardUpdate} />);
  await toggle("Open AI assistant");
};

const send = async (message: string) => {
  await userEvent.type(screen.getByLabelText("Message"), message);
  await userEvent.click(screen.getByRole("button", { name: "Send" }));
};

afterEach(() => {
  vi.mocked(sendChat).mockReset();
  localStorage.clear();
});

describe("ChatWidget", () => {
  it("starts minimized and remembers whether it is open", async () => {
    const { unmount } = render(<ChatWidget onBoardUpdate={() => {}} />);
    expect(screen.getByLabelText("Message")).not.toBeVisible();

    await toggle("Open AI assistant");
    expect(screen.getByLabelText("Message")).toBeVisible();
    unmount();

    render(<ChatWidget onBoardUpdate={() => {}} />);
    expect(screen.getByLabelText("Message")).toBeVisible();
  });

  it("keeps the conversation while minimized", async () => {
    vi.mocked(sendChat).mockResolvedValue({ reply: "Hello.", board: null });
    await renderOpen(() => {});

    await send("Hi");
    await screen.findByText("Hello.");
    await toggle("Minimize AI assistant");
    expect(screen.getByLabelText("Message")).not.toBeVisible();
    await toggle("Open AI assistant");

    expect(screen.getByText("Hi")).toBeVisible();
    expect(screen.getByText("Hello.")).toBeVisible();
  });

  it("shows the message and the reply, and sends the history with the next message", async () => {
    vi.mocked(sendChat).mockResolvedValue({ reply: "You have 8 cards.", board: null });
    await renderOpen(() => {});

    await send("How many cards?");

    expect(screen.getByText("How many cards?")).toBeInTheDocument();
    expect(await screen.findByText("You have 8 cards.")).toBeInTheDocument();
    expect(screen.getByLabelText("Message")).toHaveValue("");
    expect(sendChat).toHaveBeenCalledWith("How many cards?", []);

    await send("Thanks{Enter}");

    expect(sendChat).toHaveBeenLastCalledWith("Thanks", [
      { role: "user", content: "How many cards?" },
      { role: "assistant", content: "You have 8 cards." },
    ]);
  });

  it("shows a loading state while waiting for the reply", async () => {
    let resolve!: (value: { reply: string; board: null }) => void;
    vi.mocked(sendChat).mockReturnValue(new Promise((r) => (resolve = r)));
    await renderOpen(() => {});

    await send("Hello");

    expect(screen.getByText("Thinking...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sending..." })).toBeDisabled();

    resolve({ reply: "Hi there.", board: null });

    expect(await screen.findByText("Hi there.")).toBeInTheDocument();
    expect(screen.queryByText("Thinking...")).not.toBeInTheDocument();
  });

  it("passes a changed board to onBoardUpdate", async () => {
    const board = { columns: [], cards: {} };
    vi.mocked(sendChat).mockResolvedValue({ reply: "Done.", board });
    const onBoardUpdate = vi.fn();
    await renderOpen(onBoardUpdate);

    await send("Clear it");

    await screen.findByText("Done.");
    expect(onBoardUpdate).toHaveBeenCalledWith(board);
  });

  it.each([
    [502, "The assistant had trouble, try again."],
    [500, "The assistant could not complete that request. Try again."],
  ])("shows an error for a %i and restores the message", async (status, message) => {
    vi.mocked(sendChat).mockRejectedValue(new ChatRequestError(status));
    await renderOpen(() => {});

    await send("Move everything");

    expect(await screen.findByRole("alert")).toHaveTextContent(message);
    expect(screen.getByLabelText("Message")).toHaveValue("Move everything");
    expect(screen.queryByText("Move everything", { selector: "div" })).not.toBeInTheDocument();
  });
});
