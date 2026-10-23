import type { BoardData } from "@/lib/kanban";

const send = (url: string, method: string, body?: unknown) =>
  fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

// Returns the username, or null when there is no session.
export const me = async (): Promise<string | null> => {
  const response = await fetch("/api/me");
  return response.ok ? (await response.json()).username : null;
};

// Returns true when the credentials are accepted.
export const login = async (username: string, password: string) =>
  (await send("/api/login", "POST", { username, password })).ok;

export const logout = async () => {
  await send("/api/logout", "POST");
};

export const getBoard = async (): Promise<BoardData> =>
  (await fetch("/api/board")).json();

// Saves run one after another. The server handles requests concurrently, so
// overlapping saves (one per keystroke while renaming a column) could otherwise
// finish out of order and leave an older board stored.
let lastSave: Promise<unknown> = Promise.resolve();

export const saveBoard = (board: BoardData) => {
  lastSave = lastSave
    .catch(() => {})
    .then(() => send("/api/board", "PUT", board));
  return lastSave;
};
