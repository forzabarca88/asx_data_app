import ast
import logging
import numpy as np
import pandas as pd

from config import AU_TAX_RATE, FCF_YIELD_SENTINEL, PE_SENTINEL

log = logging.getLogger("asx")


def detect_date_column(df):
    """Detect the date column in the dataframe."""
    date_candidates = ["fetched_at", "date", "Date", "timestamp", "Timestamp"]
    for col in date_candidates:
        if col in df.columns:
            return col
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            return col
    return None


def detect_price_column(df):
    """Detect the price close column in the dataframe."""
    price_candidates = ["priceClose", "price_close", "close", "Close", "last_price", "Last_Price", "lastPrice", "last", "price", "Price"]
    for col in price_candidates:
        if col in df.columns:
            return col
    for col in df.columns:
        if col.lower() == "priceclose" or col.lower() == "close":
            return col
    return None


def detect_available_factors(df):
    """Detect all numeric columns available for growth factor selection."""
    return [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]


def detect_symbol_column(df):
    """Detect the symbol column in the dataframe."""
    candidates = ["symbol", "Symbol", "company", "Company", "ticker", "Ticker", "company_id", "companyName"]
    for col in candidates:
        if col in df.columns:
            return col
    return None


def calculate_top_n_growth(df, n=10, factor=None):
    """
    Calculate top N stocks by growth percentage from bulk snapshot.

    Growth is computed from the earliest to latest value of the selected metric
    across all available data points for each stock.

    Args:
        df: bulk snapshot DataFrame
        n: number of top stocks to return
        factor: column name to use for growth calculation (e.g., "priceClose", "priceHigh")

    Returns top N sorted descending.
    """
    if df.empty:
        return pd.DataFrame(columns=["symbol", "start_value", "end_value", "growth_pct"])

    symbol_col = detect_symbol_column(df)
    date_col = detect_date_column(df)
    factor_col = factor if factor else detect_price_column(df)

    if not symbol_col:
        raise ValueError(f"Could not detect symbol column. Found: {list(df.columns)}")
    if not factor_col:
        raise ValueError(f"No factor column found. Available columns: {list(df.columns)}")

    df = df.dropna(subset=[factor_col, symbol_col]).copy()
    df[factor_col] = pd.to_numeric(df[factor_col], errors="coerce")
    df = df.dropna(subset=[factor_col])

    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], format='mixed', errors="coerce")
        df = df.dropna(subset=[date_col])
        # Sort is load-bearing: groupby.first/last depend on row order
        df = df.sort_values([symbol_col, date_col])
    else:
        df = df.reset_index(drop=True)

    # groupby.first/last are order-dependent; the sort above ensures
    # "first" = earliest date, "last" = latest date per symbol
    grouped = df.groupby(symbol_col)[factor_col].agg(["first", "last"]).reset_index()
    grouped = grouped[grouped["first"] != 0]
    grouped["growth_pct"] = (
        ((grouped["last"] - grouped["first"]) / grouped["first"] * 100).round(2)
    )

    result = (
        grouped.sort_values("growth_pct", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )

    return result.rename(columns={"first": "start_value", "last": "end_value"})


def fetch_and_prepare_trend_data(symbols, get_history_func, start_date=None, end_date=None):
    """
    Fetch individual history data for each symbol and combine for trend chart.

    Args:
        symbols: list of symbol strings
        get_history_func: function(symbol, start_date, end_date) -> DataFrame for fetching history
        start_date: ISO date string (YYYY-MM-DD) for filtering, or None for full history
        end_date: ISO date string (YYYY-MM-DD) for filtering, or None for full history

    Returns:
        Tuple of (combined DataFrame, list of failed symbol names).
        Logs warnings for symbols that fail to fetch.
    """
    failed_symbols = []

    if not symbols:
        return pd.DataFrame(), failed_symbols

    all_data = []
    for sym in symbols:
        try:
            hist_df = get_history_func(sym, start_date=start_date, end_date=end_date)
            if not hist_df.empty:
                all_data.append(hist_df)
        except Exception as e:
            log.warning("Failed to fetch history for %s: %s", sym, e)
            failed_symbols.append(sym)
            continue

    if not all_data:
        return pd.DataFrame(), failed_symbols

    combined = pd.concat(all_data, ignore_index=True)

    date_col = detect_date_column(combined)
    price_col = detect_price_column(combined)
    symbol_col = detect_symbol_column(combined)

    if not date_col or not price_col or not symbol_col:
        return pd.DataFrame(), failed_symbols

    combined = combined.dropna(subset=[date_col, price_col])
    combined[date_col] = pd.to_datetime(combined[date_col], format='mixed')
    combined[price_col] = pd.to_numeric(combined[price_col], errors="coerce")
    combined = combined.dropna(subset=[price_col])
    combined = combined.sort_values(date_col)

    return combined, failed_symbols


# ── Data Cleaning & Sentinel Handling ──────────────────────────────

def clean_sentinel(value, sentinel=PE_SENTINEL):
    """Clean sentinel values, returning NaN for known placeholders."""
    if pd.isna(value):
        return np.nan
    try:
        v = float(value)
        return np.nan if v <= sentinel else v
    except (ValueError, TypeError):
        return np.nan


def clean_yield_sentinel(value):
    """Clean FCF yield sentinel values near zero."""
    if pd.isna(value):
        return np.nan
    try:
        v = float(value)
        return np.nan if abs(v - FCF_YIELD_SENTINEL) < 1e-9 else v
    except (ValueError, TypeError):
        return np.nan


def convert_excel_date(serial_date):
    """Convert Excel serial date to pandas Timestamp.

    Uses the Excel 1900 date system base of 1899-12-30,
    which correctly accounts for Excel's phantom leap year bug.
    Fractional days are preserved (e.g., 45838.5 -> 2025-06-30 12:00:00).
    """
    if pd.isna(serial_date):
        return pd.NaT
    try:
        serial = float(serial_date)
    except (ValueError, TypeError):
        return pd.NaT
    base = pd.Timestamp(1899, 12, 30)
    return base + pd.Timedelta(days=serial)


def parse_income_statement(statement_str):
    """Parse income statement string (handles single-quoted Python dicts).

    Uses ast.literal_eval instead of naive string replacement, which is
    safe for arbitrary Python literal expressions and avoids breaking on
    apostrophes in field values (e.g., company names like "O'Brien").
    """
    if pd.isna(statement_str) or not statement_str:
        return []
    try:
        statements = ast.literal_eval(str(statement_str))
        return sorted(statements, key=lambda x: str(x.get("period", "")))
    except (ValueError, SyntaxError, TypeError):
        return []


# ── Feature Computation Helpers ─────────────────────────────────────

def _safe_numeric(value, default=np.nan):
    """Safely convert a value to numeric, returning default on failure."""
    try:
        v = float(value)
        return v if not np.isnan(v) else default
    except (ValueError, TypeError):
        return default


def _safe_div(numerator, denominator, default=np.nan):
    """Safe division returning default when denominator is zero or NaN."""
    num = _safe_numeric(numerator)
    den = _safe_numeric(denominator)
    if pd.isna(num) or pd.isna(den) or den == 0:
        return default
    return num / den


# ── Main Feature Engineering Pipeline ───────────────────────────────

def engineer_features(df):
    """
    Compute all engineered features from bulk snapshot data.

    Returns a DataFrame with one row per symbol (latest snapshot) containing:
    - Valuation metrics: market_cap, cleaned_pe, earnings_yield, price_to_cash, free_cash_flow_yield
    - Growth metrics: yoy_revenue_growth, revenue_cagr_3y, latest_net_margin,
                     net_income_direction, earnings_quality_ratio
    - Dividend metrics: raw_dividend_yield, franking_credit_multiplier,
                       grossed_up_yield, dividend_payout_ratio, dividend_currency_risk
    - Liquidity metrics: bid_ask_spread_pct, range_position_52w,
                        volume_turnover_ratio, intraday_volatility
    - Date: period_end_date (converted from Excel serial)
    """
    if df.empty:
        return pd.DataFrame()

    symbol_col = detect_symbol_column(df)
    if not symbol_col:
        raise ValueError(f"Could not detect symbol column. Found: {list(df.columns)}")

    # Keep latest snapshot per symbol
    date_col = detect_date_column(df)
    if date_col and date_col in df.columns:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], format="mixed", errors="coerce")
        df = df.dropna(subset=[date_col])
        idx = df.groupby(symbol_col)[date_col].idxmax()
        df = df.loc[idx].copy()

    features_rows = []

    for _, row in df.iterrows():
        features = {"symbol": row.get(symbol_col, "")}

        # ── 1. Valuation & Size Metrics ──────────────────────────
        shares = _safe_numeric(row.get("numOfShares"))
        price = _safe_numeric(row.get("priceClose"))
        features["market_cap"] = shares * price if not (pd.isna(shares) or pd.isna(price)) else np.nan

        pe = _safe_numeric(row.get("priceEarningsRatio"))
        features["cleaned_pe"] = clean_sentinel(pe)
        features["earnings_yield"] = (
            1 / features["cleaned_pe"] if not np.isnan(features["cleaned_pe"]) else np.nan
        )

        pcf = _safe_numeric(row.get("priceToCash"))
        features["price_to_cash"] = clean_sentinel(pcf)

        fcf_yield = _safe_numeric(row.get("freeCashFlowYield"))
        features["free_cash_flow_yield"] = clean_yield_sentinel(fcf_yield)

        # ── 2. Growth & Financial Health (from incomeStatement) ──
        statements = parse_income_statement(row.get("incomeStatement"))

        if len(statements) >= 2:
            latest = statements[-1]
            prev = statements[-2]

            rev_latest = latest.get("revenue", 0) or 0
            rev_prev = prev.get("revenue", 0) or 0
            ni_latest = latest.get("netIncome", 0) or 0
            cf_latest = latest.get("cashFlow", 0) or 0

            features["yoy_revenue_growth"] = _safe_div(rev_latest - rev_prev, rev_prev)
            features["latest_net_margin"] = _safe_div(ni_latest, rev_latest)
            features["earnings_quality_ratio"] = _safe_div(cf_latest, ni_latest)

            ni_prev = prev.get("netIncome", 0) or 0
            features["net_income_direction"] = np.sign(ni_latest - ni_prev)
        else:
            features["yoy_revenue_growth"] = np.nan
            features["latest_net_margin"] = np.nan
            features["earnings_quality_ratio"] = np.nan
            features["net_income_direction"] = np.nan

        # 3-Year Revenue CAGR
        if len(statements) >= 4:
            rev_latest = statements[-1].get("revenue", 0) or 0
            rev_3yr_ago = statements[-4].get("revenue", 0) or 0
            if rev_3yr_ago > 0 and rev_latest > 0:
                features["revenue_cagr_3y"] = (rev_latest / rev_3yr_ago) ** (1 / 3) - 1
            else:
                features["revenue_cagr_3y"] = np.nan
        else:
            features["revenue_cagr_3y"] = np.nan

        # ── 3. Dividend & Franking Analytics ─────────────────────
        raw_yield = _safe_numeric(row.get("yieldAnnual"))
        franking = _safe_numeric(row.get("frankingPercent"), 0.0)
        features["raw_dividend_yield"] = raw_yield

        franking_pct = franking if not pd.isna(franking) else 0.0
        franking_factor = 1.0 + (franking_pct / 100) * (AU_TAX_RATE / (1 - AU_TAX_RATE))
        features["franking_credit_multiplier"] = franking_factor

        features["grossed_up_yield"] = (
            raw_yield * franking_factor if not pd.isna(raw_yield) else np.nan
        )

        eps = _safe_numeric(row.get("earningsPerShare"))
        dividend = _safe_numeric(row.get("dividend"))
        features["dividend_payout_ratio"] = _safe_div(dividend, eps)

        div_currency = str(row.get("dividendCurrency", "AUD")).upper()
        features["dividend_currency_risk"] = div_currency != "AUD"

        # ── 4. Liquidity & Technical Metrics ─────────────────────
        ask = _safe_numeric(row.get("priceAsk"))
        bid = _safe_numeric(row.get("priceBid"))
        features["bid_ask_spread_pct"] = _safe_div(ask - bid, price)

        high52 = _safe_numeric(row.get("priceFiftyTwoWeekHigh"))
        low52 = _safe_numeric(row.get("priceFiftyTwoWeekLow"))
        denom = high52 - low52 if not (pd.isna(high52) or pd.isna(low52)) else np.nan
        features["range_position_52w"] = (
            _safe_div(price - low52, denom) if not pd.isna(denom) else np.nan
        )

        vol_avg = _safe_numeric(row.get("volumeAverage"))
        features["volume_turnover_ratio"] = _safe_div(vol_avg, shares)

        day_high = _safe_numeric(row.get("priceDayHigh"))
        day_low = _safe_numeric(row.get("priceDayLow"))
        features["intraday_volatility"] = _safe_div(day_high - day_low, price)

        # ── 5. Date Conversion ───────────────────────────────────
        features["period_end_date"] = convert_excel_date(row.get("fPeriodEndDate"))

        features_rows.append(features)

    return pd.DataFrame(features_rows)
