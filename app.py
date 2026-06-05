import streamlit as st
import plotly.express as px
import pandas as pd
from api_client import get_bulk_csv_data, get_available_symbols, get_health, get_company_history
from data_processor import calculate_top_n_growth, prepare_trend_data, fetch_and_prepare_trend_data, detect_date_column, detect_price_column, detect_symbol_column, detect_available_factors

st.set_page_config(page_title="ASX Dashboard", layout="wide")

st.title("ASX Stock Analysis Dashboard")


@st.cache_data(ttl=3600)
def load_data():
    """Load bulk CSV data from API with caching."""
    return get_bulk_csv_data()


@st.cache_data(ttl=3600)
def load_symbols():
    """Load available symbols from health endpoint."""
    try:
        return get_available_symbols()
    except Exception:
        return []


@st.cache_data(ttl=3600)
def compute_top_n(df, n, factor):
    """Compute top N growth stocks with caching."""
    return calculate_top_n_growth(df, n, factor)


@st.cache_data(ttl=3600)
def fetch_history(symbol):
    """Fetch history for a single symbol with caching."""
    return get_company_history(symbol)


@st.cache_data(ttl=3600)
def compute_trend(symbols):
    """Fetch and prepare trend data for selected symbols with caching."""
    return fetch_and_prepare_trend_data(symbols, fetch_history)


try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

date_col = detect_date_column(df)
price_col = detect_price_column(df)
symbol_col = detect_symbol_column(df)

available_factors = detect_available_factors(df)
default_factor = price_col if price_col in available_factors else (available_factors[0] if available_factors else None)

with st.sidebar:
    st.header("Controls")

    try:
        symbols_list = load_symbols()
    except Exception as e:
        st.error(f"Cannot connect to API: {e}")
        st.stop()

    selected_symbols = st.multiselect(
        "Select Stocks for Trend Analysis",
        options=symbols_list,
        default=[],
        help="Choose stocks to compare in the trend chart"
    )

    growth_factor = st.selectbox(
        "Growth Factor",
        options=available_factors,
        index=available_factors.index(default_factor) if default_factor else 0,
        help="Select the metric to calculate growth over time"
    ) if available_factors else None

    top_n = st.slider("Top N Growth Stocks", min_value=5, max_value=50, value=10)

st.markdown(f"**Data loaded:** {len(df):,} records | **Symbols:** {df[symbol_col].nunique()} unique")
if date_col:
    snapshot_date = pd.to_datetime(df[date_col], format='mixed').max().date()
    st.markdown(f"**Snapshot date:** {snapshot_date}")


st.header(f"Top N Growth Stocks ({growth_factor or 'N/A'})")

if growth_factor:
    try:
        top_n_df = compute_top_n(df, top_n, growth_factor)

        if not top_n_df.empty:
            fig_bar = px.bar(
                top_n_df,
                x="symbol",
                y="growth_pct",
                title=f"Top {top_n} Stocks by {growth_factor} Growth (%)",
                labels={"symbol": "Stock Symbol", "growth_pct": "Growth (%)"},
                color="growth_pct",
                color_continuous_scale="RdYlGn",
            )
            fig_bar.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig_bar, width="stretch")
            st.dataframe(top_n_df, hide_index=True)
        else:
            st.warning("No growth data available")

    except Exception as e:
        st.error(f"Error computing top N growth: {e}")
else:
    st.warning("No numeric columns available for growth calculation")


st.header("Trend Over Time")

if selected_symbols:
    try:
        st.info(f"Fetching history for {len(selected_symbols)} symbols...")
        trend_df = compute_trend(selected_symbols)

        if not trend_df.empty and date_col and price_col:
            fig_line = px.line(
                trend_df,
                x=date_col,
                y=price_col,
                color=symbol_col,
                title="Price Trends Over Time",
                labels={date_col: "Date", price_col: "Price", symbol_col: "Stock"},
            )
            fig_line.update_layout(xaxis={"type": "date"})
            st.plotly_chart(fig_line, width="stretch")
            st.dataframe(trend_df[[date_col, symbol_col, price_col]], hide_index=True)
        else:
            st.warning("No trend data available for selected symbols")

    except Exception as e:
        st.error(f"Error computing trend data: {e}")
else:
    st.info("Select stocks from the sidebar to view trend analysis")
