# Market Simulator Design

Approach and code structure for simulating realistic stock prices when no Massive API key is configured. Reflects the shipped implementation in `backend/app/market/simulator.py` and `backend/app/market/seed_prices.py`.

## Overview

The simulator uses **Geometric Brownian Motion (GBM)** to generate realistic stock price paths. GBM is the standard model underlying Black–Scholes — prices evolve continuously with random noise, can never go negative, and follow the lognormal distribution observed empirically in equity markets.

It runs as an async background task that calls `GBMSimulator.step()` every **500 ms** and writes results to the shared `PriceCache`. Correlated draws (Cholesky decomposition of a sector-based correlation matrix) and rare random shocks make the data visually interesting without sacrificing mathematical plausibility.

## Math

At each time step, a stock price evolves as:

```
S(t+dt) = S(t) * exp((mu - sigma^2/2) * dt + sigma * sqrt(dt) * Z)
```

Where:

| Symbol | Meaning |
|---|---|
| `S(t)` | current price |
| `mu` | annualized drift (expected return), e.g. 0.05 (5%) |
| `sigma` | annualized volatility, e.g. 0.20 (20%) |
| `dt` | time step as a fraction of a trading year |
| `Z` | correlated standard normal draw (see below) |

The drift term `(mu - sigma^2/2)` is the lognormal-corrected mean; the `sigma * sqrt(dt) * Z` term is the diffusion (random noise).

### Time-step conversion

A trading year ≈ 252 days × 6.5 hours × 3600 s = **5,896,800 trading seconds**. A 500 ms tick is therefore:

```
dt = 0.5 / 5_896_800  ≈  8.48 × 10⁻⁸
```

This tiny `dt` produces sub-cent moves per tick that compound naturally into realistic intraday and daily ranges (see §"Parameter Justification" below).

## Correlated Moves

Real equities don't move independently — tech stocks tend to move together, banks track each other, etc. We use a **Cholesky decomposition** of a correlation matrix `C` to generate correlated random draws.

For independent standard normals `Z_independent`, compute `L = cholesky(C)` and:

```
Z_correlated = L @ Z_independent
```

`L @ Z_independent` has the same per-element variance (1) as `Z_independent`, but its covariance matrix is exactly `C`. This is the Cleve Moler trick that powers most Monte Carlo simulations of correlated assets.

### Correlation structure (shipped values)

```
Same tech sector       → 0.6
Same finance sector    → 0.5
TSLA with anything     → 0.3   (TSLA does its own thing)
Cross-sector / unknown → 0.3
```

Sector membership lives in `seed_prices.py`:

```python
CORRELATION_GROUPS = {
    "tech":    {"AAPL", "GOOGL", "MSFT", "AMZN", "META", "NVDA", "NFLX"},
    "finance": {"JPM", "V"},
}
```

TSLA is intentionally *not* in the tech set even though it would qualify — the code special-cases it because Tesla historically has very low correlation with other megacap tech (it tracks its own narrative).

### Positive semi-definiteness

Cholesky requires the correlation matrix be positive semi-definite (PSD). The structure used here — block diagonal with uniform off-block entries — is PSD as long as all correlations are in `[-1, 1]` and the off-block value (0.3) is not larger than the smallest on-block value (0.5). The shipped values satisfy this, so `np.linalg.cholesky` never raises.

If a future contributor adds a new sector with intra-group correlation < 0.3, the matrix may become indefinite. The simulator would crash on `_rebuild_cholesky` rather than produce silently wrong correlations — failure-loud is the right behavior.

## Random Shock Events

Each step, each ticker has a small probability (~0.001) of an instantaneous 2–5% move:

```python
if random.random() < self._event_prob:
    shock_magnitude = random.uniform(0.02, 0.05)
    shock_sign = random.choice([-1, 1])
    self._prices[ticker] *= 1 + shock_magnitude * shock_sign
```

At 2 ticks/sec × 10 tickers = 20 trials/sec, the expected rate is **~1 event every 50 seconds** across the whole watchlist (roughly **once every 8 minutes per individual ticker**). Enough to keep the dashboard alive without overwhelming the realistic baseline behavior.

## Seed Prices

The 10 default-watchlist tickers have hand-picked seed prices that approximate their real prices at project creation (so a user opening the app sees plausible numbers):

```python
SEED_PRICES = {
    "AAPL": 190.00,  "GOOGL": 175.00,  "MSFT": 420.00,
    "AMZN": 185.00,  "TSLA": 250.00,   "NVDA": 800.00,
    "META": 500.00,  "JPM":  195.00,   "V":    280.00,
    "NFLX": 600.00,
}
```

**Unknown tickers** (added via `POST /api/watchlist` or by the LLM) get a seed price randomly drawn from `random.uniform(UNKNOWN_TICKER_PRICE_MIN, UNKNOWN_TICKER_PRICE_MAX)` — currently `$20.00–$400.00` per PLAN.md §6 — and default GBM params (`sigma=0.25, mu=0.05`). The simulator accepts any ticker symbol and treats it as a generic mid-cap equity from that point on.

## Per-Ticker Parameters

Volatilities are hand-tuned to match observed long-run characteristics of each name:

```python
TICKER_PARAMS = {
    "AAPL":  {"sigma": 0.22, "mu": 0.05},
    "GOOGL": {"sigma": 0.25, "mu": 0.05},
    "MSFT":  {"sigma": 0.20, "mu": 0.05},
    "AMZN":  {"sigma": 0.28, "mu": 0.05},
    "TSLA":  {"sigma": 0.50, "mu": 0.03},   # High vol
    "NVDA":  {"sigma": 0.40, "mu": 0.08},   # High vol, strong drift
    "META":  {"sigma": 0.30, "mu": 0.05},
    "JPM":   {"sigma": 0.18, "mu": 0.04},   # Low vol (bank)
    "V":     {"sigma": 0.17, "mu": 0.04},   # Low vol (payments)
    "NFLX":  {"sigma": 0.35, "mu": 0.05},
}
DEFAULT_PARAMS = {"sigma": 0.25, "mu": 0.05}
```

## Parameter Justification

The standard GBM scaling rule is **`σ_t = σ_annual × √t`** where `t` is measured in years. So given an annualized sigma, the expected standard deviation of log-returns over any interval is `sigma * sqrt(interval_in_years)`.

### Expected daily standard deviation

A trading day = 1/252 year, so `σ_daily = σ_annual / √252 ≈ σ_annual / 15.87`.

| Ticker | σ (annual) | σ (daily) | Daily $-range on seed price (±1σ) |
|--------|-----------:|----------:|----------------------------------:|
| JPM    | 0.18 | 1.13% | ±$2.21 on $195 |
| V      | 0.17 | 1.07% | ±$2.99 on $280 |
| MSFT   | 0.20 | 1.26% | ±$5.29 on $420 |
| AAPL   | 0.22 | 1.39% | ±$2.64 on $190 |
| GOOGL  | 0.25 | 1.58% | ±$2.76 on $175 |
| AMZN   | 0.28 | 1.76% | ±$3.26 on $185 |
| META   | 0.30 | 1.89% | ±$9.45 on $500 |
| NFLX   | 0.35 | 2.20% | ±$13.22 on $600 |
| NVDA   | 0.40 | 2.52% | ±$20.16 on $800 |
| TSLA   | 0.50 | 3.15% | ±$7.88 on $250 |

These line up with real-world observation: JPM/V hover near 1% daily moves, the broad megacap tech cohort lives in 1.5–2%, and TSLA / NVDA produce the chunky multi-percent days the dashboard wants to show.

### Per-tick standard deviation (for the curious)

At `dt ≈ 8.48 × 10⁻⁸`, `√dt ≈ 2.91 × 10⁻⁴`.

For AAPL (σ = 0.22): per-tick log-return std ≈ `0.22 × 2.91 × 10⁻⁴ ≈ 6.4 × 10⁻⁵` → **0.0064% per 500 ms tick** → ~1.2¢ on a $190 price. This is right at the visual sweet spot — small enough to look like real tape, large enough to flash green/red noticeably every few seconds.

### Drift swamped by diffusion

Per tick, the drift term `(mu - σ²/2) × dt` is `O(10⁻⁹)`, three orders of magnitude smaller than the diffusion term. **The mu values barely affect what the user sees in a single session.** Over a multi-day backtest they'd matter; in a demo where the page is open for minutes, drift is essentially decorative. This is intentional — we don't want NVDA to feel like a guaranteed money pump.

### Random-event contribution

A 2–5% shock event is **~3 standard deviations** of a daily move for AAPL (~1.4%) and ~1.5σ for TSLA. So events look notable but not implausible. At the configured rate, expect **roughly one shock event per minute** across a 10-ticker watchlist — frequent enough that the chat panel and the chart have something to react to, sparse enough that the underlying GBM behavior dominates.

## Implementation

### File layout

The shipped layout differs slightly from the original sketch:

```
backend/app/market/
  ├── seed_prices.py     # SEED_PRICES, TICKER_PARAMS, DEFAULT_PARAMS,
  │                        CORRELATION_GROUPS, *_CORR constants
  └── simulator.py       # GBMSimulator class + SimulatorDataSource
```

`seed_prices.py` is constants only. `simulator.py` contains both `GBMSimulator` (pure math, sync) and `SimulatorDataSource` (the async `MarketDataSource` wrapper). Splitting them lets you unit-test the math without booting an event loop.

### `GBMSimulator` (excerpt)

```python
class GBMSimulator:
    TRADING_SECONDS_PER_YEAR = 252 * 6.5 * 3600          # 5,896,800
    DEFAULT_DT = 0.5 / TRADING_SECONDS_PER_YEAR          # ~8.48e-8

    def __init__(self, tickers, dt=DEFAULT_DT, event_probability=0.001):
        self._dt = dt
        self._event_prob = event_probability
        self._tickers: list[str] = []
        self._prices: dict[str, float] = {}
        self._params: dict[str, dict[str, float]] = {}
        self._cholesky: np.ndarray | None = None
        for t in tickers:
            self._add_ticker_internal(t)
        self._rebuild_cholesky()

    def step(self) -> dict[str, float]:
        n = len(self._tickers)
        if n == 0:
            return {}
        z_ind = np.random.standard_normal(n)
        z = self._cholesky @ z_ind if self._cholesky is not None else z_ind

        result = {}
        for i, ticker in enumerate(self._tickers):
            mu, sigma = self._params[ticker]["mu"], self._params[ticker]["sigma"]
            drift = (mu - 0.5 * sigma**2) * self._dt
            diffusion = sigma * math.sqrt(self._dt) * z[i]
            self._prices[ticker] *= math.exp(drift + diffusion)

            if random.random() < self._event_prob:
                shock = random.uniform(0.02, 0.05) * random.choice([-1, 1])
                self._prices[ticker] *= 1 + shock

            result[ticker] = round(self._prices[ticker], 2)
        return result
```

### `SimulatorDataSource` (the async wrapper)

```python
class SimulatorDataSource(MarketDataSource):
    def __init__(self, price_cache, update_interval=0.5, event_probability=0.001):
        self._cache = price_cache
        self._interval = update_interval
        self._event_prob = event_probability
        self._sim: GBMSimulator | None = None
        self._task: asyncio.Task | None = None

    async def start(self, tickers):
        self._sim = GBMSimulator(tickers=tickers, event_probability=self._event_prob)
        # Seed the cache immediately so SSE clients get data before the first tick
        for t in tickers:
            p = self._sim.get_price(t)
            if p is not None:
                self._cache.update(ticker=t, price=p)
        self._task = asyncio.create_task(self._run_loop(), name="simulator-loop")

    async def _run_loop(self):
        while True:
            try:
                if self._sim:
                    for t, p in self._sim.step().items():
                        self._cache.update(ticker=t, price=p)
            except Exception:
                logger.exception("Simulator step failed")
            await asyncio.sleep(self._interval)
```

Two implementation details worth flagging:

1. **Seed-on-start.** `start()` writes the initial prices into the cache *before* the loop begins. Without this, a client connecting to the SSE stream in the first 500 ms after startup would see nothing.
2. **Loop never dies.** A bare `except Exception` around `step()` logs and continues. A random NumPy hiccup or arithmetic edge case shouldn't kill the simulator and leave the dashboard frozen.

## Adding / Removing Tickers Mid-Session

`add_ticker` and `remove_ticker` mutate `_tickers` and trigger a `_rebuild_cholesky()`. The matrix rebuild is O(n²) but `n` is small (< 50 even with generous LLM-driven watchlist growth), so the cost is negligible.

When a ticker is added:
- Seed price = `SEED_PRICES.get(ticker, random.uniform(UNKNOWN_TICKER_PRICE_MIN, UNKNOWN_TICKER_PRICE_MAX))` — `$20.00–$400.00` per PLAN.md §6
- Params = `TICKER_PARAMS.get(ticker, dict(DEFAULT_PARAMS))` (`dict(...)` to avoid sharing the mutable default across tickers)
- The simulator immediately seeds the cache so the new ticker has a price before its first GBM step

When a ticker is removed, both the simulator's internal state and the `PriceCache` entry are dropped.

## Behavior Guarantees

- **Prices never go negative.** GBM is multiplicative — `exp(...)` is always positive — and shock events use multiplicative `(1 ± shock)`. The worst-case shock is `−5%`, so a single tick can't more than halve a price.
- **Prices are deterministic given a seeded RNG.** Tests can call `random.seed(x)` and `np.random.seed(x)` before constructing the simulator to get reproducible price paths.
- **Per-tick cost is O(n²) in the worst case** (the Cholesky multiply), but with `n < 50` this is microseconds on any modern machine. The simulator is not the bottleneck — the 500 ms sleep is.
- **No I/O.** The simulator never touches the network or disk. It's safe to construct in any test or CLI tool without environment setup.

## Testing

The simulator is covered by `backend/tests/market/test_simulator.py` (math and Cholesky) and `test_simulator_source.py` (async lifecycle, cache integration). Key invariants the tests pin down:

- A step on `n=0` tickers returns `{}` and does not call NumPy.
- Adding a ticker rebuilds the Cholesky matrix and the new ticker appears in subsequent steps.
- Removing a ticker drops it from both the simulator and the cache.
- With `event_probability=0.0`, prices follow pure GBM (no shocks). With `event_probability=1.0`, every step shocks every ticker — useful for testing the shock branch in isolation.
- The async source seeds the cache during `start()` (before the loop runs even once).

## Related Documents

- `MARKET_INTERFACE.md` — the `MarketDataSource` ABC and `PriceCache` that the simulator plugs into
- `MASSIVE_API.md` — the real-data alternative selected when `MASSIVE_API_KEY` is set
- `PLAN.md` §6 — product-level requirements (push-on-change SSE, unknown-ticker autoseed, etc.)
