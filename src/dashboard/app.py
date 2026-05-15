"""Streamlit dashboard for coffee futures price visualization."""

from datetime import date

import streamlit as st

from src.data.fetch_coffee import fetch_coffee
from src.visualization.price_charts import (
    bollinger_chart,
    candlestick_chart,
    drawdown_chart,
    returns_histogram,
    rolling_volatility_chart,
    rsi_chart,
    sma_chart,
)

st.set_page_config(
    page_title="Coffee Price Dashboard",
    page_icon="☕",
    layout="wide",
)

st.title("☕ Coffee Futures Dashboard")
st.caption("KC=F — ICE Arabica Coffee • Data: Yahoo Finance via `yfinance`")

# ---- Sidebar ----
with st.sidebar:
    st.header("Controls")
    today = date.today()
    start_date = st.date_input("Start date", value=date(2022, 1, 1), min_value=date(2000, 1, 1))
    end_date = st.date_input("End date", value=today)
    refresh = st.button("Refresh Data", use_container_width=True)

    st.divider()
    st.markdown("**Data Source**")
    st.markdown(
        "Prices sourced from **Yahoo Finance** via the `yfinance` Python library. "
        "Ticker `KC=F` represents ICE Arabica Coffee futures, quoted in US cents per pound (¢/lb). "
        "Data is cached locally and refreshed automatically once per day."
    )
    st.divider()
    st.markdown("**About**")
    st.markdown(
        "Part of the *Coffee & Climate* project. "
        "Phase 1: live price monitoring. "
        "Phase 2: weather correlation analysis."
    )

# ---- Load data ----
if refresh:
    st.cache_data.clear()

@st.cache_data(ttl=86400)
def load_data(start: str, end: str):
    return fetch_coffee(start=start, end=end)

with st.spinner("Fetching coffee futures data..."):
    df = load_data(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

if df.empty:
    st.error("No data available for the selected date range.")
    st.stop()

# ---- Stat cards ----
close = df["Close"]
latest_price = close.iloc[-1]
prev_close = close.iloc[-2] if len(close) > 1 else latest_price
daily_change = latest_price - prev_close
daily_pct = (daily_change / prev_close) * 100
ytd_start = close[close.index >= str(today.year)].iloc[0] if not close[close.index >= str(today.year)].empty else latest_price
ytd_return = (latest_price - ytd_start) / ytd_start * 100
high_52w = close[-252:].max() if len(close) >= 252 else close.max()
low_52w = close[-252:].min() if len(close) >= 252 else close.min()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest Price", f"{latest_price:.2f} ¢/lb", f"{daily_change:+.2f} ({daily_pct:+.2f}%)")
c2.metric("YTD Return", f"{ytd_return:+.2f}%")
c3.metric("52-Week High", f"{high_52w:.2f} ¢/lb")
c4.metric("52-Week Low", f"{low_52w:.2f} ¢/lb")

st.divider()

# ---- Data source banner ----
with st.expander("About This Data", expanded=False):
    st.markdown("""
    ### Data Source
    All price data comes from **Yahoo Finance** via the open-source `yfinance` Python library
    (https://pypi.org/project/yfinance/). The ticker **KC=F** represents **ICE Arabica Coffee
    futures** contracts traded on the Intercontinental Exchange (ICE). Prices are quoted in **US cents
    per pound (¢/lb)**. Data is cached locally as parquet files and refreshed once per day.

    ### What is Arabica Coffee?
    Arabica accounts for roughly 60–70% of global coffee production. It is the higher-quality species
    used in specialty coffee and trades at a premium to Robusta. Because Arabica is grown at higher
    altitudes and is more sensitive to temperature and rainfall, its supply — and therefore its price —
    is heavily influenced by weather conditions in producing regions (the focus of Phase 2 of this
    project).
    """)

# ---- Tabs ----
tab1, tab2, tab3 = st.tabs(["📊 Price Overview", "📈 Technical Indicators", "📉 Returns & Volatility"])

with tab1:
    st.plotly_chart(candlestick_chart(df), width="stretch")
    with st.expander("How to read this chart"):
        st.markdown("""
        **Candlestick chart** — each "candle" represents one trading day:\n
        - The **body** (thick bar) shows the open-to-close range. Green = price rose that day
        (close > open). Red = price fell.\n
        - The **wicks** (thin lines) show the day's high and low.\n
        - The **volume bars** below show how many contracts traded that day — taller bars mean
        heavier activity, often accompanying big price moves.
        """)

with tab2:
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(sma_chart(df), width="stretch")
        with st.expander("What is SMA?"):
            st.markdown("""
            **Simple Moving Average (SMA)** — the average closing price over a fixed number of
            days, recalculated each day as the window slides forward. It smooths out day-to-day
            noise to reveal the underlying trend.\n
            - **SMA 50** (orange) — short-term trend (~2.5 months of trading days).\n
            - **SMA 200** (purple) — long-term trend (~10 months).\n
            - A common signal: when the 50-day crosses **above** the 200-day it's called a
            "Golden Cross" (bullish); crossing **below** is a "Death Cross" (bearish).
            """)
    with col_right:
        st.plotly_chart(bollinger_chart(df), width="stretch")
        with st.expander("What are Bollinger Bands?"):
            st.markdown("""
            **Bollinger Bands** — a volatility envelope around a 20-day SMA:\n
            - The **middle line** (orange) is the 20-day SMA.\n
            - The **upper/lower bands** sit 2 standard deviations above and below the SMA.
            In a normal distribution, ~95% of prices should stay within the bands.\n
            - When the bands **squeeze** (narrow), it signals low volatility and often
            precedes a breakout. When price touches or pierces a band, it may indicate
            overbought (upper) or oversold (lower) conditions.
            """)
    st.plotly_chart(rsi_chart(df), width="stretch")
    with st.expander("What is RSI?"):
        st.markdown("""
        **Relative Strength Index (RSI, 14-day)** — a momentum oscillator that measures the
        speed and magnitude of recent price changes on a scale of 0 to 100.\n
        - **Above 70** (red zone) = traditionally "overbought" — price may be due for a
        pullback.\n
        - **Below 30** (green zone) = traditionally "oversold" — price may be due for a
        bounce.\n
        - RSI is calculated from the ratio of average gains to average losses over the
        14-day window, using an exponential smoothing formula.
        """)

with tab3:
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(returns_histogram(df), width="stretch")
        with st.expander("What is this showing?"):
            st.markdown("""
            **Daily returns histogram** — the distribution of day-over-day percentage changes
            in closing price.\n
            - A wider, flatter distribution means higher volatility (more extreme daily
            moves).\n
            - A narrow, peaked distribution means calmer price action.\n
            - The dashed line marks the **mean daily return**. In efficient markets this
            should be close to zero; a persistent positive mean suggests an upward drift
            (bull market).
            """)
    with col_right:
        st.plotly_chart(rolling_volatility_chart(df), width="stretch")
        with st.expander("What is rolling volatility?"):
            st.markdown("""
            **Rolling 30-day volatility** — the standard deviation of daily returns over a
            30-trading-day window.\n
            - It measures how much the price is swinging day-to-day, expressed as an
            annualisable percentage.\n
            - Spikes in volatility often coincide with market shocks — weather events,
            supply reports, macroeconomic news.\n
            - Traders watch volatility because it affects options pricing and position sizing.
            """)
    st.plotly_chart(drawdown_chart(df), width="stretch")
    with st.expander("What is drawdown?"):
        st.markdown("""
        **Drawdown from all-time high** — the percentage decline from the highest closing
        price ever reached in the selected period.\n
        - 0% means price is at an all-time high.\n
        - A deeper drawdown (more negative) indicates a larger peak-to-trough loss.\n
        - This is a common risk metric: "What is the worst loss an investor would have
        experienced buying at the peak?" — directly useful for understanding downside risk.
        """)
