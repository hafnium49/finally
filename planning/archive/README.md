# Planning Archive

Historical planning documents that have been superseded by current state.

## Market Data Docs (superseded by `planning/MARKET_DATA_SUMMARY.md`)

| File | Original purpose |
|------|------------------|
| `MARKET_DATA_DESIGN.md` | Long-form design proposal for the market data subsystem. The actual implementation tracks this design; the summary captures what shipped. |
| `MARKET_INTERFACE.md` | Early draft of the `MarketDataSource` ABC contract. The current contract is documented inline in `app/market/interface.py` and recapped in the summary. |
| `MARKET_SIMULATOR.md` | Early write-up of the GBM simulator. The implementation in `app/market/simulator.py` is the source of truth now. |
| `MASSIVE_API.md` | Notes from integrating the Polygon.io `massive` SDK. Useful only when revisiting that integration. |
| `MARKET_DATA_REVIEW.md` | Pre-fix code review that drove the `market-data-fixes` branch. All listed issues were resolved before merge. |

## Auto-Generated Reviews

`reviews/review-*.md` are auto-generated review artifacts written by the `Stop` hook in `.claude/settings.json` (see project README for details). They are preserved here for historical reference and to keep the active `planning/` directory uncluttered.
