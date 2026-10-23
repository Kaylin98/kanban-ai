"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";
import { getBoard, logout, me } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

export default function Home() {
  // undefined while checking the session, null when signed out.
  const [username, setUsername] = useState<string | null>();
  const [board, setBoard] = useState<BoardData | null>(null);

  useEffect(() => {
    me().then(setUsername);
  }, []);

  useEffect(() => {
    if (username) {
      getBoard().then(setBoard);
    }
  }, [username]);

  if (username === undefined) {
    return null;
  }
  if (username === null) {
    return <LoginForm onLogin={setUsername} />;
  }
  if (board === null) {
    return (
      <main className="flex min-h-screen items-center justify-center text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
        Loading board...
      </main>
    );
  }
  return (
    <KanbanBoard
      initialBoard={board}
      onLogout={async () => {
        await logout();
        setUsername(null);
        setBoard(null);
      }}
    />
  );
}
