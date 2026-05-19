# FinAlly frontend

Next.js 14 (App Router) + TypeScript single-page application, configured for
`output: 'export'`. The build artifact at `frontend/out/` is served verbatim by
the FastAPI backend on `/`.

## Scripts

- `npm install` — install dependencies
- `npm run build` — produce static export at `out/`
- `npm run dev` — local development server (Next dev mode, not used in
  production)
- `npm run test` — run Vitest unit tests

## Stack notes

- **Tailwind CSS** with brand tokens for `accent-yellow`, `blue-primary`, and
  `purple-secondary` (PLAN.md §2 color scheme) plus surface tokens for the
  dark trading-terminal palette.
- **TradingView Lightweight Charts** for the main per-ticker chart. Chosen for
  its native financial-chart features (price line, crosshair, time scale) and
  its tiny footprint vs. Chart.js or Highcharts.
- **Recharts** for the portfolio P&L area chart — a plain time-series doesn't
  need Lightweight Charts' financial features, and Recharts composes well with
  Tailwind-styled responsive containers.
- **Browser-native `EventSource`** (no third-party SSE library) wrapped in
  `app/lib/sse.ts` which exposes a small connection-state observable consumed
  by the header's status dot.

## Wire-contract assumptions

- The SSE frame shape matches `API_CONTRACT.md §2.1`: each `message` event's
  `data` payload is a JSON object **keyed by ticker** with the full
  `PriceUpdate` record as the value. Iterating the keys is how we update the
  in-memory price store.
- Watchlist rows render `change_pct` from the API initially and prefer
  recomputing against `session_anchor_price` when an SSE-cached price exists
  (the server already computes it the same way; this just keeps the value
  fresh between polls).
- Trades are instant fill — there is no confirmation dialog (per PLAN.md §9).
- The chat panel renders each entry of `ChatResponse.actions[]` as an inline
  `ActionCard`, distinguishing `status: "ok"` vs `"error"` (success uses
  emerald, errors use rose; neither uses the brand palette per spec).
