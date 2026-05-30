## Project Overview
**Goal:** Build a highly performant Python dashboard for deep analysis of ASX stock trends.
**Core Features:** Top N stock growth analysis, Trend-over-time visualization for selected stocks.
**Tech Stack:** Python 3.x, Streamlit (UI), Plotly (Visualizations), Pandas (Data processing), Requests (API Client).
**API Base URL:** `http://192.168.0.50:30181`

---

## Phase 1: Project Setup & Dependencies
**Objective:** Initialize the project structure and install required libraries.

1.  **Create Project Directory Structure:**
    *   `app.py` (Main Streamlit dashboard)
    *   `api_client.py` (API fetching logic)
    *   `data_processor.py` (Pandas data crunching)
    *   `requirements.txt` (Dependencies)
    *   `tests/` (Directory for validation scripts)
2.  **Define `requirements.txt`:**
    *   Add: `streamlit`, `pandas`, `plotly`, `requests`.
3.  **Agent Validation Step:**
    *   *Action:* Run `pip install -r requirements.txt`.
    *   *Check:* Run `python -c "import streamlit, pandas, plotly, requests; print('Phase 1 Success')"` and ensure no import errors occur.

---

## Phase 2: API Client Module (`api_client.py`)
**Objective:** Create modular functions to interface with the ASX Data API.

1.  **Setup Base Configuration:**
    *   Define `BASE_URL = "http://192.168.0.50:30181"`.
2.  **Implement `get_health()`:**
    *   Fetch `GET /health` to extract a list of available stock symbols. (The API description states it returns last refresh date for each symbol).
3.  **Implement `get_bulk_csv_data(start_date=None, end_date=None)`:**
    *   Fetch `GET /export/company`. 
    *   *Performance Note:* Use `requests.get(..., stream=True)` and read it directly into a Pandas DataFrame using `pd.read_csv(response.raw)`. This is essential for the Top N analysis without spamming the API with individual company requests.
4.  **Implement `get_company_history(symbol, start_date=None, end_date=None)`:**
    *   Fetch `GET /company/{company_id}/history`.
    *   Parse the `data` field from the `JSONResponse` schema into a Pandas DataFrame.
5.  **Agent Validation Step:**
    *   *Action:* Write a quick test script `tests/test_api.py` that asserts `get_health()` returns a 200 OK and successfully returns a list/dict of symbols.
    *   *Check:* Run `python tests/test_api.py`.

---

## Phase 3: Data Processing Engine (`data_processor.py`)
**Objective:** Transform raw API data into metrics for the UI.

1.  **Implement `calculate_top_n_growth(df, n=10)`:**
    *   *Input:* The bulk historical DataFrame fetched via `/export/company`.
    *   *Logic:* 
        *   Identify the oldest and newest record for each `symbol` based on the `fetched_at` (or explicit date) column.
        *   Extract the price/closing value (LLM must inspect the CSV columns dynamically, e.g., looking for `price`, `close`, or `last_price`).
        *   Calculate Growth %: `((Latest Price - Oldest Price) / Oldest Price) * 100`.
        *   Sort descending by growth percentage and return the top `n` rows.
2.  **Implement `prepare_trend_data(df, symbols)`:**
    *   Filter the bulk dataframe (or merge individual histories) for the selected `symbols`.
    *   Ensure the date column is a datetime object and sort chronologically.
3.  **Agent Validation Step:**
    *   *Action:* Create `tests/test_processor.py`. Mock a small Pandas DataFrame with columns `['symbol', 'fetched_at', 'price']`, pass it to `calculate_top_n_growth()`.
    *   *Check:* Assert the function correctly calculates percentage growth and returns the top stocks sorted correctly. Run `python tests/test_processor.py`.

---

## Phase 4: Dashboard UI Implementation (`app.py`)
**Objective:** Build the interactive interface using Streamlit.

1.  **Initial Configuration:**
    *   Use `st.set_page_config(page_title="ASX Dashboard", layout="wide")`.
2.  **Data Caching (Crucial for Performance):**
    *   Wrap the API client calls in `@st.cache_data(ttl=3600)` (cache for 1 hour).
    *   Create a load function: `load_data()` that triggers `get_bulk_csv_data()` and returns the master DataFrame.
3.  **Sidebar Controls:**
    *   Add a "Refresh Data" button. If clicked, call `st.cache_data.clear()` and optionally trigger a background refresh via `POST /refresh`.
    *   Add a multi-select dropdown for "Select Stocks for Trend Analysis", populated by unique symbols from the dataset.
    *   Add a slider for "Top N Growth Stocks" (e.g., 5 to 50).
4.  **Top N Growth Section:**
    *   Call `calculate_top_n_growth()`.
    *   Render a Plotly Bar Chart (`px.bar`) showing `symbol` on the X-axis and `Growth (%)` on the Y-axis.
5.  **Trend Over Time Section:**
    *   If symbols are selected in the sidebar, fetch/filter their historical data.
    *   Render a Plotly Line Chart (`px.line`) showing `Date/fetched_at` on X, `Price` on Y, and colored by `symbol`.
6.  **Agent Validation Step:**
    *   *Action:* Run `streamlit run app.py --server.port 8501 --server.headless true`.
    *   *Check:* Ensure the terminal output shows no startup errors and the app is accessible. Check the terminal logs to verify `@st.cache_data` is preventing redundant API calls on UI interactions.

---

## Phase 5: End-to-End Validation Checklist
The agent must verify these final criteria before considering the task complete:
- [ ] **Network Check:** Agent has successfully made a GET request to `http://192.168.0.50:30181/health`.
- [ ] **Data Parsing Check:** The CSV from `/export/company` handles empty values without crashing (use `df.dropna()` or `df.fillna()`).
- [ ] **Performance Check:** Changing a widget (like the Top N slider) updates the UI instantly without triggering a new HTTP request to `192.168.0.50` (verified via API server logs or cache decorators).
- [ ] **Data Format Check:** Dates in the Plotly charts are properly formatted on the X-axis, not treated as discrete string categories.