import { useState, type FormEvent } from "react";
import { login } from "@/lib/api";

type LoginFormProps = {
  onLogin: (username: string) => void;
};

export const LoginForm = ({ onLogin }: LoginFormProps) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const status = await login(username, password);
    if (status === 200) {
      onLogin(username);
    } else {
      setError(
        status === 429
          ? "Too many sign-in attempts. Try again in 15 minutes."
          : "Invalid username or password."
      );
    }
  };

  const inputClass =
    "w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]";

  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)]"
      >
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
            Kanban Studio
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
            Sign in
          </h1>
        </div>
        <input
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          aria-label="Username"
          placeholder="Username"
          autoComplete="username"
          className={inputClass}
          required
        />
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          aria-label="Password"
          placeholder="Password"
          autoComplete="current-password"
          className={inputClass}
          required
        />
        {error && (
          <p role="alert" className="text-sm font-medium text-red-600">
            {error}
          </p>
        )}
        <button
          type="submit"
          className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
        >
          Sign in
        </button>
      </form>
    </main>
  );
};
