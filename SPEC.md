# SPEC — ASX Stock Snapshot Dashboard

Implementation-agnostic functional specification. The goal is to describe **what** the
application must do, not how. Any language/framework can implement this against the
same external ASX data API.

---

## Overview

A browser-based dashboard that ingests bulk ASX (Australian Securities Exchange)
company snapshot data from an external HTTP API, engineers financial features
(valuation, growth, dividends/franking, liquidity), and presents interactive rankings,
matrices, charts, and historical trend views with user-controlled filters.

---

## External Data Source (ASX API)

The app talks to a single HTTP REST service with three endpoints:

- `GET /health` → JSON with `data.status` ("healthy") and `data.refreshes` (an object
  whose keys are the available stock symbols).
- `GET /export/company?start_date=&end_date=` → a **CSV** bulk export of all company
  snapshots (one row per company per snapshot date). May be large.
- `GET /company/{symbol}/history?start_date=&end_date=` → JSON with `data`: an array of
  per-date records for a single company.

Requirements:
- All API calls must have configurable timeouts (separate connect and read timeouts).
- Bulk CSV and per-company history fetches must retry on failure with exponential
  backoff (up to a configurable max retries).
- The API base URL must be configurable via environment variable with a sensible
  default.
- Network/parse failures must be surfaced to the user without crashing the dashboard.

---

## Data Model — expected raw columns

The bulk CSV / history JSON contain a flat record per snapshot. The app auto-detects
columns by name; the following are expected (case-insensitive fallbacks in parentheses):

- **Symbol**: `symbol` (`Symbol`, `ticker`, `Ticker`, `company`, `companyName`, …)
- **Date**: `fetched_at` (`date`, `Date`, `timestamp`, …) — any column whose name
  contains "date" or "time"
- **Price close**: `priceClose` (`price_close`, `close`, `last_price`, `last`, …)
- Other OHLCV: `priceHigh`, `priceLow`, `priceOpen`, `volume` / `volumeAverage`
- Valuation inputs: `numOfShares`, `priceEarningsRatio`, `priceToCash`,
  `freeCashFlowYield`
- Dividend inputs: `yieldAnnual`, `frankingPercent`, `dividend`, `earningsPerShare`,
  `dividendCurrency`
- Liquidity inputs: `priceAsk`, `priceBid`, `priceFiftyTwoWeekHigh`,
  `priceFiftyTwoWeekLow`, `priceDayHigh`, `priceDayLow`, `volumeAverage`
- `incomeStatement`: a stringified list of period objects, each with `revenue`,
  `netIncome`, `cashFlow`, `period` (e.g. `"2025A"`). May be single-quoted (Python
  dict repr) or JSON.
- `fPeriodEndDate`: an Excel serial date number.

The dashboard must tolerate missing columns (treat as null) and auto-detect the
symbol/date/price columns when exact names are absent.

---

## Feature Engineering Pipeline

Given the bulk snapshot data, produce **one row per symbol** (using only the **latest**
snapshot per symbol, determined by the max date) with the following engineered features:

### Valuation & size
- `market_cap` = `numOfShares` × `priceClose`
- `cleaned_pe` = `priceEarningsRatio` with sentinel placeholder values (e.g.
  `-99999.99` or anything ≤ that sentinel) replaced with null
- `earnings_yield` = `1 / cleaned_pe` (null if `cleaned_pe` is null)
- `price_to_cash` = `priceToCash` with the same sentinel cleaning
- `free_cash_flow_yield` = `freeCashFlowYield` with its own near-zero sentinel
  (`≈ -1.00000010000001e-05`) replaced with null

### Growth & financial health (from `incomeStatement`, sorted by period)
- `yoy_revenue_growth` = (latest revenue − prior revenue) / prior revenue (requires ≥2
  statements)
- `latest_net_margin` = latest netIncome / latest revenue
- `earnings_quality_ratio` = latest cashFlow / latest netIncome
- `net_income_direction` = sign(latest netIncome − prior netIncome)
- `revenue_cagr_3y` = (latest revenue / revenue 3 years ago) ^ (1/3) − 1 (requires ≥4
  statements; both revenues must be > 0)
- All of the above are null when insufficient statements exist

### Dividend & franking (ASX-specific)
- `raw_dividend_yield` = `yieldAnnual`
- `franking_credit_multiplier` = 1 + (frankingPercent/100) × (taxRate / (1 −
  taxRate)), where `taxRate` = 0.30 (Australian company tax rate). No/missing franking
  → multiplier of 1.0.
- `grossed_up_yield` = `raw_dividend_yield` × `franking_credit_multiplier`
- `dividend_payout_ratio` = `dividend` / `earningsPerShare` (safe division; null on
  zero/null denominator)
- `dividend_currency_risk` = boolean, True when `dividendCurrency` is not "AUD"

### Liquidity & technical
- `bid_ask_spread_pct` = (ask − bid) / priceClose
- `range_position_52w` = (priceClose − 52wLow) / (52wHigh − 52wLow) (null if range is 0)
- `volume_turnover_ratio` = volumeAverage / numOfShares
- `intraday_volatility` = (dayHigh − dayLow) / priceClose

### Date
- `period_end_date` = `fPeriodEndDate` converted from Excel serial (1900 date system,
  base 1899-12-30 to account for the phantom leap-year bug) to a real date

### Pipeline rules
- All divisions must be safe: null/NaN result when the denominator is null or zero.
- Sentinel placeholders must never appear in outputs — they become nulls.
- The pipeline must return an empty result set for empty input and must raise a clear
  error if no symbol column can be detected.

---

## Growth Ranking Computation

Given the bulk snapshot (all rows, not just latest) and a selected **growth factor**
(any numeric column, defaulting to priceClose):

- For each symbol, sort its rows by date, take the first and last value of the factor,
  and compute `growth_pct = (last − first) / first × 100`.
- Drop rows where the factor or symbol is null, and drop symbols whose first value is 0.
- Return the top **N** symbols (N configurable, default 10, range 5–50) sorted by
  `growth_pct` descending, with columns: `symbol`, `start_value`, `end_value`,
  `growth_pct` (rounded to 2 decimals).

---

## Historical Trend Computation

Given a list of selected symbols:
- Fetch each symbol's history from `GET /company/{symbol}/history`.
- Concatenate all records, auto-detect date/price/symbol columns, drop rows with null
  date or price, coerce to numeric/datetime, and sort chronologically.
- Return a combined dataset usable for a multi-line price-over-time chart.
- Symbols whose fetch fails must not abort the whole request; failures must be reported
  to the user.

---

## Dashboard UI Requirements

### Global
- Wide layout, page title "ASX Stock Analysis Dashboard".
- On load: fetch the bulk CSV; on failure show an error and stop rendering.
- Display a header summary: record count, unique symbol count, and the latest snapshot
  date.
- All expensive data loads and computations must be cached with a TTL (~1 hour) and a
  bounded cache size; the bulk source load must be cached once and interactive filters
  applied outside the cache.

### Sidebar controls
- **Stock selection** (multi-select) for trend analysis, populated from the `/health`
  endpoint's symbol list. Default: none.
- **Growth factor** selector (single-select) populated from available numeric columns,
  defaulting to the price-close column.
- **Top N** slider (5–50, default 10).
- **Feature filters** (only when engineered features are available):
  - Minimum market cap in $M (number input, default 0)
  - Minimum grossed-up yield in % (number input, default 0)
  - "Franked dividends only" checkbox (default off)
  - These filters restrict the engineered-feature dataset and, by extension, which
    symbols appear in the other tabs.

### Tabs (five views)

**1. Growth Rankings**
- Header showing the selected growth factor.
- A bar chart of the top N symbols by growth %, colored by growth value on a
  red→yellow→green scale, x-axis labels rotated ~45°.
- A data table of the same results (index hidden).
- Fallback messages when no factor is available or no growth data exists.

**2. Valuation Matrix**
- A table of `symbol`, market cap (in $M), cleaned P/E, earnings yield,
  price-to-cash, free cash-flow yield, with number formatting per column.
- A bar chart of market-cap size distribution bucketed into Micro / Small / Mid / Large
  (boundaries $50M / $200M / $2B), colored by bucket.
- A scatter of cleaned P/E (x) vs free cash-flow yield (y), point size by market cap,
  color by earnings yield, labeled by symbol.
- Empty-state messages when features are missing or filters exclude everything.

**3. Dividend & Franking Analysis**
- A table of `symbol`, raw yield %, franking multiplier, grossed-up yield %, payout
  ratio %, and a currency-risk badge ("⚠ FX Risk" vs "AUD").
- A bar chart of the top 15 symbols by grossed-up yield, colored by yield, with the FX
  badge as text label.
- A pie chart of franked vs unfranked count (franked = multiplier > 1.0).
- Same empty-state behavior as Tab 2.

**4. Liquidity & Technical Risk**
- A table of `symbol`, bid-ask spread %, 52-week range position %, volume turnover %,
  intraday volatility %, with per-column number formatting.
- A scatter of volume turnover (x) vs bid-ask spread (y), colored by intraday
  volatility, point size by 52-week range position, labeled by symbol (only rows with
  valid, non-negative range position).
- A histogram of 52-week range position (0=low, 1=high), ~20 bins.
- Same empty-state behavior.

**5. Trend Over Time**
- Only renders work when this tab is active (lazy/expensive).
- For the sidebar-selected symbols, fetch per-symbol history, build the combined
  dataset, and render a multi-line line chart of the selected growth factor (or price
  close) over time, one line per symbol.
- Also show a data table of date, symbol, and the plotted metric.
- Empty-state when no symbols are selected or no trend data is available; error message
  on fetch failure.

### Rendering & performance expectations
- Only the active tab's expensive content should be computed; hidden tabs must not
  trigger API calls or heavy chart rendering.
- Stable UI (title, sidebar, tab bar, data summary) must render before slow loads
  complete; a loading placeholder must be shown during unavoidable waits.
- Caches must be bounded (TTL and/or max entries) so memory does not grow unbounded
  across varying filter/factor/symbol selections.

### Error handling
- Bulk load failure → error banner + halt.
- API unreachable for the symbol list → error banner, trend selection disabled/empty.
- Feature-engineering failure → warning banner; tabs that need features show an
  "unavailable" info state instead of crashing.
- Per-symbol history failure → does not abort other symbols; user is informed.

---

## Non-functional requirements

- **Containerization**: must run as a container exposing port 8501 (or a configurable
  port), with health probes against the root path.
- **Configuration**: API base URL, server port, and headless/CORS settings must be
  environment-configurable; no secrets are currently required.
- **Kubernetes**: must ship Deployment (≥1 replica), Service, and Ingress manifests
  with matching ports and working health/readiness probes.
- **Reproducibility**: dependencies must be pinned; the build must not bundle the local
  virtualenv, tests, git history, or secret files.
- **Tests**: unit tests must cover the feature-engineering pipeline (valuation,
  growth, dividends/franking, liquidity, sentinel cleaning, Excel date conversion,
  income-statement parsing, multi-symbol deduplication), the growth-ranking
  computation, trend preparation, and column auto-detection. Tests must be hermetic
  (no live external API required).
- **Resilience**: all API calls retry with exponential backoff; all numeric parsing
  and divisions are null-safe; missing data degrades gracefully rather than throwing.
