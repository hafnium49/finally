import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChatMessage } from "../app/components/ChatMessage";
import type { ChatTurn } from "../app/lib/types";

describe("ChatMessage", () => {
  it("renders a user turn", () => {
    const turn: ChatTurn = {
      id: "u1",
      role: "user",
      content: "Buy 5 AAPL",
      timestamp: 0,
    };
    render(<ChatMessage turn={turn} />);
    expect(screen.getByTestId("chat-message-user")).toHaveTextContent("Buy 5 AAPL");
  });

  it("renders an assistant turn with actions inline", () => {
    const turn: ChatTurn = {
      id: "a1",
      role: "assistant",
      content: "Buying 5 AAPL.",
      actions: [
        {
          kind: "trade",
          status: "ok",
          ticker: "AAPL",
          side: "buy",
          quantity: 5,
          fill_price: 100,
          cash_after: 9500,
        },
      ],
      timestamp: 0,
    };
    render(<ChatMessage turn={turn} />);
    expect(screen.getByTestId("chat-message-assistant")).toHaveTextContent("Buying 5 AAPL.");
    expect(screen.getByTestId("action-trade-ok")).toBeInTheDocument();
  });

  it("renders pending indicator", () => {
    const turn: ChatTurn = {
      id: "a2",
      role: "assistant",
      content: "",
      pending: true,
      timestamp: 0,
    };
    render(<ChatMessage turn={turn} />);
    expect(screen.getByText(/FinAlly is thinking/i)).toBeInTheDocument();
  });
});
