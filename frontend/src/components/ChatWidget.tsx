import clsx from "clsx";
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { ChatRequestError, MAX_MESSAGE_LENGTH, sendChat, type ChatMessage } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

type ChatWidgetProps = {
  onBoardUpdate: (board: BoardData) => void;
};

const OPEN_KEY = "chat-open";

// A chat bubble in the bottom right corner that opens a panel floating over the board.
export const ChatWidget = ({ onBoardUpdate }: ChatWidgetProps) => {
  const [isOpen, setIsOpen] = useState(() => localStorage.getItem(OPEN_KEY) === "true");
  // The history lives only here, so it is lost on refresh.
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current!.scrollTop = listRef.current!.scrollHeight;
  }, [messages, isSending, isOpen]);

  const toggle = () => {
    localStorage.setItem(OPEN_KEY, String(!isOpen));
    setIsOpen(!isOpen);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const message = input.trim();
    if (!message || isSending) {
      return;
    }
    setMessages([...messages, { role: "user", content: message }]);
    setInput("");
    setError(null);
    setIsSending(true);
    try {
      const response = await sendChat(message, messages);
      setMessages((prev) => [...prev, { role: "assistant", content: response.reply }]);
      if (response.board) {
        onBoardUpdate(response.board);
      }
    } catch (error) {
      // Drop the failed message from the history and put it back in the input to retry.
      setMessages(messages);
      setInput(message);
      const status = error instanceof ChatRequestError ? error.status : null;
      setError(
        status === 502
          ? "The assistant had trouble, try again."
          : status === 429
            ? "You have reached the hourly chat limit. Try again later."
            : "The assistant could not complete that request. Try again."
      );
    } finally {
      setIsSending(false);
    }
  };

  // Enter sends; Shift+Enter adds a new line.
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form!.requestSubmit();
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-3 sm:bottom-6 sm:right-6">
      {/* Hidden rather than unmounted, so the message list (and listRef) always exists. */}
      <section
        id="chat-panel"
        aria-label="AI assistant"
        hidden={!isOpen}
        className="flex h-[min(600px,calc(100dvh-7rem))] w-[min(380px,calc(100vw-2rem))] flex-col rounded-3xl border border-[var(--stroke)] bg-white shadow-[0_24px_60px_rgba(3,33,71,0.22)]"
      >
        <div className="border-b border-[var(--stroke)] px-5 py-4">
          <div className="h-1.5 w-8 rounded-full bg-[var(--accent-yellow)]" />
          <h2 className="mt-2 font-display text-base font-semibold text-[var(--navy-dark)]">
            AI Assistant
          </h2>
          <p className="mt-0.5 text-xs leading-5 text-[var(--gray-text)]">
            Ask about your board, or ask it to create, edit, move or delete cards.
          </p>
        </div>

        <div
          ref={listRef}
          role="log"
          aria-label="Chat messages"
          className="flex flex-1 flex-col gap-3 overflow-y-auto px-5 py-4"
        >
          {messages.length === 0 && !isSending && (
            <p className="m-auto max-w-[240px] text-center text-xs leading-5 text-[var(--gray-text)]">
              Try &ldquo;Move the QA card to Review&rdquo; or &ldquo;What is still in
              Backlog?&rdquo;
            </p>
          )}
          {messages.map((message, index) => (
            <div
              key={index}
              className={clsx(
                "max-w-[85%] whitespace-pre-wrap wrap-break-word rounded-2xl px-4 py-2.5 text-sm leading-6",
                message.role === "user"
                  ? "self-end rounded-br-md bg-[var(--navy-dark)] text-white"
                  : "self-start rounded-bl-md bg-[var(--surface)] text-[var(--navy-dark)]"
              )}
            >
              {message.content}
            </div>
          ))}
          {isSending && (
            <div className="self-start rounded-2xl rounded-bl-md bg-[var(--surface)] px-4 py-2.5 text-sm text-[var(--gray-text)]">
              <span className="animate-pulse">Thinking...</span>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="border-t border-[var(--stroke)] p-4">
          {error && (
            <p role="alert" className="mb-2 text-xs text-[var(--secondary-purple)]">
              {error}
            </p>
          )}
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message the assistant"
              aria-label="Message"
              maxLength={MAX_MESSAGE_LENGTH}
              rows={2}
              className="min-w-0 flex-1 resize-none rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)] focus:bg-white"
            />
            <button
              type="submit"
              disabled={isSending || !input.trim()}
              className="rounded-full bg-[var(--secondary-purple)] px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110 disabled:opacity-50 disabled:hover:brightness-100"
            >
              {isSending ? "Sending..." : "Send"}
            </button>
          </div>
        </form>
      </section>

      <button
        type="button"
        onClick={toggle}
        aria-expanded={isOpen}
        aria-controls="chat-panel"
        aria-label={isOpen ? "Minimize AI assistant" : "Open AI assistant"}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--secondary-purple)] text-white shadow-[0_12px_30px_rgba(117,57,145,0.4)] transition hover:brightness-110"
      >
        {isOpen ? (
          <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <path d="M6 9l6 6 6-6" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z" />
          </svg>
        )}
      </button>
    </div>
  );
};
