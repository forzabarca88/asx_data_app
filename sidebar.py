"""Sidebar widget rendering for the ASX Stock Analysis Dashboard.

Extracts all sidebar controls into a reusable module. Widgets use
st.session_state keys for persistence across reruns, and conditional
feature filters use persist_state="session" so values survive when hidden.
"""

from __future__ import annotations

import datetime
from typing import Any, NamedTuple

import streamlit as st

from config import (
    DATE_INPUT_MIN,
    HELP_GROWTH_FACTOR,
    HELP_STOCKS_FOR_TREND,
    ICON_CONTROLS,
    ICON_DATE_RANGE,
    ICON_FEATURE_FILTERS,
    ICON_FRANKED_DIVIDENDS_ONLY,
    ICON_GROWTH_FACTOR,
    ICON_MIN_GROSSED_UP_YIELD,
    ICON_MIN_MARKET_CAP,
    ICON_STOCKS_FOR_TREND,
    ICON_TOP_N_GROWTH,
    LABEL_DATE_RANGE,
    LABEL_FRANKED_DIVIDENDS_ONLY,
    LABEL_GROWTH_FACTOR,
    LABEL_SHOW_ONLY_FRANKED,
    LABEL_MIN_GROSSED_UP_YIELD,
    LABEL_MIN_MARKET_CAP,
    LABEL_SIDEBAR_CONTROLS,
    LABEL_SIDEBAR_FEATURE_FILTERS,
    LABEL_STOCKS_FOR_TREND,
    LABEL_TOP_N_GROWTH,
    SIDEBAR_DATE_RANGE_DAYS,
    SIDEBAR_MIN_MARKET_CAP,
    SIDEBAR_MIN_YIELD,
    SIDEBAR_SHOW_ONLY_FRANKED,
    STEP_MIN_MARKET_CAP,
    STEP_MIN_YIELD,
    TOP_N_DEFAULT,
    TOP_N_MAX,
    TOP_N_MIN,
)


class FilterValues(NamedTuple):
    """Named tuple holding all sidebar filter values."""
    date_range: list[datetime.date]
    selected_symbols: list[str]
    growth_factor: str | None
    top_n: int
    min_market_cap: float
    min_yield: float
    show_only_franked: bool


def init_session_state_defaults() -> None:
    """Initialize session state defaults before widgets render.

    Called from app.py before any session state keys are read,
    ensuring defaults exist on first run. Idempotent via setdefault.
    """
    today = datetime.date.today()
    st.session_state.setdefault(
        "date_range",
        [today - datetime.timedelta(days=SIDEBAR_DATE_RANGE_DAYS), today],
    )
    st.session_state.setdefault("top_n", TOP_N_DEFAULT)
    st.session_state.setdefault("min_market_cap", SIDEBAR_MIN_MARKET_CAP)
    st.session_state.setdefault("min_yield", SIDEBAR_MIN_YIELD)
    st.session_state.setdefault("show_only_franked", SIDEBAR_SHOW_ONLY_FRANKED)


def render_sidebar(
    available_symbols: list[str] | None = None,
    available_factors: list[str] | None = None,
    default_factor: str | None = None,
    eng_df: Any = None,
) -> FilterValues:
    """Render all sidebar widgets and return the collected filter values.

    Args:
        available_symbols: List of stock symbols from the API (for multiselect).
        available_factors: List of numeric columns available for growth calculation.
        default_factor: Preferred factor to select by default.
        eng_df: Engineered features DataFrame. When provided and non-empty,
            feature filter widgets (market cap, yield, franked) are rendered.

    Returns:
        FilterValues named tuple with all filter settings read from session state.

    Note:
        Call init_session_state_defaults() before this function to ensure
        all session state keys have defaults on first run.
    """
    symbols = available_symbols or []
    factors = available_factors or []
    today = datetime.date.today()

    has_feature_filters = eng_df is not None and not eng_df.empty

    with st.sidebar:
        st.header(f"{ICON_CONTROLS} {LABEL_SIDEBAR_CONTROLS}")

        # ── Date range ──────────────────────────────────────────────
        st.date_input(
            f"{ICON_DATE_RANGE} {LABEL_DATE_RANGE}",
            min_value=DATE_INPUT_MIN,
            max_value=today,
            key="date_range",
        )

        # ── Stock multiselect ───────────────────────────────────────
        selected_symbols = st.multiselect(
            f"{ICON_STOCKS_FOR_TREND} {LABEL_STOCKS_FOR_TREND}",
            options=symbols,
            help=HELP_STOCKS_FOR_TREND,
        )

        # ── Growth factor ───────────────────────────────────────────
        growth_factor = (
            st.selectbox(
                f"{ICON_GROWTH_FACTOR} {LABEL_GROWTH_FACTOR}",
                options=factors,
                index=(
                    factors.index(default_factor)
                    if default_factor and default_factor in factors
                    else 0
                ),
                help=HELP_GROWTH_FACTOR,
            )
            if factors
            else None
        )

        # ── Top N slider ────────────────────────────────────────────
        st.slider(
            f"{ICON_TOP_N_GROWTH} {LABEL_TOP_N_GROWTH}",
            min_value=TOP_N_MIN,
            max_value=TOP_N_MAX,
            key="top_n",
        )

        # ── Feature filters (conditional on engineered data) ─────────
        if has_feature_filters:
            st.header(f"{ICON_FEATURE_FILTERS} {LABEL_SIDEBAR_FEATURE_FILTERS}")

            st.number_input(
                f"{ICON_MIN_MARKET_CAP} {LABEL_MIN_MARKET_CAP}",
                min_value=0.0,
                step=STEP_MIN_MARKET_CAP,
                key="min_market_cap",
                persist_state="session",
            )

            st.number_input(
                f"{ICON_MIN_GROSSED_UP_YIELD} {LABEL_MIN_GROSSED_UP_YIELD}",
                min_value=0.0,
                step=STEP_MIN_YIELD,
                key="min_yield",
                persist_state="session",
            )

            st.toggle(
                f"{ICON_FRANKED_DIVIDENDS_ONLY} {LABEL_SHOW_ONLY_FRANKED}",
                key="show_only_franked",
                persist_state="session",
                label_visibility="collapsed",
            )

    # ── Return filter values from session state ──────────────────────
    # Read from session_state (not widget return values) so that
    # conditional filter values persist even when widgets aren't rendered.
    return FilterValues(
        date_range=list(st.session_state["date_range"]),
        selected_symbols=selected_symbols or [],
        growth_factor=growth_factor,
        top_n=st.session_state.get("top_n", TOP_N_DEFAULT),
        min_market_cap=st.session_state.get("min_market_cap", SIDEBAR_MIN_MARKET_CAP),
        min_yield=st.session_state.get("min_yield", SIDEBAR_MIN_YIELD),
        show_only_franked=st.session_state.get(
            "show_only_franked", SIDEBAR_SHOW_ONLY_FRANKED
        ),
    )
