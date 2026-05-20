# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 02-watchlist-crud.spec.ts >> add PYPL then remove NFLX (persisted across reload)
- Location: tests/02-watchlist-crud.spec.ts:17:5

# Error details

```
Error: locator.click: Error: strict mode violation: getByRole('button', { name: 'Remove NFLX from watchlist' }) resolved to 2 elements:
    1) <div tabindex="0" role="button" data-testid="watchlist-row-NFLX" class="group grid cursor-pointer grid-cols-[1fr_auto_auto_auto] items-center gap-3 border-b border-border-muted/60 px-3 py-2 font-mono text-sm transition-colors hover:bg-surface-2 ">…</div> aka getByTestId('watchlist-row-NFLX')
    2) <button type="button" aria-label="Remove NFLX from watchlist" class="rounded px-2 py-0.5 text-xs text-text-muted opacity-0 transition-opacity hover:bg-surface-3 hover:text-rose-400 group-hover:opacity-100">✕</button> aka getByTestId('watchlist-row-NFLX').getByRole('button', { name: 'Remove NFLX from watchlist' })

Call log:
  - waiting for getByRole('button', { name: 'Remove NFLX from watchlist' })

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - banner [ref=e3]:
      - generic [ref=e4]:
        - generic [ref=e5]:
          - generic [ref=e6]: F
          - generic [ref=e7]:
            - generic [ref=e8]: FinAlly
            - generic [ref=e9]: AI Trading Workstation
        - generic [ref=e10]:
          - generic [ref=e11]:
            - generic [ref=e12]: Portfolio
            - generic [ref=e13]: $9,997.91
          - generic [ref=e14]:
            - generic [ref=e15]: Cash
            - generic [ref=e16]: $7,907.47
          - generic [ref=e17]:
            - generic [ref=e18]: Unrealized P&L
            - generic [ref=e19]: "-$2.09"
          - generic [ref=e22]: Live
    - main [ref=e23]:
      - region "Watchlist" [ref=e25]:
        - generic [ref=e26]:
          - heading "Watchlist" [level=2] [ref=e27]
          - generic [ref=e28]: 11 symbols
        - generic [ref=e29]:
          - textbox "Add ticker" [ref=e30]: PYPL
          - button "Add" [ref=e31] [cursor=pointer]
        - generic [ref=e32]: PYPL is already in your watchlist.
        - generic [ref=e33]:
          - button "AAPL +0.04% 190.07 Remove AAPL from watchlist" [ref=e34] [cursor=pointer]:
            - generic [ref=e35]:
              - generic [ref=e36]: AAPL
              - generic [ref=e37]: +0.04%
            - generic [ref=e38]: "190.07"
            - button "Remove AAPL from watchlist" [ref=e40]: ✕
          - button "AMZN -4.69% 176.32 Remove AMZN from watchlist" [ref=e41] [cursor=pointer]:
            - generic [ref=e42]:
              - generic [ref=e43]: AMZN
              - generic [ref=e44]: "-4.69%"
            - generic [ref=e45]: "176.32"
            - button "Remove AMZN from watchlist" [ref=e47]: ✕
          - button "GOOGL +0.07% 175.12 Remove GOOGL from watchlist" [ref=e48] [cursor=pointer]:
            - generic [ref=e49]:
              - generic [ref=e50]: GOOGL
              - generic [ref=e51]: +0.07%
            - generic [ref=e52]: "175.12"
            - button "Remove GOOGL from watchlist" [ref=e54]: ✕
          - button "JPM -1.90% 191.30 Remove JPM from watchlist" [ref=e55] [cursor=pointer]:
            - generic [ref=e56]:
              - generic [ref=e57]: JPM
              - generic [ref=e58]: "-1.90%"
            - generic [ref=e59]: "191.30"
            - button "Remove JPM from watchlist" [ref=e61]: ✕
          - button "META +3.61% 518.04 Remove META from watchlist" [ref=e62] [cursor=pointer]:
            - generic [ref=e63]:
              - generic [ref=e64]: META
              - generic [ref=e65]: +3.61%
            - generic [ref=e66]: "518.04"
            - button "Remove META from watchlist" [ref=e68]: ✕
          - button "MSFT -0.06% 419.74 Remove MSFT from watchlist" [ref=e69] [cursor=pointer]:
            - generic [ref=e70]:
              - generic [ref=e71]: MSFT
              - generic [ref=e72]: "-0.06%"
            - generic [ref=e73]: "419.74"
            - button "Remove MSFT from watchlist" [ref=e75]: ✕
          - button "NFLX +2.42% 614.51 Remove NFLX from watchlist" [ref=e76] [cursor=pointer]:
            - generic [ref=e77]:
              - generic [ref=e78]: NFLX
              - generic [ref=e79]: +2.42%
            - generic [ref=e80]: "614.51"
            - button "Remove NFLX from watchlist" [ref=e82]: ✕
          - button "NVDA +4.02% 832.19 Remove NVDA from watchlist" [ref=e83] [cursor=pointer]:
            - generic [ref=e84]:
              - generic [ref=e85]: NVDA
              - generic [ref=e86]: +4.02%
            - generic [ref=e87]: "832.19"
            - button "Remove NVDA from watchlist" [ref=e89]: ✕
          - button "TSLA +0.06% 250.15 Remove TSLA from watchlist" [ref=e90] [cursor=pointer]:
            - generic [ref=e91]:
              - generic [ref=e92]: TSLA
              - generic [ref=e93]: +0.06%
            - generic [ref=e94]: "250.15"
            - button "Remove TSLA from watchlist" [ref=e96]: ✕
          - button "V -0.10% 279.71 Remove V from watchlist" [ref=e97] [cursor=pointer]:
            - generic [ref=e98]:
              - generic [ref=e99]: V
              - generic [ref=e100]: "-0.10%"
            - generic [ref=e101]: "279.71"
            - button "Remove V from watchlist" [ref=e103]: ✕
          - button "PYPL -0.07% 183.56 Remove PYPL from watchlist" [ref=e104] [cursor=pointer]:
            - generic [ref=e105]:
              - generic [ref=e106]: PYPL
              - generic [ref=e107]: "-0.07%"
            - generic [ref=e108]: "183.56"
            - button "Remove PYPL from watchlist" [ref=e110]: ✕
        - generic [ref=e111]: PYPL is already in your watchlist.
      - generic [ref=e112]:
        - generic [ref=e113]:
          - region "Main chart" [ref=e115]:
            - generic [ref=e116]:
              - heading "Chart · AAPL" [level=2] [ref=e117]
              - tablist "Range" [ref=e118]:
                - tab "1h" [selected] [ref=e119] [cursor=pointer]
                - tab "6h" [ref=e120] [cursor=pointer]
                - tab "24h" [ref=e121] [cursor=pointer]
                - tab "7d" [ref=e122] [cursor=pointer]
            - table [ref=e126]:
              - row [ref=e127]:
                - cell
                - cell [ref=e128]:
                  - link "Charting by TradingView" [ref=e132] [cursor=pointer]:
                    - /url: https://www.tradingview.com/?utm_medium=lwc-link&utm_campaign=lwc-chart&utm_source=localhost/
                    - img [ref=e133]
                - cell [ref=e137]
              - row [ref=e141]:
                - cell
                - cell [ref=e142]
                - cell [ref=e146]
          - region "Portfolio heatmap" [ref=e150]:
            - heading "Allocation" [level=2] [ref=e152]
            - generic [ref=e156]:
              - img [ref=e157]:
                - generic [ref=e158]:
                  - generic [ref=e160]: AAPL
                  - generic [ref=e161]: "-0.1%"
              - list [ref=e162]:
                - listitem [ref=e163]: "AAPL: $2,090.44 (-0.10%)"
        - generic [ref=e164]:
          - region "Portfolio P&L" [ref=e166]:
            - generic [ref=e167]:
              - heading "Portfolio Value" [level=2] [ref=e168]
              - generic [ref=e169]:
                - button "1h" [ref=e170] [cursor=pointer]
                - button "6h" [ref=e171] [cursor=pointer]
                - button "24h" [ref=e172] [cursor=pointer]
                - button "7d" [ref=e173] [cursor=pointer]
            - img [ref=e177]:
              - generic [ref=e179]:
                - generic [ref=e181]: 06:43 AM
                - generic [ref=e183]: 06:45 AM
                - generic [ref=e185]: 06:46 AM
                - generic [ref=e187]: 06:48 AM
              - generic [ref=e189]:
                - generic [ref=e191]: $9,998
                - generic [ref=e193]: $9,998
                - generic [ref=e195]: $9,999
                - generic [ref=e197]: $10,000
                - generic [ref=e199]: $10,000
          - region "Positions" [ref=e205]:
            - generic [ref=e206]:
              - heading "Positions" [level=2] [ref=e207]
              - generic [ref=e208]: 1 open
            - table [ref=e210]:
              - rowgroup [ref=e211]:
                - row "Ticker Qty Avg Cost Last P&L %" [ref=e212]:
                  - columnheader "Ticker" [ref=e213]
                  - columnheader "Qty" [ref=e214]
                  - columnheader "Avg Cost" [ref=e215]
                  - columnheader "Last" [ref=e216]
                  - columnheader "P&L" [ref=e217]
                  - columnheader "%" [ref=e218]
              - rowgroup [ref=e219]:
                - row "AAPL 11 190.23 190.07 -$1.76 -0.08%" [ref=e220] [cursor=pointer]:
                  - cell "AAPL" [ref=e221]
                  - cell "11" [ref=e222]
                  - cell "190.23" [ref=e223]
                  - cell "190.07" [ref=e224]
                  - cell "-$1.76" [ref=e225]
                  - cell "-0.08%" [ref=e226]
        - region "Trade" [ref=e227]:
          - generic [ref=e228]:
            - heading "Trade" [level=2] [ref=e229]
            - generic [ref=e230]: market · instant fill
          - generic [ref=e231]:
            - textbox "Ticker" [ref=e232]:
              - /placeholder: TICKER
              - text: AAPL
            - textbox "Quantity" [ref=e233]:
              - /placeholder: QTY
            - button "Buy" [ref=e234] [cursor=pointer]
            - button "Sell" [ref=e235] [cursor=pointer]
      - complementary "AI chat" [ref=e237]:
        - generic [ref=e238]:
          - heading "FinAlly Assistant" [level=2] [ref=e241]
          - button "Hide chat panel" [ref=e242] [cursor=pointer]: —
        - generic [ref=e244]:
          - paragraph [ref=e245]: Ask FinAlly about your portfolio, request a trade, or manage your watchlist. Trades execute automatically.
          - generic [ref=e246]:
            - button "What's my portfolio?" [ref=e247] [cursor=pointer]
            - button "Buy 5 AAPL" [ref=e248] [cursor=pointer]
            - button "Add PYPL to watchlist" [ref=e249] [cursor=pointer]
        - generic [ref=e250]:
          - textbox "Chat input" [ref=e251]:
            - /placeholder: Ask FinAlly…
          - button "Send" [disabled] [ref=e252]
  - alert [ref=e253]
  - generic [ref=e254]: $9,998
```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | 
  3  | /**
  4  |  * Scenario 2: Watchlist CRUD.
  5  |  *
  6  |  *   - Add PYPL via the input control; assert row appears.
  7  |  *   - Remove a default ticker (NFLX); assert it disappears and is NOT
  8  |  *     restored after reload.
  9  |  *
  10 |  * The watchlist add control is the form inside the Watchlist component:
  11 |  *   <input placeholder="Add ticker" />  +  <button>Add</button>
  12 |  *
  13 |  * The remove control is a per-row "✕" button labelled
  14 |  *   "Remove <TICKER> from watchlist".
  15 |  */
  16 | 
  17 | test("add PYPL then remove NFLX (persisted across reload)", async ({ page }) => {
  18 |   await page.goto("/");
  19 | 
  20 |   // Wait for the seed watchlist to render so we know the page is hot.
  21 |   await expect(page.getByTestId("watchlist-row-NFLX")).toBeVisible();
  22 | 
  23 |   // -- Add PYPL ----------------------------------------------------------
  24 |   const addInput = page.getByPlaceholder("Add ticker");
  25 |   await addInput.fill("PYPL");
  26 |   await page.getByRole("button", { name: "Add", exact: true }).click();
  27 | 
  28 |   await expect(page.getByTestId("watchlist-row-PYPL")).toBeVisible({
  29 |     timeout: 10_000,
  30 |   });
  31 | 
  32 |   // -- Remove NFLX -------------------------------------------------------
  33 |   // The remove button is hidden until hover, but Playwright's click forces
  34 |   // it. We use the accessible name instead of relying on hover state.
  35 |   const nflxRow = page.getByTestId("watchlist-row-NFLX");
  36 |   await nflxRow.hover();
  37 |   await page
  38 |     .getByRole("button", { name: "Remove NFLX from watchlist" })
> 39 |     .click();
     |      ^ Error: locator.click: Error: strict mode violation: getByRole('button', { name: 'Remove NFLX from watchlist' }) resolved to 2 elements:
  40 | 
  41 |   await expect(page.getByTestId("watchlist-row-NFLX")).toHaveCount(0);
  42 | 
  43 |   // -- Reload and assert persistence ------------------------------------
  44 |   await page.reload();
  45 |   await expect(page.getByTestId("watchlist-row-PYPL")).toBeVisible({
  46 |     timeout: 10_000,
  47 |   });
  48 |   await expect(page.getByTestId("watchlist-row-NFLX")).toHaveCount(0);
  49 | });
  50 | 
```