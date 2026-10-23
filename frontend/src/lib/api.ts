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

export type ChatMessage = { role: "user" | "assistant"; content: string };

export class ChatRequestError extends Error {
  constructor(readonly status: number) {
    super(`Chat request failed with ${status}`);
  }
}

// Waits for queued saves first, so the AI sees the latest board. `board` is the
// board the AI changed and the server saved, or null when nothing changed.
// Throws ChatRequestError when the request fails (502 when the AI call fails).
export const sendChat = async (
  message: string,
  history: ChatMessage[]
): Promise<{ reply: string; board: BoardData | null }> => {
  await lastSave.catch(() => {});
  const response = await send("/api/chat", "POST", { message, history });
  if (!response.ok) {
    throw new ChatRequestError(response.status);
  }
  return response.json();
};
