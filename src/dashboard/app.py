"""Streamlit dashboard for coffee futures price visualization."""

from datetime import date, timedelta

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
st.caption("KC=F — ICE Arabica Coffee • Powered by yfinance")

# ---- Sidebar ----
with st.sidebar:
    st.header("Controls")
    today = date.today()
    default_start = today - timedelta(days=365 * 5)
    start_date = st.date_input("Start date", value=date(2022, 1, 1), min_value=date(2000, 1, 1))
    end_date = st.date_input("End date", value=today)
    refresh = st.button("🔄 Refresh Data", use_container_width=True)

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

# ---- Tabs ----
tab1, tab2, tab3 = st.tabs(["📊 Price Overview", "📈 Technical Indicators", "📉 Returns & Volatility"])

with tab1:
    st.plotly_chart(candlestick_chart(df), use_container_width=True)

with tab2:
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(sma_chart(df), use_container_width=True)
    with col_right:
        st.plotly_chart(bollinger_chart(df), use_container_width=True)
    st.plotly_chart(rsi_chart(df), use_container_width=True)

with tab3:
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(returns_histogram(df), use_container_width=True)
    with col_right:
        st.plotly_chart(rolling_volatility_chart(df), use_container_width=True)
    st.plotly_chart(drawdown_chart(df), use_container_width=True)
