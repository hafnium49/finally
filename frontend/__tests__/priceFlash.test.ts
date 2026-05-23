import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { computeDirection, flashElement } from "../app/lib/priceFlash";

describe("computeDirection", () => {
  it("returns 'up' when next > prev", () => {
    expect(computeDirection(100, 101)).toBe("up");
  });
  it("returns 'down' when next < prev", () => {
    expect(computeDirection(100, 99.5)).toBe("down");
  });
  it("returns 'flat' on no-op tick (equal prices)", () => {
    expect(computeDirection(100, 100)).toBe("flat");
  });
  it("returns 'flat' when prev is null (first observation)", () => {
    expect(computeDirection(null, 50)).toBe("flat");
  });
  it("returns 'flat' when prev is undefined", () => {
    expect(computeDirection(undefined, 50)).toBe("flat");
  });
});

describe("flashElement", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("applies the up class on upticks", () => {
    const el = document.createElement("div");
    flashElement(el, "up");
    expect(el.classList.contains("flash-up")).toBe(true);
  });

  it("applies the down class on downticks", () => {
    const el = document.createElement("div");
    flashElement(el, "down");
    expect(el.classList.contains("flash-down")).toBe(true);
  });

  it("does NOT flash on flat direction (no-op tick)", () => {
    const el = document.createElement("div");
    flashElement(el, "flat");
    expect(el.classList.contains("flash-up")).toBe(false);
    expect(el.classList.contains("flash-down")).toBe(false);
  });

  it("removes the class after ~500ms", () => {
    const el = document.createElement("div");
    flashElement(el, "up");
    expect(el.classList.contains("flash-up")).toBe(true);
    vi.advanceTimersByTime(600);
    expect(el.classList.contains("flash-up")).toBe(false);
  });

  it("swaps classes when direction reverses mid-flight", () => {
    const el = document.createElement("div");
    flashElement(el, "up");
    flashElement(el, "down");
    expect(el.classList.contains("flash-down")).toBe(true);
    expect(el.classList.contains("flash-up")).toBe(false);
  });
});
