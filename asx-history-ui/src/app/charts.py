import plotly.graph_objects as go

from datetime import datetime

from .models import HistoryItem


def build_price_close_chart(history: list[HistoryItem]):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=[item.fetched_at for item in history],
            y=[item.priceClose for item in history],
            mode="lines",
            name="Close",
        )
    )

    fig.update_layout(
        title="Closing Price",
        xaxis_title="Date",
        yaxis_title="Price",
    )
    return fig


def build_high_low_chart(history: list[HistoryItem]):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=[item.fetched_at for item in history],
            y=[item.priceDayHigh for item in history],
            mode="lines",
            name="High",
            line=dict(color="red", width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[item.fetched_at for item in history],
            y=[item.priceDayLow for item in history],
            mode="lines",
            name="Low",
            line=dict(color="green", width=2),
        )
    )

    fig.update_layout(
        title="Day High and Day Low",
        xaxis_title="Date",
        yaxis_title="Price",
    )
    return fig


def build_volume_chart(history: list[HistoryItem]):
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=[item.fetched_at for item in history],
            y=[item.volume for item in history],
            name="Volume",
        )
    )

    fig.update_layout(
        title="Trading Volume",
        xaxis_title="Date",
        yaxis_title="Volume",
    )
    return fig
