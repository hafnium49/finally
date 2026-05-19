import { describe, it, expect, vi, beforeEach } from "vitest";
import { PriceStream, type ConnectionState } from "../app/lib/sse";

class FakeEventSource {
  static OPEN = 1;
  static CLOSED = 2;
  static CONNECTING = 0;

  url: string;
  readyState = 0;
  onopen: ((ev: Event) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  onmessage: ((ev: MessageEvent<string>) => void) | null = null;

  constructor(url: string) {
    this.url = url;
  }

  open() {
    this.readyState = 1;
    this.onopen?.(new Event("open"));
  }

  error({ closed = false }: { closed?: boolean } = {}) {
    this.readyState = closed ? 2 : 0;
    this.onerror?.(new Event("error"));
  }

  message(data: string) {
    this.onmessage?.(new MessageEvent("message", { data }));
  }

  close() {
    this.readyState = 2;
  }
}

describe("PriceStream connection state machine", () => {
  let fake: FakeEventSource | null;
  let Ctor: typeof EventSource;

  beforeEach(() => {
    fake = null;
    Ctor = function (this: FakeEventSource, url: string) {
      const inst = new FakeEventSource(url);
      fake = inst;
      return inst;
    } as unknown as typeof EventSource;
  });

  const newStream = () => new PriceStream({ EventSourceCtor: Ctor });

  it("starts in 'closed' and moves to 'connecting' on start()", () => {
    const s = newStream();
    const states: ConnectionState[] = [];
    s.onState((st) => states.push(st));
    expect(states).toEqual(["closed"]);
    s.start();
    expect(states).toContain("connecting");
  });

  it("transitions to 'open' when EventSource opens", () => {
    const s = newStream();
    s.start();
    const states: ConnectionState[] = [];
    s.onState((st) => states.push(st));
    fake!.open();
    expect(s.getState()).toBe("open");
    expect(states).toContain("open");
  });

  it("transitions to 'reconnecting' on error after a successful open", () => {
    const s = newStream();
    s.start();
    fake!.open();
    fake!.error({ closed: false });
    expect(s.getState()).toBe("reconnecting");
  });

  it("transitions to 'closed' on terminal error (readyState=CLOSED)", () => {
    const s = newStream();
    s.start();
    fake!.open();
    fake!.error({ closed: true });
    expect(s.getState()).toBe("closed");
  });

  it("stays 'connecting' on error if we never opened (initial dial-up failure)", () => {
    const s = newStream();
    s.start();
    fake!.error({ closed: false });
    expect(s.getState()).toBe("connecting");
  });

  it("dispatches frame listeners with the parsed map shape", () => {
    const s = newStream();
    s.start();
    fake!.open();
    const frames: unknown[] = [];
    s.onFrame((frame) => frames.push(frame));
    fake!.message(
      JSON.stringify({
        AAPL: {
          ticker: "AAPL",
          price: 192.34,
          previous_price: 191.88,
          timestamp: 1747741234.812,
          change: 0.46,
          change_percent: 0.24,
          direction: "up",
        },
      }),
    );
    expect(frames).toHaveLength(1);
    expect(frames[0]).toMatchObject({ AAPL: { ticker: "AAPL", price: 192.34, direction: "up" } });
  });

  it("ignores malformed JSON frames silently", () => {
    const s = newStream();
    s.start();
    fake!.open();
    const frames: unknown[] = [];
    s.onFrame((f) => frames.push(f));
    fake!.message("not json");
    expect(frames).toHaveLength(0);
  });

  it("close() moves to 'closed' and stops emitting", () => {
    const s = newStream();
    s.start();
    fake!.open();
    s.close();
    expect(s.getState()).toBe("closed");
  });
});
