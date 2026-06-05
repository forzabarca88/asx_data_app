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
    factor_candidates = [
        "priceClose", "price_close", "close", "Close",
        "priceHigh", "price_high", "high", "High",
        "priceLow", "price_low", "low", "Low",
        "priceOpen", "price_open", "open", "Open",
        "volume", "Volume", "trade_volume", "tradeVolume",
        "last_price", "Last_Price", "lastPrice", "last",
        "price", "Price",
    ]
    available = []
    for col in factor_candidates:
        if col in df.columns:
            available.append(col)
    for col in df.columns:
        if col not in available and pd.api.types.is_numeric_dtype(df[col]):
            available.append(col)
    return available


def detect_symbol_column(df):
    """Detect the symbol column in the dataframe."""
    symbol_candidates = ["symbol", "Symbol", "company", "Company", "ticker", "Ticker", "company_id", "companyName"]
    for col in symbol_candidates:
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
        df = df.sort_values([symbol_col, date_col])
    else:
        df = df.reset_index(drop=True)

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
    filtered[date_col] = pd.to_datetime(filtered[date_col], format='mixed')
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
    combined[date_col] = pd.to_datetime(combined[date_col], format='mixed')
    combined[price_col] = pd.to_numeric(combined[price_col], errors="coerce")
    combined = combined.dropna(subset=[price_col])
    combined = combined.sort_values(date_col)

    return combined
