import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "@/app/page";

// Fakes the auth API: a session cookie stands in as `signedIn`.
const mockAuthApi = (signedIn: boolean) => {
  vi.stubGlobal("fetch", async (url: string, init?: RequestInit) => {
    if (url === "/api/login") {
      const { password } = JSON.parse(init!.body as string);
      signedIn = password === "password";
      return Response.json({}, { status: signedIn ? 200 : 401 });
    }
    if (url === "/api/logout") {
      signedIn = false;
      return Response.json({});
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
    mockAuthApi(false);
    render(<Home />);
    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Kanban Studio" })).not.toBeInTheDocument();
  });

  it("shows the board with an existing session", async () => {
    mockAuthApi(true);
    render(<Home />);
    expect(await screen.findByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
  });

  it("shows an error for wrong credentials", async () => {
    mockAuthApi(false);
    render(<Home />);
    await signIn("wrong");
    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid/i);
    expect(screen.queryByRole("heading", { name: "Kanban Studio" })).not.toBeInTheDocument();
  });

  it("signs in and out", async () => {
    mockAuthApi(false);
    render(<Home />);
    await signIn("password");
    expect(await screen.findByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));
    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
  });
});
