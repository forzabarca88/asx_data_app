\# PLAN.md



Modern Python web front-end for `company/<id>/history` with TDD and `uv`



\---



\## 1. Project setup



\### 1.1 Create repo and base structure



\- \*\*Goal:\*\* Have a clean, minimal project skeleton ready for TDD.

\- \*\*Steps:\*\*

&#x20; 1. Create project directory, e.g. `asx-history-ui/`.

&#x20; 2. Inside, create:

&#x20;    - `src/` (application code)

&#x20;    - `tests/` (test suite)

&#x20;    - `pyproject.toml` (managed by `uv`)

&#x20;    - `README.md`

&#x20;    - `PLAN.md` (this file)



\### 1.2 Initialize Python environment with `uv`



\- \*\*Goal:\*\* Use `uv` for all Python tooling.

\- \*\*Steps:\*\*

&#x20; 1. Create a virtual environment:



&#x20;    ```bash

&#x20;    uv venv

&#x20;    ```



&#x20; 2. Activate it (shell-dependent).

&#x20; 3. Add core dependencies (web + tests + plotting):



&#x20;    ```bash

&#x20;    uv pip install fastapi uvicorn\[standard] jinja2 httpx pydantic plotly

&#x20;    uv pip install pytest pytest-asyncio httpx\[http2]

&#x20;    ```



&#x20; 4. (Optional) Add `ruff` / `black` later for lint/format.



\- \*\*Outcome:\*\* Reproducible environment using `uv pip` and `uv run`.



\---



\## 2. High-level architecture



\- \*\*Backend framework:\*\* FastAPI (Python-based, async, modern).

\- \*\*Rendering:\*\* Server-side HTML via Jinja2 templates.

\- \*\*Charts:\*\* Plotly (Python) rendered to HTML/JS and embedded in templates.

\- \*\*HTTP client:\*\* `httpx` to call the existing API at `http://192.168.0.50:30181`.

\- \*\*Structure:\*\*



&#x20; - `src/app/main.py` — FastAPI app entrypoint.

&#x20; - `src/app/config.py` — configuration (base API URL, etc.).

&#x20; - `src/app/models.py` — Pydantic models for `health` and `history` responses.

&#x20; - `src/app/client.py` — API client wrapper around `httpx`.

&#x20; - `src/app/views.py` — route handlers.

&#x20; - `src/app/templates/` — Jinja2 templates.

&#x20; - `src/app/charts.py` — chart-building helpers using Plotly.



\---



\## 3. Global testing setup (before any feature)



\### 3.1 Add basic test configuration



\- \*\*Goal:\*\* Ensure test runner works before writing feature tests.

\- \*\*Tests to write (failing first):\*\*

&#x20; - `tests/test\_smoke.py`:

&#x20;   - `test\_pytest\_runs()` — trivial assertion `assert True` (should pass).

&#x20;   - `test\_app\_imports()` — `from app.main import app` and assert it’s a FastAPI instance (will fail until `app` exists).



\- \*\*Implementation steps (after tests fail):\*\*

&#x20; 1. Create `src/app/\_\_init\_\_.py`.

&#x20; 2. Create `src/app/main.py` with:



&#x20;    ```python

&#x20;    from fastapi import FastAPI



&#x20;    app = FastAPI(title="ASX History UI")

&#x20;    ```



&#x20; 3. Run tests:



&#x20;    ```bash

&#x20;    uv run pytest

&#x20;    ```



\- \*\*Outcome:\*\* Basic FastAPI app object exists and tests pass.



\---



\## 4. Configuration and domain models



\### 4.1 Config for base API URL



\- \*\*Tests to write (failing first):\*\*

&#x20; - `tests/test\_config.py`:

&#x20;   - `test\_default\_base\_url()` — import `settings` and assert `settings.base\_api\_url == "http://192.168.0.50:30181"`.



\- \*\*Implementation:\*\*

&#x20; 1. Create `src/app/config.py`:



&#x20;    ```python

&#x20;    from pydantic import BaseSettings



&#x20;    class Settings(BaseSettings):

&#x20;        base\_api\_url: str = "http://192.168.0.50:30181"



&#x20;    settings = Settings()

&#x20;    ```



&#x20; 2. Run tests with `uv run pytest`.



\### 4.2 Pydantic models for `/health` and `/company/<id>/history`



\- \*\*Assumption:\*\*  

&#x20; - `/health` returns a list or structure containing ASX codes (e.g. `\["IAG", "CBA", ...]` or objects with a `code` field).

&#x20; - `/company/<id>/history` returns a list of records with fields like `date`, `priceClose`, `priceDayHigh`, `priceDayLow`, `volume`, etc.



\- \*\*Tests to write (failing first):\*\*

&#x20; - `tests/test\_models.py`:

&#x20;   - `test\_company\_code\_model\_parses\_health\_item()` — given a sample `/health` payload, Pydantic model extracts `code`.

&#x20;   - `test\_history\_item\_model\_parses\_prices()` — given sample history JSON, model exposes `priceClose`, `priceDayHigh`, etc. as floats and `date` as a date/datetime.



\- \*\*Implementation:\*\*

&#x20; 1. Create `src/app/models.py` with Pydantic models, e.g.:



&#x20;    ```python

&#x20;    from datetime import date

&#x20;    from pydantic import BaseModel



&#x20;    class Company(BaseModel):

&#x20;        code: str



&#x20;    class HistoryItem(BaseModel):

&#x20;        date: date

&#x20;        priceClose: float

&#x20;        priceDayHigh: float

&#x20;        priceDayLow: float

&#x20;        volume: int | None = None

&#x20;    ```



&#x20; 2. Adjust models to match actual API shape once confirmed.

&#x20; 3. Re-run tests.



\---



\## 5. API client wrapper



\### 5.1 Client for `/health` and `/company/<id>/history`



\- \*\*Goal:\*\* Encapsulate HTTP calls and parsing.



\- \*\*Tests to write (failing first):\*\*

&#x20; - `tests/test\_client.py`:

&#x20;   - Use `pytest` + `pytest-asyncio`.

&#x20;   - Mock `httpx.AsyncClient` (or use `httpx.MockTransport`) to simulate:

&#x20;     - `/health` returning a known payload.

&#x20;     - `/company/IAG/history` returning known history data.

&#x20;   - Tests:

&#x20;     - `test\_get\_companies\_returns\_company\_models()`

&#x20;     - `test\_get\_company\_history\_returns\_history\_items()`



\- \*\*Implementation:\*\*

&#x20; 1. Create `src/app/client.py`:



&#x20;    ```python

&#x20;    import httpx

&#x20;    from .config import settings

&#x20;    from .models import Company, HistoryItem



&#x20;    class ApiClient:

&#x20;        def \_\_init\_\_(self, base\_url: str | None = None):

&#x20;            self.base\_url = base\_url or settings.base\_api\_url



&#x20;        async def get\_companies(self) -> list\[Company]:

&#x20;            async with httpx.AsyncClient(base\_url=self.base\_url) as client:

&#x20;                resp = await client.get("/health")

&#x20;                resp.raise\_for\_status()

&#x20;                data = resp.json()

&#x20;                # adapt to actual shape

&#x20;                return \[Company(code=item\["code"]) for item in data]



&#x20;        async def get\_company\_history(self, code: str) -> list\[HistoryItem]:

&#x20;            async with httpx.AsyncClient(base\_url=self.base\_url) as client:

&#x20;                resp = await client.get(f"/company/{code}/history")

&#x20;                resp.raise\_for\_status()

&#x20;                data = resp.json()

&#x20;                return \[HistoryItem(\*\*item) for item in data]

&#x20;    ```



&#x20; 2. Re-run tests and refine parsing as needed.



\---



\## 6. Web app skeleton and home page



\### 6.1 Root route and template engine



\- \*\*Goal:\*\* Have a basic HTML page served at `/`.



\- \*\*Tests to write (failing first):\*\*

&#x20; - `tests/test\_main\_routes.py`:

&#x20;   - Use `httpx.AsyncClient` with `from fastapi.testclient import TestClient` or `httpx.AsyncClient(app=app, base\_url="http://test")`.

&#x20;   - `test\_root\_returns\_200\_and\_html()` — GET `/` returns status 200 and `text/html` content type.



\- \*\*Implementation:\*\*

&#x20; 1. Add Jinja2 templates directory: `src/app/templates/`.

&#x20; 2. In `src/app/main.py`:

&#x20;    - Configure `Jinja2Templates`.

&#x20;    - Add root route that renders `index.html`.

&#x20; 3. Create `src/app/templates/base.html` and `index.html` with minimal HTML.



&#x20; 4. Run tests with `uv run pytest`.



\### 6.2 Display list of companies on home page



\- \*\*Goal:\*\* Show available ASX codes from `/health` as links.



\- \*\*Tests to write (failing first):\*\*

&#x20; - In `tests/test\_main\_routes.py`:

&#x20;   - Mock `ApiClient.get\_companies`.

&#x20;   - `test\_home\_lists\_companies()` — response HTML contains each mocked company code and links to `/company/<code>`.



\- \*\*Implementation:\*\*

&#x20; 1. Inject `ApiClient` into routes (e.g. via dependency injection).

&#x20; 2. In `views` or directly in `main.py`, implement `/` route:

&#x20;    - Call `ApiClient.get\_companies()`.

&#x20;    - Render `index.html` with `companies` context.

&#x20; 3. Update `index.html` to loop over `companies` and render links.



\- \*\*Outcome:\*\* Home page lists ASX codes with navigation.



\---



\## 7. Company history page with visualization



\### 7.1 Basic history table for a company



\- \*\*Goal:\*\* `/company/{code}` page showing tabular history.



\- \*\*Tests to write (failing first):\*\*

&#x20; - In `tests/test\_company\_history\_page.py`:

&#x20;   - Mock `ApiClient.get\_company\_history`.

&#x20;   - `test\_company\_history\_page\_renders\_table()`:

&#x20;     - GET `/company/IAG`.

&#x20;     - Assert status 200.

&#x20;     - Assert HTML contains table headers: `Date`, `Close`, `High`, `Low`, etc.

&#x20;     - Assert at least one row with expected values.



\- \*\*Implementation:\*\*

&#x20; 1. Add route `/company/{code}` in `main.py` or `views.py`.

&#x20; 2. Use `ApiClient.get\_company\_history(code)` to fetch data.

&#x20; 3. Create `templates/company\_history.html`:

&#x20;    - Extend `base.html`.

&#x20;    - Render a table with rows for each `HistoryItem`.



\### 7.2 PriceClose line chart



\- \*\*Goal:\*\* Visualize `priceClose` over time.



\- \*\*Tests to write (failing first):\*\*

&#x20; - In `tests/test\_charts.py`:

&#x20;   - `test\_price\_close\_chart\_generates\_plotly\_figure()`:

&#x20;     - Given a list of `HistoryItem`, `build\_price\_close\_chart(history)` returns a Plotly `Figure` with:

&#x20;       - x-axis = dates

&#x20;       - y-axis = `priceClose`

&#x20;   - In `tests/test\_company\_history\_page.py`:

&#x20;     - `test\_company\_history\_page\_contains\_price\_close\_chart\_div()`:

&#x20;       - Response HTML contains a `<div>` or `<script>` marker for the chart (e.g. `id="price-close-chart"`).



\- \*\*Implementation:\*\*

&#x20; 1. Create `src/app/charts.py`:



&#x20;    ```python

&#x20;    import plotly.graph\_objects as go

&#x20;    from .models import HistoryItem



&#x20;    def build\_price\_close\_chart(history: list\[HistoryItem]):

&#x20;        fig = go.Figure()

&#x20;        fig.add\_trace(

&#x20;            go.Scatter(

&#x20;                x=\[item.date for item in history],

&#x20;                y=\[item.priceClose for item in history],

&#x20;                mode="lines",

&#x20;                name="Close"

&#x20;            )

&#x20;        )

&#x20;        fig.update\_layout(

&#x20;            title="Closing Price",

&#x20;            xaxis\_title="Date",

&#x20;            yaxis\_title="Price"

&#x20;        )

&#x20;        return fig

&#x20;    ```



&#x20; 2. In the `/company/{code}` route:

&#x20;    - Call `build\_price\_close\_chart(history)`.

&#x20;    - Convert to HTML:



&#x20;      ```python

&#x20;      from plotly.io import to\_html

&#x20;      chart\_html = to\_html(fig, include\_plotlyjs="cdn", full\_html=False)

&#x20;      ```



&#x20;    - Pass `chart\_html` into template context.



&#x20; 3. In `company\_history.html`, render `{{ chart\_html | safe }}` inside a container with `id="price-close-chart"`.



\- \*\*Outcome:\*\* Interactive line chart for `priceClose` appears on the company page.



\### 7.3 Additional charts: priceDayHigh, priceDayLow, volume



\- \*\*Goal:\*\* Visualize more fields (e.g. high/low as band, volume as bar chart).



\- \*\*Tests to write (failing first):\*\*

&#x20; - In `tests/test\_charts.py`:

&#x20;   - `test\_high\_low\_chart\_uses\_high\_and\_low\_values()`.

&#x20;   - `test\_volume\_chart\_uses\_volume\_values()`.

&#x20; - In `tests/test\_company\_history\_page.py`:

&#x20;   - `test\_company\_history\_page\_contains\_high\_low\_chart\_div()`.

&#x20;   - `test\_company\_history\_page\_contains\_volume\_chart\_div()`.



\- \*\*Implementation:\*\*

&#x20; 1. Extend `charts.py` with:



&#x20;    - `build\_high\_low\_chart(history: list\[HistoryItem])`

&#x20;    - `build\_volume\_chart(history: list\[HistoryItem])`



&#x20; 2. In `/company/{code}` route:

&#x20;    - Build all charts and pass HTML snippets to template.

&#x20; 3. Update `company\_history.html` to render multiple chart sections.



\- \*\*Outcome:\*\* Page shows multiple interactive charts for key metrics.



\---



\## 8. UX and interaction improvements



\### 8.1 Company selection from dropdown on home page



\- \*\*Goal:\*\* Allow user to select a company from a dropdown and navigate.



\- \*\*Tests to write (failing first):\*\*

&#x20; - `tests/test\_home\_company\_selection.py`:

&#x20;   - `test\_home\_contains\_company\_select\_form()` — HTML contains `<select>` with company codes.

&#x20;   - (Optional) Use integration-style test to simulate form submission and redirect to `/company/{code}`.



\- \*\*Implementation:\*\*

&#x20; 1. Update `index.html` to include a `<form>` with `<select name="code">`.

&#x20; 2. Add route `/select-company` (POST) that redirects to `/company/{code}`.

&#x20; 3. Ensure tests pass.



\### 8.2 Basic styling



\- \*\*Goal:\*\* Make UI readable and modern-ish without heavy JS frameworks.



\- \*\*Tests to write (failing first):\*\*

&#x20; - Very light tests, e.g.:

&#x20;   - `test\_base\_template\_includes\_main\_stylesheet\_link()`.



\- \*\*Implementation:\*\*

&#x20; 1. Add `static/` directory with a simple CSS file.

&#x20; 2. Configure FastAPI `StaticFiles`.

&#x20; 3. Link stylesheet in `base.html`.



\---



\## 9. Error handling and edge cases



\### 9.1 Handle unknown company code



\- \*\*Tests to write (failing first):\*\*

&#x20; - `tests/test\_error\_handling.py`:

&#x20;   - Mock `ApiClient.get\_company\_history` to raise `httpx.HTTPStatusError` for unknown code.

&#x20;   - `test\_unknown\_company\_shows\_error\_message()` — HTML contains a user-friendly error message.



\- \*\*Implementation:\*\*

&#x20; 1. Wrap history fetch in try/except.

&#x20; 2. On error, render template with error banner instead of crashing.



\### 9.2 Handle empty history



\- \*\*Tests to write (failing first):\*\*

&#x20; - `test\_empty\_history\_shows\_no\_data\_message()` — when history list is empty, page shows “No history available” and no charts.



\- \*\*Implementation:\*\*

&#x20; 1. In route, if `history` is empty:

&#x20;    - Skip chart generation.

&#x20;    - Pass a flag to template to show “no data” message.



\---



\## 10. Running the app and tests



\### 10.1 Test commands



\- \*\*Run full test suite:\*\*



&#x20; ```bash

&#x20; uv run pytest



