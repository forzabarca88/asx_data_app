"""Chart builders for the ASX Stock Analysis Dashboard.

Bar charts (growth, valuation size, dividend yield) return DataFrames
ready for native ``st.bar_chart``. Scatter charts (P/E vs FCF, liquidity),
the 52-week range histogram, and the trend line chart return Altair
charts for ``st.altair_chart``. No Streamlit rendering occurs here —
output is consumed by ``app.py``.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

from config import (
    CHART_DATE_FORMAT,
    CHART_DATE_TICK_COUNT,
    CHART_HISTOGRAM_NBINS,
    CHART_LABEL_52W_RANGE_POSITION,
    CHART_LABEL_BID_ASK_SPREAD,
    CHART_LABEL_DATE,
    CHART_LABEL_EARNINGS_YIELD,
    CHART_LABEL_FCF_YIELD,
    CHART_LABEL_GROSS_DIVIDEND_YIELD,
    CHART_LABEL_GROWTH_PCT,
    CHART_LABEL_INTRADAY_VOLATILITY,
    CHART_LABEL_MARKET_CAP,
    CHART_LABEL_PE_RATIO,
    CHART_LABEL_RANGE_POSITION,
    CHART_LABEL_STOCK,
    CHART_LABEL_STOCK_SYMBOL,
    CHART_TREND_POINT_HIT_SIZE,
    CHART_LABEL_VOLUME_TURNOVER,
    CHART_TITLE_PE_VS_FCF,
    CHART_TITLE_RANGE_DISTRIBUTION,
    CHART_TITLE_TREND_TEMPLATE,
    CHART_TITLE_VOLUME_VS_SPREAD,
    CHART_XAXIS_TICK_ANGLE,
    SIZE_BUCKET_LABELS,
    TOP_N_DEFAULT,
    TOP_N_DIVIDEND,
    THEME_BACKGROUND_COLOR,
    THEME_BLUE_COLOR,
    THEME_CHART_CATEGORICAL_COLORS,
    THEME_CHART_SEQUENTIAL_COLORS,
    THEME_GRAY_COLOR,
    THEME_GREEN_COLOR,
    THEME_RED_COLOR,
    THEME_TEXT_COLOR,
)


# ── Type aliases ────────────────────────────────────────────────────
DataFrame = pd.DataFrame
Series = pd.Series


# ── Chart 1: Growth Rankings Bar ────────────────────────────────────
def render_growth_bar_chart(df: DataFrame, growth_factor: str, top_n: int = TOP_N_DEFAULT) -> DataFrame:
    """Prepare data for a native bar chart ranking stocks by growth percentage.

    Args:
        df: DataFrame with columns ``symbol`` and ``growth_pct``.
        growth_factor: Name of the metric used for growth calculation.
        top_n: Number of top stocks displayed.

    Returns:
        A DataFrame with display-ready columns for ``st.bar_chart``.
    """
    result = df.copy()
    result = result.rename(columns={
        "symbol": CHART_LABEL_STOCK_SYMBOL,
        "growth_pct": CHART_LABEL_GROWTH_PCT,
    })
    return result


# ── Chart 2: Valuation Size Category Bar ────────────────────────────
def render_valuation_size_bar(size_counts: DataFrame) -> DataFrame:
    """Prepare data for a native bar chart of market-cap size distribution.

    Args:
        size_counts: DataFrame with columns ``Size`` and ``Count``.

    Returns:
        A DataFrame with display-ready columns for ``st.bar_chart``,
        sorted by natural size category order.
    """
    result = size_counts.copy()
    result["_color"] = result["Size"].map({
        "Micro": THEME_GRAY_COLOR,
        "Small": THEME_BLUE_COLOR,
        "Mid": THEME_GREEN_COLOR,
        "Large": THEME_RED_COLOR,
    })
    result = result.sort_values(
        "Size",
        key=lambda col: col.map({label: i for i, label in enumerate(SIZE_BUCKET_LABELS)}),
    )
    return result.reset_index(drop=True)


# ── Chart 3: P/E vs FCF Yield Scatter ──────────────────────────────
def render_pe_fcf_scatter(df: DataFrame) -> alt.Chart:
    """Scatter plot of P/E ratio against free cash flow yield.

    Args:
        df: DataFrame with columns ``cleaned_pe``, ``free_cash_flow_yield``,
            ``symbol``, ``market_cap``, and ``earnings_yield``.

    Returns:
        An Altair chart with hover tooltips (no overlaid text labels).
    """
    return (
        alt.Chart(df)
        .mark_circle()
        .encode(
            x=alt.X("cleaned_pe:Q", title=CHART_LABEL_PE_RATIO),
            y=alt.Y("free_cash_flow_yield:Q", title=CHART_LABEL_FCF_YIELD),
            size=alt.Size("market_cap:Q", title=CHART_LABEL_MARKET_CAP),
            color=alt.Color("earnings_yield:Q", title=CHART_LABEL_EARNINGS_YIELD),
            tooltip=["symbol", "cleaned_pe", "free_cash_flow_yield", "market_cap", "earnings_yield"],
        )
        .properties(title=CHART_TITLE_PE_VS_FCF)
    )


# ── Chart 4: Top Dividend Yield Bar ─────────────────────────────────
def render_dividend_yield_bar(df: DataFrame, top_n: int = TOP_N_DIVIDEND) -> DataFrame:
    """Prepare data for a native bar chart of top stocks by dividend yield.

    Args:
        df: DataFrame with columns ``symbol``, ``Grossed-Up Yield (%)``,
            and ``currency_risk``.
        top_n: Number of top stocks to display.

    Returns:
        A DataFrame with display-ready columns for ``st.bar_chart``.
    """
    result = df.copy()
    result = result.rename(columns={
        "symbol": CHART_LABEL_STOCK_SYMBOL,
        "Grossed-up yield (%)": CHART_LABEL_GROSS_DIVIDEND_YIELD,
    })
    return result


# ── Chart 5: Liquidity Scatter (Turnover vs Spread) ─────────────────
def render_liquidity_scatter(df: DataFrame) -> alt.Chart:
    """Scatter plot of volume turnover against bid-ask spread.

    Args:
        df: DataFrame with columns ``volume_turnover_ratio``,
            ``bid_ask_spread_pct``, ``symbol``, ``intraday_volatility``,
            and ``range_position_52w``.

    Returns:
        An Altair chart with hover tooltips (no overlaid text labels).
    """
    return (
        alt.Chart(df)
        .mark_circle()
        .encode(
            x=alt.X("volume_turnover_ratio:Q", title=CHART_LABEL_VOLUME_TURNOVER),
            y=alt.Y("bid_ask_spread_pct:Q", title=CHART_LABEL_BID_ASK_SPREAD),
            size=alt.Size("range_position_52w:Q", title=CHART_LABEL_52W_RANGE_POSITION),
            color=alt.Color("intraday_volatility:Q", title=CHART_LABEL_INTRADAY_VOLATILITY),
            tooltip=["symbol", "volume_turnover_ratio", "bid_ask_spread_pct", "range_position_52w", "intraday_volatility"],
        )
        .properties(title=CHART_TITLE_VOLUME_VS_SPREAD)
    )


# ── Chart 7: 52-Week Range Histogram ────────────────────────────────
def render_range_histogram(series: Series) -> alt.Chart:
    """Histogram showing distribution of 52-week range positions.

    Args:
        series: Pandas Series of ``range_position_52w`` values.

    Returns:
        An Altair bar chart for ``st.altair_chart``.
    """
    df = series.to_frame()
    bin_step = 1.0 / CHART_HISTOGRAM_NBINS

    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(
                "range_position_52w:Q",
                bin=alt.Bin(step=bin_step),
                title=CHART_LABEL_RANGE_POSITION,
            ),
            y=alt.Y("count()", title="Count"),
            color=alt.Color(
                "count():Q",
                scale=alt.Scale(range=THEME_CHART_SEQUENTIAL_COLORS),
            ),
        )
        .properties(title=CHART_TITLE_RANGE_DISTRIBUTION)
    )


# ── Chart 8: Trend Line ─────────────────────────────────────────────
def render_trend_line(
    df: DataFrame,
    date_col: str,
    y_col: str,
    symbol_col: str,
    y_label: str,
) -> alt.Chart:
    """Build an Altair line chart tracking a metric over time per symbol.

    Uses the long-format trend DataFrame directly (no pivot) so each
    symbol's data points are plotted at their own timestamps. This
    avoids the sparse-matrix problem that occurs when different symbols
    have different fetch timestamps.

    Args:
        df: DataFrame containing time-series data (long format).
        date_col: Column name for dates.
        y_col: Column name for the metric to plot.
        symbol_col: Column name for stock symbols (used for color grouping).
        y_label: Display label for the y-axis.

    Returns:
        An Altair line chart for ``st.altair_chart``.
    """
    result = df.copy()
    result[date_col] = pd.to_datetime(result[date_col], format="mixed")
    result = result.sort_values(date_col)

    tooltip = [
        alt.Tooltip(
            f"{date_col}:T",
            title=CHART_LABEL_DATE,
            format=CHART_DATE_FORMAT,
        ),
        alt.Tooltip(symbol_col, title=CHART_LABEL_STOCK_SYMBOL),
        alt.Tooltip(y_col, title=y_label),
    ]
    color = alt.Color(
        symbol_col,
        scale=alt.Scale(range=THEME_CHART_CATEGORICAL_COLORS),
        legend=alt.Legend(title="Symbol"),
    )
    color_no_legend = alt.Color(
        symbol_col,
        scale=alt.Scale(range=THEME_CHART_CATEGORICAL_COLORS),
        legend=None,
    )

    # Visible line drawn first; an invisible point overlay drawn on top
    # carries the tooltips. A bare 1px line is nearly impossible to hover,
    # so the overlay gives each data point a ~12px hit radius.
    line = (
        alt.Chart(result)
        .mark_line()
        .encode(
            x=alt.X(
                f"{date_col}:T",
                title=CHART_LABEL_DATE,
                axis=alt.Axis(
                    format=CHART_DATE_FORMAT,
                    tickCount=CHART_DATE_TICK_COUNT,
                    labelAngle=CHART_XAXIS_TICK_ANGLE,
                ),
            ),
            y=alt.Y(y_col, title=y_label),
            color=color,
        )
    )
    points = (
        alt.Chart(result)
        .mark_circle(opacity=0, size=CHART_TREND_POINT_HIT_SIZE)
        .encode(
            x=alt.X(f"{date_col}:T", title=CHART_LABEL_DATE),
            y=alt.Y(y_col, title=y_label),
            color=color_no_legend,
            tooltip=tooltip,
        )
    )
    return line + points
