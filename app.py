import datetime
import logging
import streamlit as st
import plotly.express as px
import pandas as pd
from api_client import get_bulk_csv_data, get_available_symbols, get_health, get_company_history
from data_processor import (
    calculate_top_n_growth,
    prepare_trend_data,
    fetch_and_prepare_trend_data,
    detect_date_column,
    detect_price_column,
    detect_symbol_column,
    detect_available_factors,
    engineer_features,
)

# Configure logging for diagnostics
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

st.set_page_config(page_title="ASX Dashboard", layout="wide")

st.title("ASX Stock Analysis Dashboard")


@st.cache_data(ttl=3600, max_entries=20)
def load_data(start_date=None, end_date=None):
    """Load bulk CSV data from API with caching."""
    return get_bulk_csv_data(start_date=start_date, end_date=end_date)


@st.cache_data(ttl=3600, max_entries=10)
def load_symbols():
    """Load available symbols from health endpoint."""
    try:
        return get_available_symbols()
    except Exception:
        return []


@st.cache_data(ttl=3600, max_entries=64)
def compute_top_n(df, n, factor):
    """Compute top N growth stocks with caching on full data.

    Cache at the source granularity (full df), then apply cheap
    interactive filters outside the cached function.
    """
    return calculate_top_n_growth(df, n, factor)


@st.cache_data(ttl=3600, max_entries=256)
def fetch_history(symbol, start_date=None, end_date=None):
    """Fetch history for a single symbol with caching."""
    return get_company_history(symbol, start_date=start_date, end_date=end_date)


@st.cache_data(ttl=3600, max_entries=128)
def compute_trend(symbols, start_date=None, end_date=None):
    """Fetch and prepare trend data for selected symbols with caching.

    Returns tuple of (DataFrame, list_of_failed_symbols).
    """
    return fetch_and_prepare_trend_data(symbols, fetch_history, start_date=start_date, end_date=end_date)


@st.cache_data(ttl=3600, max_entries=8)
def compute_engineered(df):
    """Compute all engineered features with caching."""
    return engineer_features(df)


# ── Date range initialization ─────────────────────────────────────
# Initialize defaults before any code reads from session_state.
# The st.date_input widget (rendered later in the sidebar) picks up
# these defaults on first run and persists them thereafter.
_today = datetime.date.today()
st.session_state.setdefault(
    "date_range",
    [_today - datetime.timedelta(days=90), _today],
)

# Read dates from session state and convert to ISO format for API
start_date = st.session_state["date_range"][0]
end_date = st.session_state["date_range"][1]
start_date_str = start_date.isoformat()
end_date_str = end_date.isoformat()

try:
    df = load_data(start_date=start_date_str, end_date=end_date_str)
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

if df.empty:
    st.warning("No data available for the selected date range. Try a wider date range.")
    st.stop()

date_col = detect_date_column(df)
price_col = detect_price_column(df)
symbol_col = detect_symbol_column(df)

available_factors = detect_available_factors(df)
default_factor = price_col if price_col in available_factors else (available_factors[0] if available_factors else None)

try:
    symbols_list = load_symbols()
except Exception as e:
    st.error(f"Cannot connect to API: {e}")
    symbols_list = []

try:
    eng_df = compute_engineered(df)
except Exception as e:
    eng_df = pd.DataFrame()
    st.warning(f"Feature engineering unavailable: {e}")

st.markdown(f"**Data loaded:** {len(df):,} records | **Symbols:** {df[symbol_col].nunique() if symbol_col else 0} unique")
if date_col:
    snapshot_date = pd.to_datetime(df[date_col], format="mixed").max().date()
    st.markdown(f"**Snapshot date:** {snapshot_date}")

# ── Sidebar Controls ────────────────────────────────────────────────
with st.sidebar:
    st.header("Controls")

    # Date range filter (defaults to last 90 days, set via setdefault above)
    today = datetime.date.today()

    st.date_input(
        "Date range",
        min_value=datetime.date(2020, 1, 1),
        max_value=today,
        key="date_range",
    )

    selected_symbols = st.multiselect(
        "Select Stocks for Trend Analysis",
        options=symbols_list,
        default=[],
        help="Choose stocks to compare in the trend chart",
    )

    growth_factor = st.selectbox(
        "Growth Factor",
        options=available_factors,
        index=available_factors.index(default_factor) if default_factor else 0,
        help="Select the metric to calculate growth over time",
    ) if available_factors else None

    top_n = st.slider("Top N Growth Stocks", min_value=5, max_value=50, value=10)

    if not eng_df.empty:
        st.divider()
        st.header("Feature Filters")
        min_market_cap = st.number_input(
            "Min Market Cap ($M)",
            min_value=0.0,
            value=0.0,
            step=100.0,
            key="min_market_cap",
        )
        min_yield = st.number_input(
            "Min Grossed-Up Yield (%)",
            min_value=0.0,
            value=0.0,
            step=0.5,
            key="min_yield",
        )
        show_only_franked = st.checkbox(
            "Franked Dividends Only",
            value=False,
            key="show_only_franked",
        )

        # Always apply filters from session_state values (persists across reruns)
        filtered_eng = eng_df.copy()
        if st.session_state.get("min_market_cap", 0) > 0:
            filtered_eng = filtered_eng[filtered_eng["market_cap"] >= st.session_state["min_market_cap"] * 1e6]
        if st.session_state.get("min_yield", 0) > 0:
            filtered_eng = filtered_eng[filtered_eng["grossed_up_yield"] >= st.session_state["min_yield"] / 100]
        if st.session_state.get("show_only_franked", False):
            filtered_eng = filtered_eng[filtered_eng["franking_credit_multiplier"] > 1.0]
    else:
        filtered_eng = pd.DataFrame()

# ── Tabs (dynamic: on_change="rerun" + .open guards) ────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Growth Rankings",
    "Valuation Matrix",
    "Dividend Analysis",
    "Liquidity & Risk",
    "Trend Over Time",
], on_change="rerun")

# ── Tab 1: Growth Rankings ──────────────────────────────────────────
if tab1.open:
    with tab1:
        st.header(f"Top N Growth Stocks ({growth_factor or 'N/A'})")

        if growth_factor:
            try:
                # Cache at source granularity (full df), filter outside
                top_n_df = compute_top_n(df, top_n, growth_factor)
                if not filtered_eng.empty:
                    allowed_symbols = set(filtered_eng["symbol"])
                    top_n_df = top_n_df[top_n_df["symbol"].isin(allowed_symbols)]

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

# ── Tab 2: Valuation Matrix ─────────────────────────────────────────
if tab2.open:
    with tab2:
        st.header("Valuation Matrix")

        if not eng_df.empty and not filtered_eng.empty:
            val_cols = ["symbol", "market_cap", "cleaned_pe", "earnings_yield", "price_to_cash", "free_cash_flow_yield"]
            display_df = filtered_eng[val_cols].copy()

            display_df["market_cap"] = display_df["market_cap"] / 1e6
            display_df.rename(columns={"market_cap": "Market Cap ($M)"}, inplace=True)

            st.markdown("Company size and valuation multiples relative to share price.")
            st.dataframe(
                display_df.style.format({
                    "Market Cap ($M)": "{:,.2f}",
                    "cleaned_pe": "{:.2f}",
                    "earnings_yield": "{:.4f}",
                    "price_to_cash": "{:.2f}",
                    "free_cash_flow_yield": "{:.4f}",
                }),
                hide_index=True,
                width="stretch",
            )

            # Size category distribution
            eng_df_copy = filtered_eng.copy()
            eng_df_copy["market_cap_m"] = eng_df_copy["market_cap"] / 1e6
            bins = [0, 50, 200, 2000, float("inf")]
            labels = ["Micro", "Small", "Mid", "Large"]
            eng_df_copy["size_category"] = pd.cut(eng_df_copy["market_cap_m"], bins=bins, labels=labels)

            size_counts = eng_df_copy["size_category"].value_counts().reset_index()
            size_counts.columns = ["Size", "Count"]

            fig_size = px.bar(
                size_counts,
                x="Size",
                y="Count",
                title="Market Cap Distribution",
                color="Size",
                color_discrete_map={"Micro": "grey", "Small": "blue", "Mid": "green", "Large": "red"},
            )
            st.plotly_chart(fig_size)

            # P/E scatter
            pe_data = filtered_eng.dropna(subset=[
                "cleaned_pe", "free_cash_flow_yield",
                "market_cap", "earnings_yield",
            ])
            pe_data = pe_data[pe_data["market_cap"] > 0]
            if not pe_data.empty:
                fig_pe = px.scatter(
                    pe_data,
                    x="cleaned_pe",
                    y="free_cash_flow_yield",
                    text="symbol",
                    title="P/E Ratio vs Free Cash Flow Yield",
                    labels={"cleaned_pe": "P/E Ratio", "free_cash_flow_yield": "FCF Yield"},
                    size="market_cap",
                    color="earnings_yield",
                )
                st.plotly_chart(fig_pe)
        elif eng_df.empty:
            st.info("Feature engineering data not available.")
        else:
            st.info("No stocks match the current filters.")

# ── Tab 3: Dividend Analysis ────────────────────────────────────────
if tab3.open:
    with tab3:
        st.header("Dividend & Franking Analysis")

        if not eng_df.empty and not filtered_eng.empty:
            div_cols = [
                "symbol", "raw_dividend_yield", "franking_credit_multiplier",
                "grossed_up_yield", "dividend_payout_ratio", "dividend_currency_risk",
            ]
            div_df = filtered_eng[div_cols].copy()

            div_df["raw_yield_pct"] = div_df["raw_dividend_yield"] * 100
            div_df["grossed_up_pct"] = div_df["grossed_up_yield"] * 100
            div_df["payout_pct"] = div_df["dividend_payout_ratio"] * 100
            div_df["currency_risk"] = div_df["dividend_currency_risk"].map({True: "⚠ FX Risk", False: "AUD"})

            display_div = div_df[["symbol", "raw_yield_pct", "franking_credit_multiplier", "grossed_up_pct", "payout_pct", "currency_risk"]]
            display_div.rename(columns={
                "raw_yield_pct": "Raw Yield (%)",
                "franking_credit_multiplier": "Franking Multiplier",
                "grossed_up_pct": "Grossed-Up Yield (%)",
                "payout_pct": "Payout Ratio (%)",
            }, inplace=True)

            st.markdown("Tax-adjusted dividend yields with franking credit benefits.")
            st.dataframe(
                display_div.style.format({
                    "Raw Yield (%)": "{:.2f}",
                    "Franking Multiplier": "{:.4f}",
                    "Grossed-Up Yield (%)": "{:.2f}",
                    "Payout Ratio (%)": "{:.1f}",
                }),
                hide_index=True,
                width="stretch",
            )

            # Grossed-up yield bar chart
            ranked = display_div.dropna(subset=["Grossed-Up Yield (%)"]).nlargest(15, "Grossed-Up Yield (%)")
            if not ranked.empty:
                fig_div = px.bar(
                    ranked,
                    x="symbol",
                    y="Grossed-Up Yield (%)",
                    title="Top 15 by Grossed-Up Dividend Yield",
                    color="Grossed-Up Yield (%)",
                    color_continuous_scale="YlOrRd",
                    text="currency_risk",
                )
                fig_div.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig_div, width="stretch")

            # Franking distribution
            franked = filtered_eng[filtered_eng["franking_credit_multiplier"] > 1.0]
            unfranked = filtered_eng[filtered_eng["franking_credit_multiplier"] == 1.0]
            frank_data = pd.DataFrame({
                "Type": ["Franked", "Unfranked"],
                "Count": [len(franked), len(unfranked)],
            })
            fig_frank = px.pie(frank_data, values="Count", names="Type", title="Franking Credit Distribution")
            st.plotly_chart(fig_frank)
        elif eng_df.empty:
            st.info("Feature engineering data not available.")
        else:
            st.info("No stocks match the current filters.")

# ── Tab 4: Liquidity & Risk ─────────────────────────────────────────
if tab4.open:
    with tab4:
        st.header("Liquidity & Technical Risk")

        if not eng_df.empty and not filtered_eng.empty:
            liq_cols = [
                "symbol", "bid_ask_spread_pct", "range_position_52w",
                "volume_turnover_ratio", "intraday_volatility",
            ]
            liq_df = filtered_eng[liq_cols].copy()

            liq_df["spread_pct"] = liq_df["bid_ask_spread_pct"] * 100
            liq_df["range_pos"] = liq_df["range_position_52w"] * 100
            liq_df["turnover_pct"] = liq_df["volume_turnover_ratio"] * 100
            liq_df["intraday_vol"] = liq_df["intraday_volatility"] * 100

            display_liq = liq_df[["symbol", "spread_pct", "range_pos", "turnover_pct", "intraday_vol"]]
            display_liq.rename(columns={
                "spread_pct": "Bid-Ask Spread (%)",
                "range_pos": "52W Range Position (%)",
                "turnover_pct": "Volume Turnover (%)",
                "intraday_vol": "Intraday Volatility (%)",
            }, inplace=True)

            st.markdown("Transaction costs, price positioning, and short-term volatility indicators.")
            st.dataframe(
                display_liq.style.format({
                    "Bid-Ask Spread (%)": "{:.3f}",
                    "52W Range Position (%)": "{:.1f}",
                    "Volume Turnover (%)": "{:.4f}",
                    "Intraday Volatility (%)": "{:.3f}",
                }),
                hide_index=True,
                width="stretch",
            )

            # Liquidity scatter: spread vs turnover
            liq_clean = liq_df.dropna(subset=[
                "bid_ask_spread_pct", "volume_turnover_ratio",
                "intraday_volatility", "range_position_52w",
            ])
            liq_clean = liq_clean[liq_clean["range_position_52w"] >= 0]
            if not liq_clean.empty:
                fig_liq = px.scatter(
                    liq_clean,
                    x="volume_turnover_ratio",
                    y="bid_ask_spread_pct",
                    text="symbol",
                    title="Volume Turnover vs Bid-Ask Spread",
                    labels={
                        "volume_turnover_ratio": "Volume Turnover Ratio",
                        "bid_ask_spread_pct": "Bid-Ask Spread",
                    },
                    color="intraday_volatility",
                    size="range_position_52w",
                )
                st.plotly_chart(fig_liq)

            # 52-week range position histogram
            range_data = filtered_eng["range_position_52w"].dropna()
            if not range_data.empty:
                fig_range = px.histogram(
                    range_data,
                    x="range_position_52w",
                    title="52-Week Range Position Distribution",
                    labels={"range_position_52w": "Position (0=Low, 1=High)"},
                    nbins=20,
                    color_discrete_sequence=["steelblue"],
                )
                st.plotly_chart(fig_range)
        elif eng_df.empty:
            st.info("Feature engineering data not available.")
        else:
            st.info("No stocks match the current filters.")

# ── Tab 5: Trend Over Time ──────────────────────────────────────────
if tab5.open:
    with tab5:
        st.header("Trend Over Time")

        if selected_symbols:
            try:
                trend_df, failed_syms = compute_trend(selected_symbols, start_date=start_date_str, end_date=end_date_str)

                if failed_syms:
                    st.warning(f"Could not fetch history for: {', '.join(sorted(failed_syms))}")

                if not trend_df.empty and date_col:
                    y_col = growth_factor if growth_factor and growth_factor in trend_df.columns else price_col
                    if y_col:
                        y_label = y_col.replace("_", " ").title()
                        fig_line = px.line(
                            trend_df,
                            x=date_col,
                            y=y_col,
                            color=symbol_col,
                            title=f"{y_label} Trends Over Time",
                            labels={date_col: "Date", y_col: y_label, symbol_col: "Stock"},
                        )
                        fig_line.update_layout(xaxis={"type": "date"})
                        st.plotly_chart(fig_line, width="stretch")
                        display_cols = [date_col, symbol_col, y_col]
                        st.dataframe(trend_df[display_cols], hide_index=True)
                else:
                    st.warning("No trend data available for selected symbols")

            except Exception as e:
                st.error(f"Error computing trend data: {e}")
        else:
            st.info("Select stocks from the sidebar to view trend analysis")
