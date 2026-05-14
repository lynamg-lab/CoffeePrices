"""Plotly-based chart builders for coffee price data."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config import COLOR_PALETTE


def candlestick_chart(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
    )
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="KC=F",
            increasing_line_color=COLOR_PALETTE["up"],
            decreasing_line_color=COLOR_PALETTE["down"],
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color=COLOR_PALETTE["down"],
            opacity=0.4,
        ),
        row=2, col=1,
    )
    fig.update_layout(
        title="Coffee Futures (KC=F) — Candlestick & Volume",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=650,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Price (US¢/lb)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    return fig


def sma_chart(df: pd.DataFrame, windows: tuple = (50, 200)) -> go.Figure:
    close = df["Close"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index, y=close,
            mode="lines", name="Close", line=dict(color="white", width=1),
        )
    )
    for w in windows:
        sma = close.rolling(window=w).mean()
        key = f"sma{w}" if w != 50 else "sma50"
        fig.add_trace(
            go.Scatter(
                x=df.index, y=sma,
                mode="lines", name=f"SMA {w}",
                line=dict(color=COLOR_PALETTE[key], width=1.5),
            )
        )
    fig.update_layout(
        title="Simple Moving Averages",
        template="plotly_dark",
        height=500,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Price (US¢/lb)")
    return fig


def bollinger_chart(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> go.Figure:
    close = df["Close"]
    sma = close.rolling(window=window).mean()
    std = close.rolling(window=window).std()
    upper = sma + num_std * std
    lower = sma - num_std * std

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index, y=upper,
            mode="lines", name="Upper Band", line=dict(width=0),
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, y=lower,
            mode="lines", name="Lower Band",
            fill="tonexty",
            fillcolor=COLOR_PALETTE["bollinger"],
            line=dict(width=0),
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, y=close,
            mode="lines", name="Close", line=dict(color="white", width=1),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, y=sma,
            mode="lines", name=f"SMA {window}",
            line=dict(color="#ffa726", width=1.5),
        )
    )
    fig.update_layout(
        title=f"Bollinger Bands ({window}-day, {num_std}σ)",
        template="plotly_dark",
        height=500,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Price (US¢/lb)")
    return fig


def rsi_chart(df: pd.DataFrame, window: int = 14) -> go.Figure:
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))

    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(
        go.Scatter(
            x=df.index, y=rsi,
            mode="lines", name=f"RSI {window}",
            line=dict(color="#42a5f5", width=1.5),
        )
    )
    fig.add_hline(y=70, line_dash="dash", line_color=COLOR_PALETTE["down"], opacity=0.6)
    fig.add_hline(y=30, line_dash="dash", line_color=COLOR_PALETTE["up"], opacity=0.6)
    fig.add_hrect(
        y0=70, y1=100,
        fillcolor=COLOR_PALETTE["rsi_overbought"], layer="below", line_width=0,
    )
    fig.add_hrect(
        y0=0, y1=30,
        fillcolor=COLOR_PALETTE["rsi_oversold"], layer="below", line_width=0,
    )
    fig.update_layout(
        title=f"Relative Strength Index ({window}-day)",
        template="plotly_dark",
        height=400,
        hovermode="x unified",
    )
    fig.update_yaxes(range=[0, 100], title_text="RSI")
    return fig


def returns_histogram(df: pd.DataFrame) -> go.Figure:
    returns = df["Close"].pct_change().dropna() * 100
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=returns,
            nbinsx=60,
            marker_color=COLOR_PALETTE["up"],
            opacity=0.75,
            name="Daily Returns",
        )
    )
    mean_val = returns.mean()
    fig.add_vline(x=mean_val, line_dash="dash", line_color="white",
                  annotation_text=f"Mean: {mean_val:.2f}%")
    fig.update_layout(
        title="Distribution of Daily Returns",
        template="plotly_dark",
        height=400,
        hovermode="x",
    )
    fig.update_xaxes(title_text="Daily Return (%)")
    fig.update_yaxes(title_text="Frequency")
    return fig


def rolling_volatility_chart(df: pd.DataFrame, window: int = 30) -> go.Figure:
    returns = df["Close"].pct_change().dropna() * 100
    vol = returns.rolling(window=window).std()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=returns.index, y=vol,
            mode="lines", name=f"{window}-day Vol",
            line=dict(color=COLOR_PALETTE["sma200"], width=1.5),
            fill="tozeroy",
            fillcolor="rgba(171,71,188,0.1)",
        )
    )
    fig.update_layout(
        title=f"Rolling {window}-Day Volatility (σ of daily returns)",
        template="plotly_dark",
        height=400,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Volatility (%)")
    return fig


def drawdown_chart(df: pd.DataFrame) -> go.Figure:
    close = df["Close"]
    peak = close.cummax()
    drawdown = (close - peak) / peak * 100
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index, y=drawdown,
            mode="lines", name="Drawdown",
            line=dict(color=COLOR_PALETTE["down"], width=1.5),
            fill="tozeroy",
            fillcolor="rgba(239,83,80,0.1)",
        )
    )
    fig.update_layout(
        title="Drawdown from All-Time High",
        template="plotly_dark",
        height=400,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Drawdown (%)")
    return fig
