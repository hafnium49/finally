"use client";

import type { ChatTurn } from "../lib/types";
import { ActionCard } from "./ActionCard";

interface ChatMessageProps {
  turn: ChatTurn;
}

export function ChatMessage({ turn }: ChatMessageProps) {
  const isUser = turn.role === "user";

  return (
    <div
      data-testid={`chat-message-${turn.role}`}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[88%] rounded-md border px-3 py-2 text-sm leading-snug ${
          isUser
            ? "border-blue-primary/40 bg-blue-primary/10 text-text-primary"
            : turn.errored
              ? "border-rose-700/60 bg-rose-500/10 text-rose-200"
              : "border-border-muted bg-surface-2 text-text-primary"
        }`}
      >
        {turn.pending ? (
          <div className="flex items-center gap-2 text-text-muted">
            <span className="inline-flex gap-1">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-primary [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-primary [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-primary" />
            </span>
            <span className="text-xs">FinAlly is thinking…</span>
          </div>
        ) : (
          <div className="whitespace-pre-wrap">{turn.content}</div>
        )}
        {turn.actions && turn.actions.length > 0 && (
          <div className="mt-2 flex flex-col gap-1">
            {turn.actions.map((a, i) => (
              <ActionCard key={i} action={a} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
