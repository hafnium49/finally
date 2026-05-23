"use client";

import { useCallback, useState } from "react";
import { sendChat } from "../lib/api";
import type { ChatTurn } from "../lib/types";

let turnCounter = 0;
function makeId(prefix: string): string {
  turnCounter += 1;
  return `${prefix}-${Date.now()}-${turnCounter}`;
}

export interface UseChatReturn {
  turns: ChatTurn[];
  pending: boolean;
  send: (message: string) => Promise<void>;
  clear: () => void;
}

export function useChat(): UseChatReturn {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [pending, setPending] = useState(false);

  const send = useCallback(async (message: string) => {
    const trimmed = message.trim();
    if (!trimmed) return;

    const userTurn: ChatTurn = {
      id: makeId("u"),
      role: "user",
      content: trimmed,
      timestamp: Date.now(),
    };
    const placeholderId = makeId("a");
    const pendingTurn: ChatTurn = {
      id: placeholderId,
      role: "assistant",
      content: "",
      pending: true,
      timestamp: Date.now(),
    };

    setTurns((prev) => [...prev, userTurn, pendingTurn]);
    setPending(true);

    try {
      const res = await sendChat(trimmed);
      setTurns((prev) =>
        prev.map((t) =>
          t.id === placeholderId
            ? {
                ...t,
                content: res.message,
                actions: res.actions ?? [],
                pending: false,
              }
            : t,
        ),
      );
    } catch (err) {
      setTurns((prev) =>
        prev.map((t) =>
          t.id === placeholderId
            ? {
                ...t,
                content:
                  err instanceof Error
                    ? `Chat failed: ${err.message}`
                    : "Chat failed.",
                pending: false,
                errored: true,
              }
            : t,
        ),
      );
    } finally {
      setPending(false);
    }
  }, []);

  const clear = useCallback(() => setTurns([]), []);

  return { turns, pending, send, clear };
}
