import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Brand palette per PLAN.md §2 "Color Scheme"
        "accent-yellow": "#ecad0a",
        "blue-primary": "#209dd7",
        "purple-secondary": "#753991",
        // Surface tokens
        "surface-0": "#0d1117",
        "surface-1": "#141a23",
        "surface-2": "#1a2230",
        "surface-3": "#222c3d",
        "border-muted": "#2a3344",
        "text-primary": "#e6edf3",
        "text-secondary": "#9ba8b8",
        "text-muted": "#6b7785",
        // Price flash (separate from brand palette per spec)
        "flash-up": "#16a34a",
        "flash-down": "#dc2626",
      },
      fontFamily: {
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "Liberation Mono",
          "Courier New",
          "monospace",
        ],
      },
      transitionDuration: {
        "500": "500ms",
      },
    },
  },
  plugins: [],
};

export default config;
