const post = (url: string, body?: unknown) =>
  fetch(url, {
    method: "POST",
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
  (await post("/api/login", { username, password })).ok;

export const logout = async () => {
  await post("/api/logout");
};
