# E2E Tests — ASX Stock Analysis Dashboard

Playwright-based end-to-end tests that verify the Streamlit app works correctly against a mock ASX API server.

## Prerequisites

- Python 3.12+ with an active virtual environment
- `playwright` installed with browser binaries:
  ```bash
  playwright install chromium
  ```
- `responses` installed for API mocking:
  ```bash
  python -m pip install responses
  ```

## Running Tests

```bash
# Full E2E suite
pytest tests/e2e/ -v

# Single test file
pytest tests/e2e/test_app_structure.py -v

# Single test
pytest tests/e2e/test_app_structure.py::test_page_title -v

# Visible browser (for debugging)
pytest tests/e2e/ --headed --slow-mo 100 -v

# Verbose output
pytest tests/e2e/ -v -s
```

## How It Works

1. **Mock API Server** (`mock_api_server.py`) — A lightweight HTTP server on port `19000` that returns deterministic responses matching the ASX API format. No external network calls.

2. **Streamlit App** — Launched via subprocess with `ASX_API_BASE_URL=http://127.0.0.1:19000` so it connects to the mock server instead of the real API.

3. **Playwright Browser** — Headless Chromium navigates to `http://localhost:8501` and verifies the app renders correctly.

### Mock API Endpoints

| Endpoint | Response |
|----------|----------|
| `GET /health` | JSON: `{"data": {"status": "healthy", "refreshes": {...}}}` |
| `GET /export/company` | CSV with 5 mock stocks (BHP, CBA, CSL, WES, WBC) |
| `GET /company/{symbol}/history` | JSON: `{"data": [{"symbol", "priceClose", "fetched_at"}]}` |

Date filtering (`start_date`, `end_date` query params) is supported on bulk CSV and history endpoints.

## Fixtures

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `mock_api_server` | session | Starts/stops the mock HTTP server |
| `start_app` | session | Starts/stops Streamlit once for all tests (warm cache) |
| `browser` | session | Headless Chromium instance |
| `page` | function | Fresh page per test (1920×1080 viewport) |
| `app_url` | function | Returns `http://localhost:8501` |
| `mock_api_url` | function | Returns `http://127.0.0.1:19000` |
| `screenshot` | function | Captures and saves screenshots to `/tmp/screens/e2e/` |

## Screenshots

Screenshots are saved to `/tmp/screens/e2e/` and can be used for debugging test failures:

```python
def test_something(page, screenshot):
    page.goto(app_url)
    # ... test logic ...
    if something_failed:
        screenshot()  # Saves as test_something.png
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--headed` | Run browser in visible (non-headless) mode |
| `--slow-mo <ms>` | Slow down Playwright operations for visual debugging |
