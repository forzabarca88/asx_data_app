# ASX Stock Snapshot Dashboard

> ⚠️ This was a personal project primarily implemented with generative AI. Please review code accordingly before re-use.  

Comprehensive feature engineering framework for ASX stock snapshot data, integrating valuation, growth, dividend/franking, and liquidity metrics into a Streamlit dashboard.

## Features

- **Growth Rankings**: YoY revenue growth, net margin trends, earnings quality, 3-year CAGR
- **Valuation Matrix**: Cleaned P/E, earnings yield, price-to-cash, FCF yield
- **Dividend Analysis**: ASX-specific franking credits, tax-adjusted yields, currency risk flags
- **Liquidity & Risk**: Bid-ask spread, volume turnover, intraday volatility, 52-week range position
- **Trend Over Time**: Historical price tracking with selectable symbols

## Setup

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```powershell
streamlit run .\app.py
```

## Testing

```powershell
pytest tests/ -v
```

## Architecture

- `api_client.py` — ASX API data fetching with retry logic
- `data_processor.py` — Feature engineering pipeline (sentinel cleaning, date conversion, income statement parsing)
- `app.py` — Streamlit dashboard with 5 tabs and sidebar filters
- `tests/` — 16 tests covering all processor functions and API health
