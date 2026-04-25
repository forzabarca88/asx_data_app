import sys
sys.path.insert(0, "src")

from datetime import datetime

from app.charts import build_price_close_chart, build_high_low_chart, build_volume_chart
from app.models import HistoryItem


def test_price_close_chart_generates_plotly_figure():
    history = [
        HistoryItem(fetched_at="2024-01-01T00:00:00", priceClose=100.0, priceDayHigh=102.0, priceDayLow=99.0),
        HistoryItem(fetched_at="2024-01-02T00:00:00", priceClose=101.0, priceDayHigh=103.0, priceDayLow=100.0),
        HistoryItem(fetched_at="2024-01-03T00:00:00", priceClose=102.0, priceDayHigh=104.0, priceDayLow=101.0),
    ]
    fig = build_price_close_chart(history)
    
    assert fig is not None
    assert len(fig.data) == 1


def test_high_low_chart_uses_high_and_low_values():
    history = [
        HistoryItem(fetched_at="2024-01-01T00:00:00", priceClose=100.0, priceDayHigh=102.0, priceDayLow=99.0),
        HistoryItem(fetched_at="2024-01-02T00:00:00", priceClose=101.0, priceDayHigh=103.0, priceDayLow=100.0),
    ]
    fig = build_high_low_chart(history)
    
    assert fig is not None
    assert len(fig.data) == 2


def test_volume_chart_uses_volume_values():
    history = [
        HistoryItem(fetched_at="2024-01-01T00:00:00", priceClose=100.0, priceDayHigh=102.0, priceDayLow=99.0, volume=1000000),
        HistoryItem(fetched_at="2024-01-02T00:00:00", priceClose=101.0, priceDayHigh=103.0, priceDayLow=100.0, volume=2000000),
    ]
    fig = build_volume_chart(history)
    
    assert fig is not None
    assert len(fig.data) == 1
