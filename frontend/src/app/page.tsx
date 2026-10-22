"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";
import { logout, me } from "@/lib/api";

export default function Home() {
  // undefined while checking the session, null when signed out.
  const [username, setUsername] = useState<string | null>();

  useEffect(() => {
    me().then(setUsername);
  }, []);

  if (username === undefined) {
    return null;
  }
  if (username === null) {
    return <LoginForm onLogin={setUsername} />;
  }
  return (
    <KanbanBoard
      onLogout={async () => {
        await logout();
        setUsername(null);
      }}
    />
  );
}
