from app.charts import build_price_close_chart, build_high_low_chart, build_volume_chart
from app.models import HistoryItem
from datetime import date
import plotly.graph_objects as go

def test_price_close_chart_generates_plotly_figure():
    # Given a list of HistoryItem
    history = [
        HistoryItem(
            date=date(2023, 1, 1),
            priceClose=100.5,
            priceDayHigh=105.0,
            priceDayLow=99.0,
            volume=1000000
        ),
        HistoryItem(
            date=date(2023, 1, 2),
            priceClose=101.0,
            priceDayHigh=106.0,
            priceDayLow=100.0,
            volume=1100000
        )
    ]
    # When we build the price close chart
    fig = build_price_close_chart(history)
    
    # Then it returns a Plotly Figure with correct data
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].type == "scatter"
    assert fig.data[0].mode == "lines"
    assert fig.data[0].name == "Close"
    assert list(fig.data[0].x) == [date(2023, 1, 1), date(2023, 1, 2)]
    assert list(fig.data[0].y) == [100.5, 101.0]
    assert fig.layout.title.text == "Closing Price"
    assert fig.layout.xaxis.title.text == "Date"
    assert fig.layout.yaxis.title.text == "Price"

def test_high_low_chart_uses_high_and_low_values():
    # Given a list of HistoryItem
    history = [
        HistoryItem(
            date=date(2023, 1, 1),
            priceClose=100.5,
            priceDayHigh=105.0,
            priceDayLow=99.0,
            volume=1000000
        ),
        HistoryItem(
            date=date(2023, 1, 2),
            priceClose=101.0,
            priceDayHigh=106.0,
            priceDayLow=100.0,
            volume=1100000
        )
    ]
    # When we build the high low chart
    fig = build_high_low_chart(history)
    
    # Then it returns a Plotly Figure with correct data
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].type == "scatter"
    assert fig.data[0].mode == "lines"
    assert fig.data[0].name == "High-Low Range"
    assert list(fig.data[0].x) == [date(2023, 1, 1), date(2023, 1, 2)]
    assert list(fig.data[0].y) == [(105.0 + 99.0)/2, (106.0 + 100.0)/2]  # Average of high and low
    # Note: In a real implementation, we might want to show a band or range, 
    # but for simplicity we're showing the average as a line
    assert fig.layout.title.text == "High-Low Range"
    assert fig.layout.xaxis.title.text == "Date"
    assert fig.layout.yaxis.title.text == "Price"

def test_volume_chart_uses_volume_values():
    # Given a list of HistoryItem
    history = [
        HistoryItem(
            date=date(2023, 1, 1),
            priceClose=100.5,
            priceDayHigh=105.0,
            priceDayLow=99.0,
            volume=1000000
        ),
        HistoryItem(
            date=date(2023, 1, 2),
            priceClose=101.0,
            priceDayHigh=106.0,
            priceDayLow=100.0,
            volume=1100000
        )
    ]
    # When we build the volume chart
    fig = build_volume_chart(history)
    
    # Then it returns a Plotly Figure with correct data
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].type == "bar"
    assert fig.data[0].name == "Volume"
    assert list(fig.data[0].x) == [date(2023, 1, 1), date(2023, 1, 2)]
    assert list(fig.data[0].y) == [1000000, 1100000]
    assert fig.layout.title.text == "Trading Volume"
    assert fig.layout.xaxis.title.text == "Date"
    assert fig.layout.yaxis.title.text == "Volume"