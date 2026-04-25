import plotly.graph_objects as go
from .models import HistoryItem

def build_price_close_chart(history: list[HistoryItem]):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[item.date for item in history],
            y=[item.priceClose for item in history],
            mode="lines",
            name="Close"
        )
    )
    fig.update_layout(
        title="Closing Price",
        xaxis_title="Date",
        yaxis_title="Price"
    )
    return fig

def build_high_low_chart(history: list[HistoryItem]):
    fig = go.Figure()
    # For simplicity, we'll plot the average of high and low as a line
    # In a more sophisticated implementation, we might show a band
    avg_values = [(item.priceDayHigh + item.priceDayLow) / 2 for item in history]
    fig.add_trace(
        go.Scatter(
            x=[item.date for item in history],
            y=avg_values,
            mode="lines",
            name="High-Low Range"
        )
    )
    fig.update_layout(
        title="High-Low Range",
        xaxis_title="Date",
        yaxis_title="Price"
    )
    return fig

def build_volume_chart(history: list[HistoryItem]):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[item.date for item in history],
            y=[item.volume for item in history],
            name="Volume"
        )
    )
    fig.update_layout(
        title="Trading Volume",
        xaxis_title="Date",
        yaxis_title="Volume"
    )
    return fig