# ASX Stock Analysis Dashboard

> ⚠️ This was a personal project primarily implemented with generative AI. Please review code accordingly before re-use.

Streamlit dashboard for analysing ASX stock snapshots — valuation, growth, dividend/franking, and liquidity metrics.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)

## Setup

```bash
# Install dependencies
uv sync

# (Optional) Install Playwright for E2E tests
playwright install chromium
```

## Configuration

The API server URL defaults to `http://localhost:30181` in `config.py`. Override at runtime:

```bash
export ASX_API_BASE_URL=http://192.168.0.50:30181
uv run streamlit run app.py
```

Or edit the default in `config.py`:

```python
API_BASE_URL_DEFAULT = "http://192.168.0.50:30181"
```

## Running

```bash
uv run streamlit run app.py
```

## Features

| Tab | Description |
|------|-------------|
| **Growth rankings** | Top N stocks ranked by growth across selected metrics |
| **Valuation matrix** | P/E ratio, FCF yield, earnings yield, price-to-cash |
| **Dividend analysis** | Grossed-up yield, franking credits, payout ratio, currency risk |
| **Liquidity & risk** | Bid-ask spread, volume turnover, 52-week range position, intraday volatility |
| **Trend over time** | Historical price/volume trends for selected symbols |

## Project structure

```
├── app.py              — Layout orchestrator, tabs, data loading
├── api_client.py       — HTTP client for the ASX data API
├── charts.py           — Chart builders (Altair, Streamlit native)
├── config.py           — Central configuration (labels, icons, defaults, theme)
├── data_processor.py   — Data processing pipeline (feature engineering, growth)
├── sidebar.py          — Sidebar widgets and session state
├── requirements.txt    — Production dependencies
├── .streamlit/
│   └── config.toml     — Theme and server configuration
├── tests/
│   ├── test_api.py
│   ├── test_processor.py
│   └── e2e/            — Playwright end-to-end tests
├── k8s/                — Kubernetes deployment manifests
└── AGENTS.md           — Dev agent instructions (not for users)
```

## Testing

```bash
# Unit tests
uv run pytest tests/ -v

# E2E tests (requires Playwright)
uv run pytest tests/e2e/ -v
```

## Deployment

See `k8s/` for Kubernetes manifests including `Dockerfile`, `deployment.yaml`, `service.yaml`, and `ingress.yaml`.