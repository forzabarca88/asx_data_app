import pandas as pd


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
    """Detect the price column in the dataframe."""
    price_candidates = ["priceClose", "price_close", "close", "Close", "last_price", "Last_Price", "lastPrice", "last", "price", "Price"]
    for col in price_candidates:
        if col in df.columns:
            return col
    for col in df.columns:
        if col.lower() == "priceclose" or col.lower() == "close":
            return col
    return None


def detect_symbol_column(df):
    """Detect the symbol column in the dataframe."""
    symbol_candidates = ["symbol", "Symbol", "company", "Company", "ticker", "Ticker", "company_id", "companyName"]
    for col in symbol_candidates:
        if col in df.columns:
            return col
    return None


def calculate_top_n_growth(df, n=10):
    """
    Calculate top N stocks by 52-week growth percentage from bulk snapshot.

    Uses priceClose vs priceFiftyTwoWeekLow for growth calculation.
    Returns top N sorted descending.
    """
    if df.empty:
        return pd.DataFrame(columns=["symbol", "low_52w", "current_price", "growth_pct"])

    price_col = detect_price_column(df)
    symbol_col = detect_symbol_column(df)

    low_52w_col = None
    for col in df.columns:
        if "fiftytwo" in col.lower() and "low" in col.lower():
            low_52w_col = col
            break

    if not price_col or not symbol_col or not low_52w_col:
        raise ValueError(
            f"Could not detect required columns. Found: {list(df.columns)}. "
            f"Need: price_col={price_col}, symbol_col={symbol_col}, low_52w_col={low_52w_col}"
        )

    df = df.dropna(subset=[price_col, symbol_col, low_52w_col]).copy()
    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    df[low_52w_col] = pd.to_numeric(df[low_52w_col], errors="coerce")
    df = df.dropna(subset=[price_col, low_52w_col])
    df = df[df[low_52w_col] > 0]

    df["growth_pct"] = ((df[price_col] - df[low_52w_col]) / df[low_52w_col] * 100).round(2)

    result = (
        df.sort_values("growth_pct", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )

    return result[[symbol_col, low_52w_col, price_col, "growth_pct"]].rename(
        columns={low_52w_col: "low_52w", price_col: "current_price"}
    )


def prepare_trend_data(df, symbols):
    """
    Filter dataframe for selected symbols and prepare for trend chart.

    Returns dataframe with datetime index sorted chronologically.
    """
    if not symbols or df.empty:
        return pd.DataFrame()

    symbol_col = detect_symbol_column(df)
    date_col = detect_date_column(df)
    price_col = detect_price_column(df)

    if not symbol_col or not date_col or not price_col:
        raise ValueError(
            f"Could not detect required columns. Found: {list(df.columns)}"
        )

    filtered = df[df[symbol_col].isin(symbols)].copy()
    filtered = filtered.dropna(subset=[date_col, price_col])
    filtered[date_col] = pd.to_datetime(filtered[date_col])
    filtered[price_col] = pd.to_numeric(filtered[price_col], errors="coerce")
    filtered = filtered.dropna(subset=[price_col])
    filtered = filtered.sort_values(date_col)

    return filtered


def fetch_and_prepare_trend_data(symbols, get_history_func):
    """
    Fetch individual history data for each symbol and combine for trend chart.

    Args:
        symbols: list of symbol strings
        get_history_func: function(symbol) -> DataFrame for fetching history

    Returns combined dataframe with symbol, fetched_at, priceClose columns.
    """
    if not symbols:
        return pd.DataFrame()

    all_data = []
    for sym in symbols:
        try:
            hist_df = get_history_func(sym)
            if not hist_df.empty:
                all_data.append(hist_df)
        except Exception:
            continue

    if not all_data:
        return pd.DataFrame()

    combined = pd.concat(all_data, ignore_index=True)

    date_col = detect_date_column(combined)
    price_col = detect_price_column(combined)
    symbol_col = detect_symbol_column(combined)

    if not date_col or not price_col or not symbol_col:
        return pd.DataFrame()

    combined = combined.dropna(subset=[date_col, price_col])
    combined[date_col] = pd.to_datetime(combined[date_col])
    combined[price_col] = pd.to_numeric(combined[price_col], errors="coerce")
    combined = combined.dropna(subset=[price_col])
    combined = combined.sort_values(date_col)

    return combined
