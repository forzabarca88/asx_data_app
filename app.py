import streamlit as st
import plotly.express as px
import pandas as pd
from api_client import get_bulk_csv_data, get_available_symbols, trigger_refresh, get_health, get_company_history
from data_processor import calculate_top_n_growth, prepare_trend_data, fetch_and_prepare_trend_data, detect_date_column, detect_price_column, detect_symbol_column

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
def compute_top_n(df, n):
    """Compute top N growth stocks with caching."""
    return calculate_top_n_growth(df, n)


@st.cache_data(ttl=3600)
def fetch_history(symbol):
    """Fetch history for a single symbol with caching."""
    return get_company_history(symbol)


@st.cache_data(ttl=3600)
def compute_trend(symbols):
    """Fetch and prepare trend data for selected symbols with caching."""
    return fetch_and_prepare_trend_data(symbols, fetch_history)


with st.sidebar:
    st.header("Controls")

    if st.button("Refresh Data"):
        st.cache_data.clear()
        try:
            trigger_refresh()
            st.success("Data refresh triggered on server")
        except Exception as e:
            st.warning(f"Could not trigger server refresh: {e}")
        st.rerun()

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

    top_n = st.slider("Top N Growth Stocks", min_value=5, max_value=50, value=10)

try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

date_col = detect_date_column(df)
price_col = detect_price_column(df)
symbol_col = detect_symbol_column(df)

st.markdown(f"**Data loaded:** {len(df):,} records | **Symbols:** {df[symbol_col].nunique()} unique")
if date_col:
    snapshot_date = pd.to_datetime(df[date_col]).max().date()
    st.markdown(f"**Snapshot date:** {snapshot_date}")


st.header("Top N Growth Stocks (52-Week)")

try:
    top_n_df = compute_top_n(df, top_n)

    if not top_n_df.empty:
        fig_bar = px.bar(
            top_n_df,
            x="symbol",
            y="growth_pct",
            title=f"Top {top_n} Stocks by 52-Week Growth (%)",
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
