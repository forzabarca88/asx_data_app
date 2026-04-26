# PLAN.md

---

Modern Python web front-end for `company/<id>/history` with TDD and `uv`

---

## 1. Project setup

### 1.1 Create repo and base structure

- **Goal:** Have a clean, minimal project skeleton ready for TDD.
- **Steps:**

  1. Create project directory, e.g. `asx-history-ui/`.
  2. Inside, create:

     - `src/` (application code)
     - `tests/` (test suite)
     - `pyproject.toml` (managed by `uv`)
     - `README.md`
     - `PLAN.md` (this file)

### 1.2 Initialize Python environment with `uv`

- **Goal:** Use `uv` for all Python tooling.
- **Steps:**

  1. Create a virtual environment:

     ```bash
     uv venv
     ```

  2. Activate it (shell-dependent).
  3. Add core dependencies (web + tests + plotting):

     ```bash
     uv pip install fastapi uvicorn[standard] jinja2 httpx pydantic plotly
     uv pip install pytest pytest-asyncio httpx[http2]
     ```

  4. (Optional) Add `ruff` / `black` later for lint/format.

- **Outcome:** Reproducible environment using `uv pip` and `uv run`.

---

## 2. High-level architecture

- **Backend framework:** FastAPI (Python-based, async, modern).
- **Rendering:** Server-side HTML via Jinja2 templates.
- **Charts:** Plotly (Python) rendered to HTML/JS and embedded in templates.
- **HTTP client:** `httpx` to call the existing API at `http://192.168.0.50:30181`.
- **Structure:**

  - `src/app/main.py` — FastAPI app entrypoint.
  - `src/app/config.py` — configuration (base API URL, etc.).
  - `src/app/models.py` — Pydantic models for `health` and `history` responses.
  - `src/app/client.py` — API client wrapper around `httpx`.
  - `src/app/views.py` — route handlers.
  - `src/app/templates/` — Jinja2 templates.
  - `src/app/charts.py` — chart-building helpers using Plotly.

---

## 3. Global testing setup (before any feature)

### 3.1 Add basic test configuration

- **Goal:** Ensure test runner works before writing feature tests.
- **Tests to write (failing first):**

  - `tests/test_smoke.py`:
    - `test_pytest_runs()` — trivial assertion `assert True` (should pass).
    - `test_app_imports()` — `from app.main import app` and assert it's a FastAPI instance (will fail until `app` exists).

- **Implementation steps (after tests fail):**

  1. Create `src/app/__init__.py`.
  2. Create `src/app/main.py` with:

     ```python
     from fastapi import FastAPI

     app = FastAPI(title="ASX History UI")
     ```

  3. Run tests:

     ```bash
     uv run pytest
     ```

- **Outcome:** Basic FastAPI app object exists and tests pass.

---

## 4. Configuration and domain models

### 4.1 Config for base API URL

- **Tests to write (failing first):**

  - `tests/test_config.py`:
    - `test_default_base_url()` — import `settings` and assert `settings.base_api_url == "http://192.168.0.50:30181"`.

- **Implementation:**

  1. Create `src/app/config.py`:

     ```python
     from pydantic import BaseSettings

     class Settings(BaseSettings):
         base_api_url: str = "http://192.168.0.50:30181"

     settings = Settings()
     ```

  2. Run tests with `uv run pytest`.

### 4.2 Pydantic models for `/health` and `/company/<id>/history`

- **Assumption:**

  - `/health` returns a list or structure containing ASX codes (e.g. `["IAG", "CBA", ...]` or objects with a `code` field).
  - `/company/<id>/history` returns a list of records with fields like `date`, `priceClose`, `priceDayHigh`, `priceDayLow`, `volume`, etc.

- **Tests to write (failing first):**

  - `tests/test_models.py`:
    - `test_company_code_model_parses_health_item()` — given a sample `/health` payload, Pydantic model extracts `code`.
    - `test_history_item_model_parses_prices()` — given sample history JSON, model exposes `priceClose`, `priceDayHigh`, etc. as floats and `date` as a date/datetime.

- **Implementation:**

  1. Create `src/app/models.py` with Pydantic models, e.g.:

     ```python
     from datetime import date
     from pydantic import BaseModel

     class Company(BaseModel):
         code: str

     class HistoryItem(BaseModel):
         date: date
         priceClose: float
         priceDayHigh: float
         priceDayLow: float
         volume: int | None = None
     ```

  2. Adjust models to match actual API shape once confirmed.
  3. Re-run tests.

---

## 5. API client wrapper

### 5.1 Client for `/health` and `/company/<id>/history`

- **Goal:** Encapsulate HTTP calls and parsing.
- **Tests to write (failing first):**

  - `tests/test_client.py`:
    - Use `pytest` + `pytest-asyncio`.
    - Mock `httpx.AsyncClient` (or use `httpx.MockTransport`) to simulate:
      - `/health` returning a known payload.
      - `/company/IAG/history` returning known history data.
    - Tests:
      - `test_get_companies_returns_company_models()`
      - `test_get_company_history_returns_history_items()`

- **Implementation:**

  1. Create `src/app/client.py`:

     ```python
     import httpx
     from .config import settings
     from .models import Company, HistoryItem

     class ApiClient:
         def __init__(self, base_url: str | None = None):
             self.base_url = base_url or settings.base_api_url

         async def get_companies(self) -> list[Company]:
             async with httpx.AsyncClient(base_url=self.base_url) as client:
                 resp = await client.get("/health")
                 resp.raise_for_status()
                 data = resp.json()
                 # adapt to actual shape
                 return [Company(code=item["code"]) for item in data]

         async def get_company_history(self, code: str) -> list[HistoryItem]:
             async with httpx.AsyncClient(base_url=self.base_url) as client:
                 resp = await client.get(f"/company/{code}/history")
                 resp.raise_for_status()
                 data = resp.json()
                 return [HistoryItem(**item) for item in data]
     ```

  2. Re-run tests and refine parsing as needed.

---

## 6. Web app skeleton and home page

### 6.1 Root route and template engine

- **Goal:** Have a basic HTML page served at `/`.
- **Tests to write (failing first):**

  - `tests/test_main_routes.py`:
    - Use `httpx.AsyncClient` with `from fastapi.testclient import TestClient` or `httpx.AsyncClient(app=app, base_url="http://test")`.
    - `test_root_returns_200_and_html()` — GET `/` returns status 200 and `text/html` content type.

- **Implementation:**

  1. Add Jinja2 templates directory: `src/app/templates/`.
  2. In `src/app/main.py`:
     - Configure `Jinja2Templates`.
     - Add root route that renders `index.html`.
  3. Create `src/app/templates/base.html` and `index.html` with minimal HTML.
  4. Run tests with `uv run pytest`.

### 6.2 Display list of companies on home page

- **Goal:** Show available ASX codes from `/health` as links.
- **Tests to write (failing first):**

  - In `tests/test_main_routes.py`:
    - Mock `ApiClient.get_companies`.
    - `test_home_lists_companies()` — response HTML contains each mocked company code and links to `/company/<code>`.

- **Implementation:**

  1. Inject `ApiClient` into routes (e.g. via dependency injection).
  2. In `views` or directly in `main.py`, implement `/` route:
     - Call `ApiClient.get_companies()`.
     - Render `index.html` with `companies` context.
  3. Update `index.html` to loop over `companies` and render links.

- **Outcome:** Home page lists ASX codes with navigation.

---

## 7. Company history page with visualization

### 7.1 Basic history table for a company

- **Goal:** `/company/{code}` page showing tabular history.
- **Tests to write (failing first):**

  - In `tests/test_company_history_page.py`:
    - Mock `ApiClient.get_company_history`.
    - `test_company_history_page_renders_table()`:
      - GET `/company/IAG`.
      - Assert status 200.
      - Assert HTML contains table headers: `Date`, `Close`, `High`, `Low`, etc.
      - Assert at least one row with expected values.

- **Implementation:**

  1. Add route `/company/{code}` in `main.py` or `views.py`.
  2. Use `ApiClient.get_company_history(code)` to fetch data.
  3. Create `templates/company_history.html`:
     - Extend `base.html`.
     - Render a table with rows for each `HistoryItem`.

### 7.2 PriceClose line chart

- **Goal:** Visualize `priceClose` over time.
- **Tests to write (failing first):**

  - In `tests/test_charts.py`:
    - `test_price_close_chart_generates_plotly_figure()`:
      - Given a list of `HistoryItem`, `build_price_close_chart(history)` returns a Plotly `Figure` with:
        - x-axis = dates
        - y-axis = `priceClose`
    - In `tests/test_company_history_page.py`:
      - `test_company_history_page_contains_price_close_chart_div()`:
        - Response HTML contains a `<div>` or `<script>` marker for the chart (e.g. `id="price-close-chart"`).

- **Implementation:**

  1. Create `src/app/charts.py`:

     ```python
     import plotly.graph_objects as go
     from .models import HistoryItem

     def build_price_close_chart(history: list[HistoryItem]):
         fig = go.Figure()
         fig.add_trace(
             go.Scatter(
                 x=[item.date for item in history],
                 y=[item.priceClose for item in history],
                 mode="lines",
                 name="Close"
             )
         )
         fig.update_layout(
             title="Closing Price",
             xaxis_title="Date",
             yaxis_title="Price"
         )
         return fig
     ```

  2. In the `/company/{code}` route:
     - Call `build_price_close_chart(history)`.
     - Convert to HTML:

       ```python
       from plotly.io import to_html
       chart_html = to_html(fig, include_plotlyjs="cdn", full_html=False)
       ```

     - Pass `chart_html` into template context.

  3. In `company_history.html`, render `{{ chart_html | safe }}` inside a container with `id="price-close-chart"`.

- **Outcome:** Interactive line chart for `priceClose` appears on the company page.

### 7.3 Additional charts: priceDayHigh, priceDayLow, volume

- **Goal:** Visualize more fields (e.g. high/low as band, volume as bar chart).
- **Tests to write (failing first):**

  - In `tests/test_charts.py`:
    - `test_high_low_chart_uses_high_and_low_values()`.
    - `test_volume_chart_uses_volume_values()`.
  - In `tests/test_company_history_page.py`:
    - `test_company_history_page_contains_high_low_chart_div()`.
    - `test_company_history_page_contains_volume_chart_div()`.

- **Implementation:**

  1. Extend `charts.py` with:

     - `build_high_low_chart(history: list[HistoryItem])`
     - `build_volume_chart(history: list[HistoryItem])`

  2. In `/company/{code}` route:
     - Build all charts and pass HTML snippets to template.
  3. Update `company_history.html` to render multiple chart sections.

- **Outcome:** Page shows multiple interactive charts for key metrics.

---

## 8. UX and interaction improvements

### 8.1 Company selection from dropdown on home page

- **Goal:** Allow user to select a company from a dropdown and navigate.
- **Tests to write (failing first):**

  - `tests/test_home_company_selection.py`:
    - `test_home_contains_company_select_form()` — HTML contains `<select>` with company codes.
    - (Optional) Use integration-style test to simulate form submission and redirect to `/company/{code}`.

- **Implementation:**

  1. Update `index.html` to include a `<form>` with `<select name="code">`.
  2. Add route `/select-company` (POST) that redirects to `/company/{code}`.
  3. Ensure tests pass.

### 8.2 Basic styling

- **Goal:** Make UI readable and modern-ish without heavy JS frameworks.
- **Tests to write (failing first):**

  - Very light tests, e.g.:
    - `test_base_template_includes_main_stylesheet_link()`.

- **Implementation:**

  1. Add `static/` directory with a simple CSS file.
  2. Configure FastAPI `StaticFiles`.
  3. Link stylesheet in `base.html`.

---

## 9. Error handling and edge cases

### 9.1 Handle unknown company code

- **Tests to write (failing first):**

  - `tests/test_error_handling.py`:
    - Mock `ApiClient.get_company_history` to raise `httpx.HTTPStatusError` for unknown code.
    - `test_unknown_company_shows_error_message()` — HTML contains a user-friendly error message.

- **Implementation:**

  1. Wrap history fetch in try/except.
  2. On error, render template with error banner instead of crashing.

### 9.2 Handle empty history

- **Tests to write (failing first):**

  - `test_empty_history_shows_no_data_message()` — when history list is empty, page shows "No history available" and no charts.

- **Implementation:**

  1. In route, if `history` is empty:
     - Skip chart generation.
     - Pass a flag to template to show "no data" message.

---

## 10. Running the app and tests

### 10.1 Test commands

- **Run full test suite:**

  ```bash
  uv run pytest
  ```

- **Run individual test file:**

  ```bash
  uv run pytest tests/test_smoke.py
  ```

- **Run with verbose output:**

  ```bash
  uv run pytest -v
  ```

- **Run with coverage:**

  ```bash
  uv run pytest --cov=src --cov-report=html
  ```

- **Run tests with coverage report:**

  ```bash
  uv run pytest --cov=src --cov-report=term-missing
  ```

---

## 11. Development workflow

### 11.1 Adding new features

1. Write failing tests first (TDD).
2. Make tests pass.
3. Refactor if needed.
4. Add documentation.

### 11.2 Running the application

```bash
uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

Access at `http://localhost:8000`

---

## 12. Project structure

```
asx-history-ui/
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── client.py
│   │   ├── views.py
│   │   ├── charts.py
│   │   └── templates/
│   │       ├── base.html
│   │       ├── index.html
│   │       └── company_history.html
│   └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── test_smoke.py
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_client.py
│   ├── test_main_routes.py
│   ├── test_company_history_page.py
│   ├── test_charts.py
│   ├── test_home_company_selection.py
│   ├── test_error_handling.py
│   └── conftest.py
├── pyproject.toml
├── README.md
└── PLAN.md
```

---

## 13. Notes

- All tests should follow the TDD principle: write failing tests first, then implement.
- Use `uv run` for all Python commands to ensure the correct environment is used.
- Keep dependencies minimal and focused on the task.
- Document any assumptions about the API response format in comments or a separate file.