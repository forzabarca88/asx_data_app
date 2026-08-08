"""Unit tests for the centralised tooltip/help constants.

Guards against drift between the tooltip dictionaries in ``config.py``
and the ``column_config`` keys actually wired up in ``app.py``. Each
tooltip dict must cover exactly the expected displayed-column keys so a
new column cannot silently render without an explanation.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import (
    TOOLTIP_DIVIDEND_COLS,
    TOOLTIP_GROWTH_COLS,
    TOOLTIP_LIQUIDITY_COLS,
    TOOLTIP_VALUATION_COLS,
)


def test_growth_tooltip_keys():
    """Growth dataframe tooltips cover exactly its displayed columns."""
    assert set(TOOLTIP_GROWTH_COLS.keys()) == {
        "symbol",
        "start_value",
        "end_value",
        "growth_pct",
    }


def test_valuation_tooltip_keys():
    """Valuation dataframe tooltips cover exactly its numeric columns."""
    assert set(TOOLTIP_VALUATION_COLS.keys()) == {
        "Market cap ($M)",
        "cleaned_pe",
        "earnings_yield",
        "price_to_cash",
        "free_cash_flow_yield",
    }


def test_dividend_tooltip_keys():
    """Dividend dataframe tooltips cover exactly its non-symbol columns."""
    assert set(TOOLTIP_DIVIDEND_COLS.keys()) == {
        "Raw yield (%)",
        "Franking multiplier",
        "Grossed-up yield (%)",
        "Payout ratio (%)",
        "currency_risk",
    }


def test_liquidity_tooltip_keys():
    """Liquidity dataframe tooltips cover exactly its numeric columns."""
    assert set(TOOLTIP_LIQUIDITY_COLS.keys()) == {
        "Bid-Ask spread (%)",
        "52W range position (%)",
        "Volume turnover (%)",
        "Intraday volatility (%)",
    }


def test_all_tooltip_texts_non_empty():
    """Every tooltip/help string is present and non-empty."""
    dicts = [
        TOOLTIP_GROWTH_COLS,
        TOOLTIP_VALUATION_COLS,
        TOOLTIP_DIVIDEND_COLS,
        TOOLTIP_LIQUIDITY_COLS,
    ]
    for d in dicts:
        for key, text in d.items():
            assert text and text.strip(), f"Empty tooltip for key '{key}'"
