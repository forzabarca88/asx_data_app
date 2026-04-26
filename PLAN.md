# PLAN.md: ASX Stock Visualisation Web App

## 🎯 Project Overview
The goal of this project is to build a modern, interactive web application entirely in Python. The app will consume an *already existing* local API serving ASX stock data and visualise historical stock parameters (e.g., `priceClose`, `volumeAverage`) over time.

**API Base URL:** `http://192.168.0.50:30181`

### Recommended Tech Stack
*   **Package Manager:** [uv](https://docs.astral.sh/uv/) (Blazing fast Python package and project manager)
*   **Web Framework:** [Streamlit](https://docs.streamlit.io/) (Ideal for rapid, modern data web apps in Python)
*   **Data Manipulation:** [Pandas](https://pandas.pydata.org/docs/)
*   **HTTP Client:** [Requests](https://requests.readthedocs.io/en/latest/)
*   **Visualisation:** [Plotly Express](https://plotly.com/python/plotly-express/)

---

## 🤖 AI Agent Instructions
*   **Execution:** Treat this plan as a state machine. Execute one step at a time.
*   **Persistence:** You may be stopped and started between steps. Ensure code is saved to disk continuously.
*   **Research:** Use the provided documentation links to research the syntax for any packages you are unfamiliar with before writing the code.
*   **Environment Management:** Use `uv` exclusively for managing dependencies and running scripts.
*   **Validation:** DO NOT proceed to the next step until the "Validation Check" for the current step has been successfully completed and confirmed.

---

## 📋 Execution Steps

### Step 1: Project Setup & Research
**Goal:** Initialize the project environment using `uv` and gather necessary dependencies.
**Tasks:**
1. Initialize the project using `uv init` (this will create a `pyproject.toml`).
2. Add the required dependencies by running: `uv add streamlit pandas requests plotly`.
3. Create the main application file, e.g., `app.py`.
4. Review the documentation for Streamlit's caching mechanism (`@st.cache_data`) to understand how to prevent redundant API calls: [Streamlit Caching Docs](https://docs.streamlit.io/library/advanced-features/caching).

**Research Links:**
- [uv Documentation](https://docs.astral.sh/uv/getting-started/features/)

**Validation Check:** 
- The `uv add` command executes without errors, automatically creating the virtual environment and lockfile.
- Running `uv run streamlit run app.py` opens a blank web page successfully.

---

### Step 2: API Client & Data Fetching Module
**Goal:** Create a robust module to communicate with the internal API.
**Tasks:**
1. Create a file `api_client.py`.
2. Implement a function `get_available_companies()` that:
   - GETs `http://192.168.0.50:30181/health`
   - Parses the JSON response and extracts the keys from `data.refreshes` to return a list of company symbols (e.g., `["10X", "14D", ...]`).
3. Implement a function `get_company_history(symbol: str)` that:
   - GETs `http://192.168.0.50:30181/company/{symbol}/history`
   - Returns the `data` array containing historical records.
4. Add basic error handling (e.g., try/except blocks using `requests.exceptions.RequestException`).

**Research Links:**
- [Requests API Docs](https://requests.readthedocs.io/en/latest/api/)

**Validation Check:** 
- Write a short `test_api.py` script that prints the list of companies and the first historical record for `"14D"`. Run it via `uv run test_api.py` and confirm valid JSON data is returned.

---

### Step 3: Data Transformation Pipeline
**Goal:** Convert the raw JSON API responses into clean Pandas DataFrames suitable for visualisation.
**Tasks:**
1. In `app.py` (or a dedicated `data_processor.py`), write a function that takes the raw history data and converts it into a `pandas.DataFrame`.
2. Ensure the `fetched_at` column is converted to a datetime object using `pd.to_datetime()`.
3. Sort the DataFrame chronologically by `fetched_at`.
4. Identify numerical columns that can be graphed (e.g., `priceAsk`, `priceBid`, `priceClose`, `priceDayHigh`, `priceDayLow`, `volumeAverage`).

**Research Links:**
- [Pandas to_datetime Docs](https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html)

**Validation Check:** 
- Fetch data for `"14D"`, pass it through the DataFrame function, and print `df.dtypes` and `df.head()`. Ensure `fetched_at` is a datetime type and numerical fields are floats/ints.

---

### Step 4: Web UI Shell & Controls
**Goal:** Build the basic layout of the application.
**Tasks:**
1. In `app.py`, set the page config using `st.set_page_config()`.
2. Create a sidebar (`st.sidebar`).
3. Use the API client to fetch the list of companies. Display them in the sidebar using `st.selectbox("Select Company", companies)`.
4. Create a second `st.selectbox` in the sidebar for "Select Parameter to Visualise" (hardcode a list like `["priceClose", "priceAsk", "priceBid", "volumeAverage", "cashFlow"]`).
5. *Crucial:* Wrap the data fetching calls in `@st.cache_data` with a short TTL (e.g., 5 minutes) so the API isn't overloaded every time a user changes a dropdown.

**Research Links:**
- [Streamlit Selectbox](https://docs.streamlit.io/library/api-reference/widgets/st.selectbox)

**Validation Check:** 
- Run the Streamlit app using `uv run streamlit run app.py`. Verify that the sidebar appears, the company dropdown is populated with live API data, and changing the dropdown updates the main page state without crashing.

---

### Step 5: Implement Visualisation
**Goal:** Plot the selected parameter over time.
**Tasks:**
1. Based on the selected company and selected parameter from Step 4, filter the DataFrame.
2. Use Plotly Express (`px.line()`) to generate a line graph. 
   - X-axis: `fetched_at`
   - Y-axis: The dynamically selected parameter (e.g., `priceClose`).
3. Render the chart in Streamlit using `st.plotly_chart(fig, use_container_width=True)`.
4. (Optional but recommended): Display the `incomeStatement` array from the most recent historical record as a table below the chart using `st.dataframe()`.

**Research Links:**
- [Plotly Express Line Charts](https://plotly.com/python/line-charts/)
- [Streamlit Plotly Integration](https://docs.streamlit.io/library/api-reference/charts/st.plotly_chart)

**Validation Check:** 
- Open the web app. Select "14D" and "priceClose". Verify a line graph accurately plots the price over time. Switch to "volumeAverage" and verify the chart updates correctly.

---

### Step 6: Polish & Edge Cases
**Goal:** Make the app robust and user-friendly.
**Tasks:**
1. **Empty States:** Add logic to display a friendly warning (`st.warning()`) if a company has no historical data.
2. **Missing Data:** Ensure Plotly handles nulls gracefully (e.g., using `.dropna(subset=[selected_parameter])`).
3. **API Unavailability:** Update the data fetching wrapper to show an `st.error()` in the UI if the API at `192.168.0.50:30181` cannot be reached, rather than throwing a raw Python exception.
4. **Metrics:** Use `st.metric()` at the top of the page to show the *latest* price and how it changed from the *previous* recorded price.

**Validation Check:** 
- Disconnect from the API (or temporarily break the URL in code) and ensure the UI displays a clean error message. Reconnect and verify the summary metrics and chart load perfectly.