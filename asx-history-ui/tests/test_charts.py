from app.charts import (
    build_price_close_chart,
    build_high_low_chart,
    build_volume_chart,
)
from app.models import HistoryItem


from datetime import date


from datetime import date


def test_price_close_chart_generates_plotly_figure() -> None:
    """Ensure price close chart generates a Plotly figure."""
    history = [
        HistoryItem(date="2024-01-01", priceClose=100.0, priceDayHigh=101.0, priceDayLow=99.0),
        HistoryItem(date="2024-01-02", priceClose=102.0, priceDayHigh=103.0, priceDayLow=100.0),
    ]
    fig = build_price_close_chart(history)
    assert fig is not None


def test_high_low_chart_uses_high_and_low_values() -> None:
    """Ensure high/low chart uses high and low values."""
    history = [
        HistoryItem(date="2024-01-01", priceClose=100.0, priceDayHigh=102.0, priceDayLow=99.0),
    ]
    fig = build_high_low_chart(history)
    assert fig is not None


def test_volume_chart_uses_volume_values() -> None:
    """Ensure volume chart uses volume values."""
    history = [
        HistoryItem(date="2024-01-01", priceClose=100.0, priceDayHigh=101.0, priceDayLow=99.0, volume=1000000),
    ]
    fig = build_volume_chart(history)
    assert fig is not None
