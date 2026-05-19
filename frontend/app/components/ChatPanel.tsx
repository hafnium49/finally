"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useChat } from "../hooks/useChat";
import { ChatMessage } from "./ChatMessage";

interface ChatPanelProps {
  onActivity?: () => void;
}

const SUGGESTIONS = [
  "What's my portfolio?",
  "Buy 5 AAPL",
  "Add PYPL to watchlist",
];

export function ChatPanel({ onActivity }: ChatPanelProps) {
  const { turns, pending, send } = useChat();
  const [input, setInput] = useState("");
  const [open, setOpen] = useState(true);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [turns]);

  // Notify parent of activity (so it can refresh portfolio after LLM trades).
  const turnsLength = turns.length;
  useEffect(() => {
    if (!pending && turnsLength > 0) onActivity?.();
  }, [pending, turnsLength, onActivity]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const value = input.trim();
    if (!value || pending) return;
    setInput("");
    await send(value);
  };

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 z-20 rounded-full bg-purple-secondary px-4 py-3 text-sm font-semibold text-white shadow-lg hover:bg-purple-secondary/80"
      >
        AI Chat
      </button>
    );
  }

  return (
    <aside
      aria-label="AI chat"
      className="flex h-full w-full flex-col overflow-hidden rounded-md border border-border-muted bg-surface-1"
    >
      <header className="flex items-center justify-between border-b border-border-muted px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-purple-secondary" />
          <h2 className="text-xs font-semibold uppercase tracking-widest text-blue-primary">
            FinAlly Assistant
          </h2>
        </div>
        <button
          type="button"
          onClick={() => setOpen(false)}
          aria-label="Hide chat panel"
          className="rounded px-2 py-0.5 text-xs text-text-muted hover:bg-surface-2 hover:text-text-primary"
        >
          —
        </button>
      </header>

      <div
        ref={scrollRef}
        className="flex-1 space-y-2 overflow-y-auto px-3 py-2"
        data-testid="chat-scroll"
      >
        {turns.length === 0 ? (
          <div className="space-y-3 text-xs text-text-muted">
            <p>
              Ask FinAlly about your portfolio, request a trade, or manage your
              watchlist. Trades execute automatically.
            </p>
            <div className="flex flex-wrap gap-1.5">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => send(s)}
                  className="rounded border border-border-muted bg-surface-2 px-2 py-1 text-xs text-text-secondary transition-colors hover:border-blue-primary hover:text-text-primary"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          turns.map((t) => <ChatMessage key={t.id} turn={t} />)
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex items-end gap-2 border-t border-border-muted bg-surface-2 px-3 py-2"
      >
        <textarea
          aria-label="Chat input"
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e as unknown as FormEvent);
            }
          }}
          placeholder="Ask FinAlly…"
          className="max-h-24 flex-1 resize-none rounded border border-border-muted bg-surface-1 px-2 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:border-blue-primary focus:outline-none"
        />
        <button
          type="submit"
          disabled={pending || !input.trim()}
          className="rounded bg-purple-secondary px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-purple-secondary/80 disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </aside>
  );
}
