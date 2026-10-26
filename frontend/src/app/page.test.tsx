import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "@/app/page";
import { defaultBoard } from "@/test/board";

// The board the fake API serves, with a renamed column so tests can tell it came from the API.
const storedBoard = {
  ...defaultBoard,
  columns: [{ ...defaultBoard.columns[0], title: "From API" }, ...defaultBoard.columns.slice(1)],
};

// Fakes the backend API: a session cookie stands in as `signedIn`. The board
// response waits for `boardReady`, which resolves immediately by default.
// Signing in with "limited" as the password answers as the rate limit would.
const mockApi = (signedIn: boolean, boardReady = Promise.resolve()) => {
  vi.stubGlobal("fetch", async (url: string, init?: RequestInit) => {
    if (url === "/api/login") {
      const { password } = JSON.parse(init!.body as string);
      signedIn = password === "password";
      const status = signedIn ? 200 : password === "limited" ? 429 : 401;
      return Response.json({}, { status });
    }
    if (url === "/api/logout") {
      signedIn = false;
      return Response.json({});
    }
    if (url === "/api/board") {
      await boardReady;
      return Response.json(storedBoard);
    }
    return signedIn
      ? Response.json({ username: "user" })
      : Response.json({}, { status: 401 });
  });
};

const signIn = async (password: string) => {
  await userEvent.type(await screen.findByLabelText("Username"), "user");
  await userEvent.type(screen.getByLabelText("Password"), password);
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Home", () => {
  it("shows the login form without a session", async () => {
    mockApi(false);
    render(<Home />);
    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Kanban Studio" })).not.toBeInTheDocument();
  });

  it("shows a loading state, then the board from the API", async () => {
    const board = Promise.withResolvers<void>();
    mockApi(true, board.promise);
    render(<Home />);
    expect(await screen.findByText("Loading board...")).toBeInTheDocument();
    board.resolve();
    expect(await screen.findByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
    expect(screen.getAllByLabelText("Column title")[0]).toHaveValue("From API");
  });

  it("shows an error for wrong credentials", async () => {
    mockApi(false);
    render(<Home />);
    await signIn("wrong");
    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid/i);
    expect(screen.queryByRole("heading", { name: "Kanban Studio" })).not.toBeInTheDocument();
  });

  it("shows an error when sign-in attempts are rate limited", async () => {
    mockApi(false);
    render(<Home />);
    await signIn("limited");
    expect(await screen.findByRole("alert")).toHaveTextContent(/too many sign-in attempts/i);
  });

  it("signs in and out", async () => {
    mockApi(false);
    render(<Home />);
    await signIn("password");
    expect(await screen.findByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));
    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
  });
});
