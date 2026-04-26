from typing import Optional
import plotly.graph_objects as go
from .models import HistoryItem


def build_price_close_chart(history: list[HistoryItem]) -> go.Figure:
    """Build a line chart for priceClose over time."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[item.date for item in history if item.date],
            y=[item.priceClose for item in history if item.priceClose],
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


def build_high_low_chart(history: list[HistoryItem]) -> go.Figure:
    """Build a chart showing price high and low bands."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[item.date for item in history if item.date],
            y=[item.priceDayHigh for item in history if item.priceDayHigh],
            mode="lines",
            name="High",
            line=dict(color="red")
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[item.date for item in history if item.date],
            y=[item.priceDayLow for item in history if item.priceDayLow],
            mode="lines",
            name="Low",
            line=dict(color="green")
        )
    )
    fig.update_layout(
        title="Price Range (High/Low)",
        xaxis_title="Date",
        yaxis_title="Price"
    )
    return fig


def build_volume_chart(history: list[HistoryItem]) -> go.Figure:
    """Build a bar chart for volume."""
    fig = go.Figure()
    volumes = [item.volume for item in history if item.volume is not None]
    if volumes:
        dates = [item.date for item in history if item.volume is not None]
        fig.add_trace(
            go.Bar(
                x=dates,
                y=volumes,
                name="Volume"
            )
        )
        fig.update_layout(
            title="Trading Volume",
            xaxis_title="Date",
            yaxis_title="Volume"
        )
    else:
        fig = go.Figure()
        fig.update_layout(
            title="Trading Volume",
            xaxis_title="Date",
            yaxis_title="Volume",
            annotation_text="No volume data available"
        )
    return fig
