# AGENTS.md

## Core Principles

- **DESIGN AND BUILD PRODUCTION GRADE CODE FROM THE START** - i.e. no monolithic files when they can modularised, no unnecessary duplication of code, no hardcoded values when they can be placed in a centralised config file, etc.
- Keep AGENTS.md minimal - **only** keep information which will be required every time you look at this project. Project structure should **always** be kept up to date, and include a CONCISE single sentence description of each file in the project.  Do not modify `Core Principles`, but review and remove anything else from the document which is not required.
- Do **not** make assumptions without testing and validating first. Follow the scientific method.
- You **must** review your own code as you write as a *Senior Software Engineer*.
- Write the bare minimum of tests - follow **ARRANGE, ACT, ASSERT**. You must test the end result, NOT the implmentation details.
- If you start the application (e.g. for testing), you must validate that the application is stopped before marking the task complete.
- Use mocks for testing sparingly - if the code requires excessive mocking, then redesign the implementation to be easier to test.
- **You must assume that your knowledge is outdated** - always research topics and frameworks before making decisions.

## Important Notes

### Project Structure

- `app.py` — Thin layout orchestrator (imports from modules, tab structure, data loading, caching)
- `api_client.py` — HTTP client for the ASX data API (bulk export, company history, health)
- `charts.py` — Chart builders (3 native bar charts return DataFrames for `st.bar_chart`; 2 Altair scatter charts; 1 Altair histogram; 1 Altair line chart uses long-format data directly for `st.altair_chart`)
- `config.py` — Central configuration module (labels, icons, defaults, chart params, tooltips/help text, captions, messages; theme colors read from `.streamlit/config.toml` via `tomllib`; sentence case exception constants)
- `sidebar.py` — Sidebar widget rendering and session state initialization (`init_session_state_defaults` sets defaults; `render_sidebar` renders widgets)
- `data_processor.py` — Data processing pipeline (column detection, feature engineering, growth calculation)
- `requirements.txt` — Production Python dependencies
- `requirements-dev.txt` — Development Python dependencies (references `requirements.txt` via `-r`, plus testing/linting tools)
- `.streamlit/config.toml` — Streamlit theme and server configuration
- `tests/__init__.py` — Makes tests a proper Python package
- `tests/test_api.py` — Unit tests for API client (mocks via `unittest.mock`)
- `tests/test_processor.py` — Unit tests for data processing pipeline
- `tests/test_config.py` — Unit tests validating centralised tooltip/help dict keys match displayed columns
- `tests/e2e/__init__.py` — Makes e2e tests a proper Python package
- `tests/e2e/conftest.py` — Playwright fixtures (browser, page, app launcher, mock API server, screenshots)
- `tests/e2e/mock_api_server.py` — Mock HTTP server for the ASX API (deterministic responses for reliable E2E tests)
- `tests/e2e/test_app_structure.py` — E2E tests for UI element presence (page title, sidebar, tabs, widgets)
- `tests/e2e/test_charts.py` — E2E tests for chart rendering and visual quality (Vega-Lite charts, axis labels, sentence case, no overlaid text)
- `tests/e2e/test_dataframes.py` — E2E tests for data table rendering (column headers from column_config, data correctness, no Pandas Styler artifacts)
- `tests/e2e/test_interactions.py` — E2E tests for widget interaction (date range, growth factor, slider, franked toggle, multiselect, tab switching)
- `tests/e2e/README.md` — E2E test documentation and run instructions
- `k8s/` — Kubernetes deployment manifests
