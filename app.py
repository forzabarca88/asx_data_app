import logging
import streamlit as st
import pandas as pd
from api_client import get_bulk_csv_data, get_available_symbols, get_health, get_company_history
from data_processor import (
    calculate_top_n_growth,
    fetch_and_prepare_trend_data,
    detect_date_column,
    detect_price_column,
    detect_symbol_column,
    detect_available_factors,
    engineer_features,
)
from sidebar import init_session_state_defaults, render_sidebar
from charts import (
    render_growth_bar_chart,
    render_valuation_size_bar,
    render_pe_fcf_scatter,
    render_dividend_yield_bar,
    render_liquidity_scatter,
    render_range_histogram,
    render_trend_line,
)
from config import (
    APP_PAGE_TITLE,
    APP_TITLE,
    APP_LAYOUT,
    ICON_APP,

    ICON_TAB_GROWTH,
    ICON_TAB_VALUATION,
    ICON_TAB_DIVIDEND,
    ICON_TAB_LIQUIDITY,
    ICON_TAB_TREND,
    ICON_HEADER_GROWTH,
    ICON_HEADER_VALUATION,
    ICON_HEADER_DIVIDEND,
    ICON_HEADER_LIQUIDITY,
    ICON_HEADER_TREND,
    ICON_CALLOUT_ERROR,
    ICON_CALLOUT_WARNING,
    ICON_CALLOUT_INFO,
    MSG_DATA_LOAD_FAILED,
    MSG_NO_DATA_FOR_RANGE,
    MSG_API_CONNECT_FAILED,
    MSG_FEATURE_ENGINEERING_UNAVAILABLE,
    MSG_NO_GROWTH_DATA,
    MSG_NO_NUMERIC_COLUMNS,
    MSG_GROWTH_COMPUTE_ERROR,
    MSG_FEATURE_DATA_NOT_AVAILABLE,
    MSG_NO_STOCKS_MATCH_FILTERS,
    MSG_SELECT_STOCKS_FOR_TREND,
    MSG_TREND_FETCH_FAILED,
    MSG_NO_TREND_DATA,
    MSG_TREND_COMPUTE_ERROR,
    DESC_DATA_LOADED,
    DESC_SNAPSHOT_DATE,
    HEADER_GROWTH_TEMPLATE,
    HEADER_GROWTH_FALLBACK,
    HEADER_VALUATION_MATRIX,
    HEADER_DIVIDEND_ANALYSIS,
    HEADER_LIQUIDITY_RISK,
    HEADER_TREND_OVER_TIME,
    DESC_VALUATION,
    DESC_DIVIDEND,
    DESC_LIQUIDITY,
    VALUATION_SOURCE_COLS,
    VALUATION_DISPLAY_RENAME,
    VALUATION_DISPLAY_COLS,
    DIVIDEND_SOURCE_COLS,
    DIVIDEND_DISPLAY_RENAME,
    DIVIDEND_DISPLAY_COLS,
    CURRENCY_RISK_MAP,
    LIQUIDITY_SOURCE_COLS,
    LIQUIDITY_DISPLAY_RENAME,
    LIQUIDITY_DISPLAY_COLS,
    TABS,
    SIZE_BUCKET_BINS,
    SIZE_BUCKET_LABELS,
    MARKET_CAP_MILLION_MULTIPLIER,
    FRANKING_CREDIT_FRANKED_THRESHOLD,
    TOP_N_DIVIDEND,
    TREND_FACTOR_LABELS,
    CHART_LABEL_STOCK_SYMBOL,
    CHART_LABEL_GROWTH_PCT,
    CHART_LABEL_SIZE_CATEGORY,
    CHART_LABEL_STOCK_COUNT,
    CHART_LABEL_GROSS_DIVIDEND_YIELD,
    CHART_TITLE_FRANKING_DISTRIBUTION,
    LABEL_FRANKED,
    LABEL_UNFRANKED,
    THEME_GREEN_COLOR,
    THEME_ORANGE_COLOR,
)

# Configure logging for diagnostics
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

st.set_page_config(page_title=APP_PAGE_TITLE, page_icon=ICON_APP, layout=APP_LAYOUT)
st.title(APP_TITLE)


# ── Cached data functions ───────────────────────────────────────────
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
    """Compute top N growth stocks with caching on full data."""
    return calculate_top_n_growth(df, n, factor)


@st.cache_data(ttl=3600, max_entries=256)
def fetch_history(symbol, start_date=None, end_date=None):
    """Fetch history for a single symbol with caching."""
    return get_company_history(symbol, start_date=start_date, end_date=end_date)


@st.cache_data(ttl=3600, max_entries=128)
def compute_trend(symbols, start_date=None, end_date=None):
    """Fetch and prepare trend data for selected symbols with caching."""
    return fetch_and_prepare_trend_data(symbols, fetch_history, start_date=start_date, end_date=end_date)


@st.cache_data(ttl=3600, max_entries=8)
def compute_engineered(df):
    """Compute all engineered features with caching."""
    return engineer_features(df)


# ── Ensure session state defaults exist (set in sidebar.py) ─────────
init_session_state_defaults()

# Read dates from session state and convert to ISO format for API
start_date = st.session_state["date_range"][0]
end_date = st.session_state["date_range"][1]
start_date_str = start_date.isoformat()
end_date_str = end_date.isoformat()

try:
    df = load_data(start_date=start_date_str, end_date=end_date_str)
except Exception as e:
    st.error(MSG_DATA_LOAD_FAILED.format(e), icon=ICON_CALLOUT_ERROR)
    st.stop()

if df.empty:
    st.warning(MSG_NO_DATA_FOR_RANGE, icon=ICON_CALLOUT_WARNING)
    st.stop()

date_col = detect_date_column(df)
price_col = detect_price_column(df)
symbol_col = detect_symbol_column(df)

available_factors = detect_available_factors(df)
default_factor = price_col if price_col in available_factors else (
    available_factors[0] if available_factors else None
)

try:
    symbols_list = load_symbols()
except Exception as e:
    st.error(MSG_API_CONNECT_FAILED.format(e), icon=ICON_CALLOUT_ERROR)
    symbols_list = []

try:
    eng_df = compute_engineered(df)
except Exception as e:
    eng_df = pd.DataFrame()
    st.warning(MSG_FEATURE_ENGINEERING_UNAVAILABLE.format(e), icon=ICON_CALLOUT_WARNING)

st.markdown(DESC_DATA_LOADED.format(len(df), df[symbol_col].nunique() if symbol_col else 0))
if date_col:
    snapshot_date = pd.to_datetime(df[date_col], format="mixed").max().date()
    st.markdown(DESC_SNAPSHOT_DATE.format(snapshot_date))

# ── Sidebar (full render with all context) ──────────────────────────
filters = render_sidebar(
    available_symbols=symbols_list,
    available_factors=available_factors,
    default_factor=default_factor,
    eng_df=eng_df,
)

# ── Apply feature filters ───────────────────────────────────────────
if not eng_df.empty:
    filtered_eng = eng_df.copy()
    if st.session_state.get("min_market_cap", 0) > 0:
        filtered_eng = filtered_eng[
            filtered_eng["market_cap"] >= st.session_state["min_market_cap"] * MARKET_CAP_MILLION_MULTIPLIER
        ]
    if st.session_state.get("min_yield", 0) > 0:
        filtered_eng = filtered_eng[
            filtered_eng["grossed_up_yield"] >= st.session_state["min_yield"] / 100
        ]
    if st.session_state.get("show_only_franked", False):
        filtered_eng = filtered_eng[
            filtered_eng["franking_credit_multiplier"] > FRANKING_CREDIT_FRANKED_THRESHOLD
        ]
else:
    filtered_eng = pd.DataFrame()

# ── Tabs (dynamic: on_change="rerun" + .open guards) ────────────────
tab_labels = [
    f"{ICON_TAB_GROWTH} {TABS[0]}",
    f"{ICON_TAB_VALUATION} {TABS[1]}",
    f"{ICON_TAB_DIVIDEND} {TABS[2]}",
    f"{ICON_TAB_LIQUIDITY} {TABS[3]}",
    f"{ICON_TAB_TREND} {TABS[4]}",
]
tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels, on_change="rerun")

# ── Tab 1: Growth Rankings ──────────────────────────────────────────
if tab1.open:
    with tab1:
        st.header(f"{ICON_HEADER_GROWTH} {HEADER_GROWTH_TEMPLATE.format(filters.growth_factor or HEADER_GROWTH_FALLBACK)}")

        if filters.growth_factor:
            try:
                growth_df = df
                if not filtered_eng.empty:
                    allowed_symbols = set(filtered_eng["symbol"])
                    growth_df = df[df[symbol_col].isin(allowed_symbols)]
                top_n_df = compute_top_n(growth_df, filters.top_n, filters.growth_factor)

                if not top_n_df.empty:
                    with st.container(border=True):
                        chart_df = render_growth_bar_chart(top_n_df, filters.growth_factor, filters.top_n)
                        st.bar_chart(
                            chart_df,
                            x=CHART_LABEL_STOCK_SYMBOL,
                            y=CHART_LABEL_GROWTH_PCT,
                            horizontal=True,
                            x_label=CHART_LABEL_GROWTH_PCT,
                            y_label=CHART_LABEL_STOCK_SYMBOL,
                            sort="-" + CHART_LABEL_GROWTH_PCT,
                            color=THEME_GREEN_COLOR,
                        )
                        st.dataframe(top_n_df, hide_index=True)
                else:
                    st.warning(MSG_NO_GROWTH_DATA, icon=ICON_CALLOUT_WARNING)

            except Exception as e:
                st.error(MSG_GROWTH_COMPUTE_ERROR.format(e), icon=ICON_CALLOUT_ERROR)
        else:
            st.warning(MSG_NO_NUMERIC_COLUMNS, icon=ICON_CALLOUT_WARNING)

# ── Tab 2: Valuation Matrix ─────────────────────────────────────────
if tab2.open:
    with tab2:
        st.header(f"{ICON_HEADER_VALUATION} {HEADER_VALUATION_MATRIX}")

        if not eng_df.empty and not filtered_eng.empty:
            display_df = filtered_eng[VALUATION_SOURCE_COLS].copy()
            display_df["market_cap"] = display_df["market_cap"] / MARKET_CAP_MILLION_MULTIPLIER
            display_df.rename(columns=VALUATION_DISPLAY_RENAME, inplace=True)

            with st.container(border=True):
                st.markdown(DESC_VALUATION)
                st.dataframe(
                    display_df,
                    column_config={
                        "symbol": st.column_config.TextColumn("Symbol"),
                        "Market cap ($M)": st.column_config.NumberColumn(
                            "Market cap ($M)", format="$%.2f"
                        ),
                        "cleaned_pe": st.column_config.NumberColumn(
                            "P/E ratio", format="%.2f"
                        ),
                        "earnings_yield": st.column_config.NumberColumn(
                            "Earnings yield", format="%.4f"
                        ),
                        "price_to_cash": st.column_config.NumberColumn(
                            "Price/cash", format="%.2f"
                        ),
                        "free_cash_flow_yield": st.column_config.NumberColumn(
                            "FCF yield", format="%.4f"
                        ),
                    },
                    hide_index=True,
                )

            eng_df_copy = filtered_eng.copy()
            eng_df_copy["market_cap_m"] = eng_df_copy["market_cap"] / MARKET_CAP_MILLION_MULTIPLIER
            eng_df_copy["size_category"] = pd.cut(
                eng_df_copy["market_cap_m"],
                bins=SIZE_BUCKET_BINS,
                labels=SIZE_BUCKET_LABELS,
            )
            size_counts = eng_df_copy["size_category"].value_counts().reset_index()
            size_counts.columns = ["Size", "Count"]

            with st.container(border=True):
                chart_df = render_valuation_size_bar(size_counts)
                st.bar_chart(
                    chart_df,
                    x="Size",
                    y="Count",
                    x_label=CHART_LABEL_SIZE_CATEGORY,
                    y_label=CHART_LABEL_STOCK_COUNT,
                    color="_color",
                    sort=False,
                )

            pe_data = filtered_eng.dropna(subset=[
                "cleaned_pe", "free_cash_flow_yield",
                "market_cap", "earnings_yield",
            ])
            pe_data = pe_data[pe_data["market_cap"] > 0]
            if not pe_data.empty:
                with st.container(border=True):
                    chart = render_pe_fcf_scatter(pe_data)
                    st.altair_chart(chart)
        elif eng_df.empty:
            st.info(MSG_FEATURE_DATA_NOT_AVAILABLE, icon=ICON_CALLOUT_INFO)
        else:
            st.info(MSG_NO_STOCKS_MATCH_FILTERS, icon=ICON_CALLOUT_INFO)

# ── Tab 3: Dividend Analysis ────────────────────────────────────────
if tab3.open:
    with tab3:
        st.header(f"{ICON_HEADER_DIVIDEND} {HEADER_DIVIDEND_ANALYSIS}")

        if not eng_df.empty and not filtered_eng.empty:
            div_df = filtered_eng[DIVIDEND_SOURCE_COLS].copy()
            div_df["raw_yield_pct"] = div_df["raw_dividend_yield"] * 100
            div_df["grossed_up_pct"] = div_df["grossed_up_yield"] * 100
            div_df["payout_pct"] = div_df["dividend_payout_ratio"] * 100
            div_df["currency_risk"] = div_df["dividend_currency_risk"].map(CURRENCY_RISK_MAP)

            display_div = div_df[DIVIDEND_DISPLAY_COLS].copy()
            display_div.rename(columns=DIVIDEND_DISPLAY_RENAME, inplace=True)

            with st.container(border=True):
                st.markdown(DESC_DIVIDEND)
                st.dataframe(
                    display_div,
                    column_config={
                        "symbol": st.column_config.TextColumn("Symbol"),
                        "Raw yield (%)": st.column_config.NumberColumn(
                            "Raw yield (%)", format="%.2f%%"
                        ),
                        "Franking multiplier": st.column_config.NumberColumn(
                            "Franking multiplier", format="%.4f"
                        ),
                        "Grossed-up yield (%)": st.column_config.NumberColumn(
                            "Grossed-up yield (%)", format="%.2f%%"
                        ),
                        "Payout ratio (%)": st.column_config.NumberColumn(
                            "Payout ratio (%)", format="%.1f%%"
                        ),
                        "currency_risk": st.column_config.TextColumn("Currency risk"),
                    },
                    hide_index=True,
                )

            ranked = display_div.dropna(subset=["Grossed-up yield (%)"]).nlargest(
                TOP_N_DIVIDEND, "Grossed-up yield (%)"
            )
            if not ranked.empty:
                chart_df = render_dividend_yield_bar(ranked, TOP_N_DIVIDEND)
                with st.container(border=True):
                    st.bar_chart(
                        chart_df,
                        x=CHART_LABEL_STOCK_SYMBOL,
                        y=CHART_LABEL_GROSS_DIVIDEND_YIELD,
                        horizontal=True,
                        x_label=CHART_LABEL_GROSS_DIVIDEND_YIELD,
                        y_label=CHART_LABEL_STOCK_SYMBOL,
                        sort="-" + CHART_LABEL_GROSS_DIVIDEND_YIELD,
                        color=THEME_ORANGE_COLOR,
                    )

            franked_count = int(
                (filtered_eng["franking_credit_multiplier"] > FRANKING_CREDIT_FRANKED_THRESHOLD).sum()
            )
            unfranked_count = int(
                (filtered_eng["franking_credit_multiplier"] == FRANKING_CREDIT_FRANKED_THRESHOLD).sum()
            )
            total = franked_count + unfranked_count
            franked_pct = f"{franked_count / total * 100:.1f}%" if total else "0%"
            unfranked_pct = f"{unfranked_count / total * 100:.1f}%" if total else "0%"

            with st.container(border=True):
                st.subheader(f":material/pie_chart: {CHART_TITLE_FRANKING_DISTRIBUTION}")
                c1, c2 = st.columns(2, border=True)
                with c1:
                    st.metric(LABEL_FRANKED, f"{franked_count:,}", franked_pct, border=True)
                with c2:
                    st.metric(LABEL_UNFRANKED, f"{unfranked_count:,}", unfranked_pct, border=True)
        elif eng_df.empty:
            st.info(MSG_FEATURE_DATA_NOT_AVAILABLE, icon=ICON_CALLOUT_INFO)
        else:
            st.info(MSG_NO_STOCKS_MATCH_FILTERS, icon=ICON_CALLOUT_INFO)

# ── Tab 4: Liquidity & Risk ─────────────────────────────────────────
if tab4.open:
    with tab4:
        st.header(f"{ICON_HEADER_LIQUIDITY} {HEADER_LIQUIDITY_RISK}")

        if not eng_df.empty and not filtered_eng.empty:
            liq_df = filtered_eng[LIQUIDITY_SOURCE_COLS].copy()
            liq_df["spread_pct"] = liq_df["bid_ask_spread_pct"] * 100
            liq_df["range_pos"] = liq_df["range_position_52w"] * 100
            liq_df["turnover_pct"] = liq_df["volume_turnover_ratio"] * 100
            liq_df["intraday_vol"] = liq_df["intraday_volatility"] * 100

            display_liq = liq_df[LIQUIDITY_DISPLAY_COLS].copy()
            display_liq.rename(columns=LIQUIDITY_DISPLAY_RENAME, inplace=True)

            with st.container(border=True):
                st.markdown(DESC_LIQUIDITY)
                st.dataframe(
                    display_liq,
                    column_config={
                        "symbol": st.column_config.TextColumn("Symbol"),
                        "Bid-Ask spread (%)": st.column_config.NumberColumn(
                            "Bid-Ask spread (%)", format="%.3f%%"
                        ),
                        "52W range position (%)": st.column_config.NumberColumn(
                            "52W range position (%)", format="%.1f%%"
                        ),
                        "Volume turnover (%)": st.column_config.NumberColumn(
                            "Volume turnover (%)", format="%.4f%%"
                        ),
                        "Intraday volatility (%)": st.column_config.NumberColumn(
                            "Intraday volatility (%)", format="%.3f%%"
                        ),
                    },
                    hide_index=True,
                )

            liq_clean = liq_df.dropna(subset=[
                "bid_ask_spread_pct", "volume_turnover_ratio",
                "intraday_volatility", "range_position_52w",
            ])
            liq_clean = liq_clean[liq_clean["range_position_52w"] >= 0]
            if not liq_clean.empty:
                with st.container(border=True):
                    chart = render_liquidity_scatter(liq_clean)
                    st.altair_chart(chart)

            range_data = filtered_eng["range_position_52w"].dropna()
            if not range_data.empty:
                with st.container(border=True):
                    chart = render_range_histogram(range_data)
                    st.altair_chart(chart)
        elif eng_df.empty:
            st.info(MSG_FEATURE_DATA_NOT_AVAILABLE, icon=ICON_CALLOUT_INFO)
        else:
            st.info(MSG_NO_STOCKS_MATCH_FILTERS, icon=ICON_CALLOUT_INFO)

# ── Tab 5: Trend Over Time ──────────────────────────────────────────
if tab5.open:
    with tab5:
        st.header(f"{ICON_HEADER_TREND} {HEADER_TREND_OVER_TIME}")

        if filters.selected_symbols:
            try:
                trend_df, failed_syms = compute_trend(
                    filters.selected_symbols,
                    start_date=start_date_str,
                    end_date=end_date_str,
                )

                if failed_syms:
                    st.warning(MSG_TREND_FETCH_FAILED.format(", ".join(sorted(failed_syms))), icon=ICON_CALLOUT_WARNING)

                if not trend_df.empty and date_col:
                    y_col = (
                        filters.growth_factor
                        if filters.growth_factor and filters.growth_factor in trend_df.columns
                        else price_col
                    )
                    if y_col:
                        y_label = TREND_FACTOR_LABELS.get(y_col, y_col)
                        chart = render_trend_line(trend_df, date_col, y_col, symbol_col, y_label)
                        with st.container(border=True):
                            st.altair_chart(chart, width="stretch")
                            st.dataframe(trend_df[[date_col, symbol_col, y_col]], hide_index=True)
                else:
                    st.warning(MSG_NO_TREND_DATA, icon=ICON_CALLOUT_WARNING)

            except Exception as e:
                st.error(MSG_TREND_COMPUTE_ERROR.format(e), icon=ICON_CALLOUT_ERROR)
        else:
            st.info(MSG_SELECT_STOCKS_FOR_TREND, icon=ICON_CALLOUT_INFO)
