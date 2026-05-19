import { describe, it, expect } from "vitest";
import { formatPct, formatPrice, formatQuantity, formatUsd } from "../app/lib/format";

describe("format", () => {
  it("formatUsd handles positive, negative, zero, null", () => {
    expect(formatUsd(1234.5)).toBe("$1,234.50");
    expect(formatUsd(-50.1)).toBe("-$50.10");
    expect(formatUsd(0)).toBe("$0.00");
    expect(formatUsd(null)).toBe("—");
    expect(formatUsd(undefined)).toBe("—");
  });

  it("formatPct includes sign for positive numbers", () => {
    expect(formatPct(1.234)).toBe("+1.23%");
    expect(formatPct(-2.5)).toBe("-2.50%");
    expect(formatPct(0)).toBe("0.00%");
    expect(formatPct(null)).toBe("—");
  });

  it("formatPrice renders 2 decimals", () => {
    expect(formatPrice(192.345)).toBe("192.35");
    expect(formatPrice(null)).toBe("—");
  });

  it("formatQuantity drops trailing zeros for integers", () => {
    expect(formatQuantity(10)).toBe("10");
    expect(formatQuantity(10.5)).toBe("10.5");
  });
});
