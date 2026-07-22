# ISSUES — ASX Stock Snapshot Dashboard

Audit of the codebase against Streamlit 1.60 best practices and general code-quality
criteria. Each issue is tagged with a severity, the file(s) involved, and a concrete
remediation a small worker agent can follow.

Severity legend: 🔴 high · 🟠 medium · 🟡 low

---

## 1. Streamlit / UX

### 1.1 🔴 All five tabs compute on every rerun, even hidden ones
**Files:** `app.py` (the `tab1..tab5 = st.tabs([...])` block and each `with tabN:` block)

`st.tabs` is called **without `on_change="rerun"`**, so Streamlit renders the body of
every tab on every script run regardless of which tab is visible. The Trend tab even
triggers API fetches (`compute_trend`) when it is not the active tab. With Streamlit
1.60 this is both wasteful and a source of greyed/stale UI.

**Remediation (worker):**
- Change the tab creation to dynamic tabs:
  ```python
  tab1, tab2, tab3, tab4, tab5 = st.tabs(
      ["Growth Rankings", "Valuation Matrix", "Dividend Analysis",
       "Liquidity & Risk", "Trend Over Time"],
      on_change="rerun",
  )
  ```
- Guard each tab's body with its `.open` flag, e.g.:
  ```python
  if tab1.open:
      with tab1:
          ...existing tab1 body...
  ```
- Repeat for `tab2`–`tab5`. The expensive Trend fetch should only run when `tab5.open`
  is True. Do **not** leave the `with tabN:` block unconditional.
- Reference: `.agents/skills/developing-with-streamlit/references/performance.md`
  ("Tabs with expensive content").

### 1.2 🟠 Plotly used where Vega-based native charts are preferred
**Files:** `app.py` (every `px.bar`, `px.scatter`, `px.line`, `px.histogram`, `px.pie` +
`st.plotly_chart`)

The Streamlit skill prefers native Vega-based charts (`st.bar_chart`, `st.line_chart`,
`st.scatter_chart`, `st.altair_chart`) over Plotly for common cases — they are lighter,
render server-side, and avoid the WebGL-context limit Plotly hits with many charts.

**Remediation (worker):**
- Convert the simple bar/line/histogram/pie charts to `st.bar_chart` / `st.line_chart` /
  `st.hist_frame` or Altair (`st.altair_chart`).
- Keep Plotly only for charts that genuinely need it (e.g., the bubble/scatter with
  `size` + `color` encodings could stay as `st.scatter_chart` with `size`/`color`
  columns, or `st.altair_chart` with a layered spec).
- This is a recommendation, not a correctness fix; do not break existing behavior.

### 1.3 🟡 No `.streamlit/config.toml` / no theme
**Files:** missing `.streamlit/config.toml`

The app has no theme configuration and relies entirely on Streamlit defaults.

**Remediation (worker):**
- Create `.streamlit/config.toml` with a `[theme]` block (and optionally
`[server] headless = true`). Use a provided template from
`.agents/skills/developing-with-streamlit/assets/templates/themes/configs/` (e.g.
`financial-dashboard`) as a starting point. Copy it into `.streamlit/config.toml`.

### 1.4 🟡 Sidebar filters not batched in a form
**Files:** `app.py` sidebar block

Each sidebar `number_input` / `checkbox` / `multiselect` change triggers a full rerun.
For the three feature filters (min market cap, min yield, franked-only) a `st.form`
would batch them into a single rerun on submit.

**Remediation (worker):** Wrap the "Feature Filters" block (`min_market_cap`,
`min_yield`, `show_only_franked`) in `with st.form("filters", border=False):` and add an
`st.form_submit_button("Apply filters")`. Apply the filtering only after submit. Leave
the symbol multiselect, growth factor, and top-N slider outside the form (they are used
by multiple tabs and benefit from immediate feedback). See
`references/performance.md` "Forms to batch interactions".

### 1.5 🟡 `st.info("Fetching history…")` flashes on every cached rerun
**Files:** `app.py` Tab 5

The "Fetching history for N symbols…" info message is shown unconditionally even when
`compute_trend` returns from cache instantly, which is misleading.

**Remediation (worker):** Either remove the message, or only show it the first time by
checking `st.session_state` / a cache-hit indicator. Simplest: drop the `st.info` line
and rely on Streamlit's native run indicator.

---

## 2. Caching / Performance

### 2.1 🟠 Unbounded parameterized caches (no `max_entries`)
**Files:** `app.py` — `compute_top_n`, `compute_trend`, `compute_engineered`

These `@st.cache_data(ttl=3600)` functions are called with varying arguments
(`n`, `factor`, `symbols` list, filtered DataFrames). Each distinct argument set creates
a new cache entry with no size bound. Over a long session this grows memory indefinitely.

**Remediation (worker):** Add `max_entries` to each, e.g.:
```python
@st.cache_data(ttl=3600, max_entries=64)
def compute_top_n(df, n, factor): ...
@st.cache_data(ttl=3600, max_entries=64)
def compute_trend(symbols): ...
@st.cache_data(ttl=3600, max_entries=8)
def compute_engineered(df): ...
```
Reference: `references/performance.md` "Prevent unbounded cache growth".

### 2.2 🟠 `compute_top_n` is cached on the *filtered* DataFrame — wrong granularity
**Files:** `app.py` Tab 1

`growth_df` is `df` filtered by the engineered-feature filters
(`allowed_symbols = set(filtered_eng["symbol"])`), producing a new DataFrame object every
time the sidebar filters change. Because `@st.cache_data` hashes the DataFrame input,
every filter combination misses the cache and stores a new entry — so the cache is both
ineffective and unbounded.

**Remediation (worker):** Cache the unfiltered `compute_top_n(df, n, factor)` on the full
`df` (source data), then apply the `allowed_symbols` filter **outside** the cached
function before passing to `px.bar` / `st.dataframe`. Pattern from
`references/best-practices.md` "Performance": cache the expensive source load, apply
cheap filters outside.

### 2.3 🟡 No loading skeleton / reserved slot for the slow bulk load
**Files:** `app.py` top-level `df = load_data()` (runs before any UI renders)

`load_data()` (bulk CSV) runs at the very top of the script, so on a cache miss the
entire page is blocked behind it with no UI painted and no skeleton.

**Remediation (worker):** Render the title and sidebar chrome first, reserve a container
slot for the data-dependent area, and run `load_data()` inside `with slot.skeleton():`,
writing results into `slot`. See `references/performance.md` "Render stable UI before
slow work". (Lower priority because the bulk load is cached for 1h.)

---

## 3. Data Processing / `data_processor.py`

### 3.1 🟠 `parse_income_statement` uses blanket `replace("'", '"')` — fragile
**Files:** `data_processor.py` `parse_income_statement`

It converts single-quoted Python-dict strings to JSON by replacing every `'` with `"`.
If any field value contains an apostrophe (e.g., a company name or a period label like
`"O'Brien"`) the JSON parse breaks and the whole record is silently dropped.

**Remediation (worker):** Replace the naive replace with `ast.literal_eval` (the strings
are already valid Python literals), then normalize to dicts:
```python
import ast
def parse_income_statement(statement_str):
    if pd.isna(statement_str) or not statement_str:
        return []
    try:
        statements = ast.literal_eval(str(statement_str))
        return sorted(statements, key=lambda x: str(x.get("period", "")))
    except (ValueError, SyntaxError, TypeError):
        return []
```
Keep the existing sort-by-period behavior. Update the test
`test_parse_income_statement` if needed (it should still pass).

### 3.2 🟡 `convert_excel_date` truncates fractional days (drops time component)
**Files:** `data_processor.py` `convert_excel_date`

`int(float(serial))` discards any fractional-day time portion. For `fPeriodEndDate`
this is probably fine (dates only), but the function is generic.

**Remediation (worker):** If sub-day precision is ever needed, use
`base + pd.Timedelta(days=float(serial))` instead of `int(...)`. Otherwise document the
date-only assumption in the docstring. Low priority.

### 3.3 🟡 `detect_available_factors` exposes unrelated numeric columns as growth factors
**Files:** `data_processor.py` `detect_available_factors`

The fallback loop appends **every** numeric column (e.g., `numOfShares`,
`volumeAverage`, `priceEarningsRatio`) to the growth-factor dropdown. Users can select
"numOfShares" as a "growth factor", which is meaningless for price-growth ranking.

**Remediation (worker):** Restrict the fallback to a curated allow-list of price/volume
metrics, or at minimum exclude obvious non-timeseries numerics
(`numOfShares`, `priceEarningsRatio`, `priceToCash`, `frankingPercent`, `yieldAnnual`,
`*Sentinel` fields). Keep the explicit candidate list at the top of the function.

### 3.4 🟡 Per-symbol fetch errors silently swallowed
**Files:** `data_processor.py` `fetch_and_prepare_trend_data`

`except Exception: continue` drops any symbol whose history fetch fails, with no log or
UI signal. The user sees fewer lines than selected with no explanation.

**Remediation (worker):** Collect failed symbols into a list and return/raise them, or
at minimum `print`/`logging.warning` the symbol + exception. Have `app.py` show an
`st.warning` listing the symbols that failed. (Don't change the success path.)

### 3.5 🟡 `calculate_top_n_growth` relies on `agg(["first","last"])` after sort
**Files:** `data_processor.py` `calculate_top_n_growth`

This works because the DataFrame is sorted by `[symbol, date]` first, but it is fragile
to future refactors that change sort order. `groupby.first/last` are order-dependent.

**Remediation (worker):** Make the intent explicit by using
`groupby(symbol_col)[factor_col].agg(start_value="first", end_value="last")` only after
an explicit sort, and add an inline comment that the sort is load-bearing. Optionally
switch to `.iloc[0]` / `.iloc[-1]` via a helper to be unambiguous. Low priority.

### 3.6 🟡 No unit tests for column-detection functions
**Files:** `tests/test_processor.py`

`detect_date_column`, `detect_price_column`, `detect_symbol_column`, and
`detect_available_factors` have no direct tests despite being the backbone of the
auto-schema logic.

**Remediation (worker):** Add small tests (mirror the existing style with `assert` +
`print("PASS: ...")`) covering: a known-schema frame, a frame with only lowercase
columns, and a frame missing the expected columns (should return `None` / empty list).
Add each new test to the `tests` list in `__main__`.

---

## 4. API Client / `api_client.py`

### 4.1 🔴 `BASE_URL` is hardcoded to a private IP with no env override
**Files:** `api_client.py`

`BASE_URL = "http://192.168.0.50:30181"` is a literal. It cannot be overridden for
local dev, staging, tests, or a different cluster without editing source. It also bakes
a network assumption into the container image.

**Remediation (worker):**
```python
import os
BASE_URL = os.environ.get("ASX_API_BASE_URL", "http://192.168.0.50:30181")
```
Then set `ASX_API_BASE_URL` via the k8s `env` block in `deployment.yaml`. Keep the
current value as the default so behavior is unchanged when unset.

### 4.2 🟠 `get_bulk_csv_data` streams but then loads `response.content` into memory
**Files:** `api_client.py` `get_bulk_csv_data`

`stream=True` is set but `pd.read_csv(io.BytesIO(response.content), ...)` buffers the
entire body in memory anyway, defeating streaming.

**Remediation (worker):** Either drop `stream=True` (since the body is fully buffered
regardless), or genuinely stream with `pd.read_csv(response.raw, ...)` and chunksize.
Simplest correct fix: remove `stream=True` and the misleading comment, keep the retry
logic. Document that the bulk export is loaded whole.

### 4.3 🟡 Retry sleeps block the Streamlit script thread
**Files:** `api_client.py` (both retry loops)

`time.sleep(5 * 2**...)` blocks the event loop / script thread during backoff, freezing
the UI with no feedback.

**Remediation (worker):** Wrap the call in `st.status`/`st.spinner` at the `app.py` call
site, or surface progress. A lower-effort fix is to reduce `max_retries` to 2 and the
base sleep. Not a correctness issue.

### 4.4 🟡 No timeout on `requests` import path / inconsistent timeout shapes
**Files:** `api_client.py`

Timeouts use tuples `(connect, read)` which is fine, but the values are inconsistent
(connect 10–30, read 60–600). Not a bug; just hard to tune.

**Remediation (worker):** Extract named constants (`CONNECT_TIMEOUT`, `READ_TIMEOUT`)
and reuse. Optional.

---

## 5. Kubernetes / Docker

### 5.1 🔴 Ingress backend port (80) does not match Service port (8501)
**Files:** `k8s/ingress.yaml` vs `k8s/service.yaml`

`ingress.yaml` routes to `service: asx-dashboard-service` on `port.number: 80`, but
`service.yaml` only exposes `port: 8501` (targetPort 8501, nodePort 30181). There is no
port 80 on the Service, so the Ingress will return 503/connection-refused.

**Remediation (worker):** Change `ingress.yaml` backend `port.number` from `80` to
`8501`. Verify with `kubectl describe ingress` after applying.

### 5.2 🟠 Service type inconsistency (NodePort vs README's "LoadBalancer")
**Files:** `k8s/service.yaml`, `k8s/README.md`

`service.yaml` is `type: NodePort` with a fixed `nodePort: 30181`, but `k8s/README.md`
says "LoadBalancer Service to expose the application" and references a `<EXTERNAL-IP>`.
Also `30181` is the same nodePort as the hardcoded `BASE_URL` port — if the ASX API and
this dashboard ever run on the same cluster nodes, the ports collide.

**Remediation (worker):** Decide one strategy and align docs:
- Either set `service.yaml` `type: LoadBalancer` and drop the fixed `nodePort`, or
- Keep `NodePort` and fix the README text to say NodePort + node IP, not External-IP.
Also confirm `30181` is not already used by the ASX API Service on the same cluster; if
it is, change the dashboard nodePort (e.g. `30282`) and update any references.

### 5.3 🟠 No `.dockerignore` — image bloat and secret risk
**Files:** `k8s/Dockerfile` (`COPY . .`), missing `.dockerignore`

`COPY . .` copies `.venv/` (hundreds of MB), `.git/`, `tests/`, `__pycache__/`, and
potentially `.streamlit/secrets.toml` into the image.

**Remediation (worker):** Create a `.dockerignore` at repo root containing at least:
```
.venv/
venv/
.git/
__pycache__/
*.pyc
.pytest_cache/
tests/
.streamlit/secrets.toml
*.log
```

### 5.4 🟡 Python version mismatch between Dockerfile and local venv
**Files:** `k8s/Dockerfile` (`python:3.11-slim`) vs `.venv` (Python 3.13)

The container runs 3.11 while the local venv is 3.13. Features like
`pd.to_datetime(..., format="mixed")` behave the same, but the divergence is a drift
risk.

**Remediation (worker):** Pin the Dockerfile base to match the intended runtime, e.g.
`python:3.13-slim`, or document 3.11 as the supported target and test there. Pick one.

### 5.5 🟡 `requirements.txt` has no version pins
**Files:** `requirements.txt`

`streamlit`, `pandas`, `numpy`, `plotly`, `requests` are all unpinned. A fresh install
can pull breaking versions (Streamlit 2.x API changes, pandas 3.0 dtype changes).

**Remediation (worker):** Pin to the installed versions (run
`./.venv/bin/pip freeze | grep -E 'streamlit|pandas|numpy|plotly|requests'`) and commit
pinned `requirements.txt`, or add a `requirements-dev.txt` / use `uv pip compile`. Keep
`pytest` out of the runtime image (add a separate test stage or dev requirements).

### 5.6 🟡 2 replicas × in-memory cache = duplicated API load
**Files:** `k8s/deployment.yaml` (replicas: 2), `app.py` `@st.cache_data`

Streamlit's `@st.cache_data` is per-process. With 2 replicas each pod independently
fetches the bulk CSV / histories, doubling API load and giving inconsistent cache TTLs
across pods.

**Remediation (worker):** Either run `replicas: 1`, or move caching to a shared layer
(e.g., a CDN/ingress cache for the bulk export, or a shared memoization store). At
minimum document the trade-off in `k8s/README.md`.

---

## 6. Tests

### 6.1 🟠 `test_api.py` depends on a live external API
**Files:** `tests/test_api.py`

The health test hits the real `192.168.0.50:30181` API and `raise`s (fails the suite)
when it is unreachable. This makes the test suite non-hermetic and CI-unfriendly.

**Remediation (worker):** Mock `requests.get` (e.g., with `unittest.mock.patch`) and
assert `get_health`/`get_available_symbols` parse a canned JSON response. Keep a
separate, opt-in smoke test (e.g., `test_api_live.py` skipped by default) for the real
endpoint. Ensure `pytest tests/ -v` passes offline.

### 6.2 🟡 README claims "16 tests" — verify count after changes
**Files:** `README.md`

The count is currently correct (15 in `test_processor.py` + 1 in `test_api.py`) but
will drift if tests are added/removed in issue 3.6 / 6.1.

**Remediation (worker):** After test changes, recount and update the "16 tests" line in
`README.md`, or reword to "unit tests covering all processor functions and API health"
without a number.

### 6.3 🟡 No `pytest` in `requirements.txt` / no test config
**Files:** `requirements.txt`, missing `pytest.ini`/`pyproject.toml`

`pytest` is imported/run but not declared. Tests also use `print("PASS: ...")` style and
can be run via `python tests/test_processor.py` directly, but the README documents
`pytest`.

**Remediation (worker):** Add a `requirements-dev.txt` with `pytest`, or a `[project.optional-dependencies] dev = ["pytest"]` in a `pyproject.toml`. Optionally add a minimal `pyproject.toml` with `[tool.pytest.ini_options] pythonpath = ["."]`.

---

## 7. General / Misc

### 7.1 🟡 `app.py` is a single ~400-line script
**Files:** `app.py`

All UI, tab logic, and filter wiring live in one file. It works, but the per-tab blocks
are good candidates for `app_pages/` + `st.navigation` (the skill's recommended
multipage pattern) or at least helper functions in a `ui/` module.

**Remediation (worker):** Optional refactor — extract each tab body into a function in
a new `ui/tabs.py` (e.g., `render_growth_tab(df, ...)`), keeping `app.py` as the
orchestrator. Do **not** switch to `st.navigation` unless the user wants true multipage
routing; tabs are fine for this app. Reference: `references/code-organization.md`.

### 7.2 🟡 No logging; diagnostics use `print`/`st.error` only
**Files:** `data_processor.py`, `api_client.py`, `app.py`

There is no `logging` configuration; failures surface only as Streamlit error banners or
silent `continue`. In k8s this makes debugging hard.

**Remediation (worker):** Add `import logging; log = logging.getLogger("asx")` and
replace silent `except: continue` / bare `print` with `log.warning(..., exc_info=True)`.
Configure a basic handler in `app.py` entry. Low priority.

### 7.3 🟡 No `.streamlit/secrets.toml` handling (no secrets used yet)
**Files:** n/a — informational

The app currently needs no secrets (the ASX API is unauthenticated). If auth is added,
follow `references/best-practices.md` "Secrets and queries": use `st.secrets`, never
hardcode, and gitignore `.streamlit/secrets.toml` (`.gitignore` already covers `.env*`
but not `.streamlit/`).

**Remediation (worker):** Add `.streamlit/secrets.toml` to `.gitignore` proactively.

---

## Priority order for a worker agent

1. **5.1** Ingress port mismatch (broken k8s routing) — quick, high impact.
2. **4.1** `BASE_URL` env override — quick, unblocks deployment flexibility.
3. **1.1** Dynamic tabs (`on_change="rerun"` + `.open` guards) — biggest UX/perf win.
4. **5.3** Add `.dockerignore` — quick, prevents image bloat + secret leakage.
5. **3.1** `parse_income_statement` → `ast.literal_eval` — correctness.
6. **2.1 / 2.2** Cache bounds + filter granularity — stability under load.
7. **6.1** Hermetic API test — unblocks CI.
8. **5.2 / 5.4 / 5.5** k8s + dependency hygiene.
9. Remaining 🟡 items as time permits.
