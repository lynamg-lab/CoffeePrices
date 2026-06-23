"""Streamlit dashboard for coffee futures and Brazil weather analysis."""

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import DATA_PROCESSED_DIR, MESOREGIONS
from src.data.fetch_coffee import fetch_coffee
from src.data.merge_data import load_combined
from src.visualization.price_charts import (
    bollinger_chart,
    candlestick_chart,
    drawdown_chart,
    returns_histogram,
    rolling_volatility_chart,
    rsi_chart,
    sma_chart,
)
from src.visualization.production_maps import (
    mesoregion_bar_chart,
    municipality_choropleth,
    production_by_state_pie,
)
from src.visualization.weather_maps import (
    anomaly_heatmap,
    seasonal_climate_profile,
    shock_timeline,
)
from src.visualization.correlation_plots import (
    car_by_event_type,
    car_by_production_quartile,
    granger_summary_table,
    lag_correlation_heatmap,
)
from src.visualization.regression_plots import (
    actual_vs_predicted,
    coefficient_plot,
    rsquared_comparison,
    run_all_models,
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
    st.markdown("**Data Analysis**")
    refresh_analysis = st.button("Refresh Analysis Data", use_container_width=True)
    if refresh_analysis:
        st.cache_data.clear()

    st.divider()
    st.markdown("**About**")
    st.markdown(
        "Part of the *Coffee & Climate* project.<br>"
        "Phase 1: live price monitoring.<br>"
        "Phase 2: weather correlation analysis.",
        unsafe_allow_html=True,
    )

# ---- Load data ----
if refresh:
    st.cache_data.clear()

@st.cache_data(ttl=86400)
def load_data(start: str, end: str):
    return fetch_coffee(start=start, end=end)

with st.spinner("Fetching coffee futures data..."):
    df = load_data(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

# ---- Cached analysis data loaders ----
@st.cache_data(ttl=3600)
def load_analysis_data():
    return load_combined()

@st.cache_data(ttl=3600)
def load_shock_events():
    path = DATA_PROCESSED_DIR / "shock_events.parquet"
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()

@st.cache_data(ttl=3600)
def load_car_results():
    path = DATA_PROCESSED_DIR / "event_study_results.parquet"
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()

@st.cache_data(ttl=3600)
def load_regression_models():
    return run_all_models()

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

st.markdown("""
<style>
div[data-testid="stMetric"] {
    background-color: #f0ebe3;
    border: 1px solid #e0d5c5;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}
div[data-testid="stMetric"] label {
    color: #8b7355 !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #4a3728 !important;
}
</style>
""", unsafe_allow_html=True)

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
tabs = st.tabs([
    "📊 Price Overview",
    "📈 Technical Indicators",
    "📉 Returns & Volatility",
    "🗺️ Production",
    "🌦️ Weather Monitor",
    "🔗 Correlation Explorer",
    "📐 Regression Models",
])
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = tabs

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

with tab4:
    with st.spinner("Loading production maps..."):
        st.plotly_chart(municipality_choropleth(), use_container_width=True)
    c_left, c_right = st.columns(2)
    with c_left:
        st.plotly_chart(production_by_state_pie(), use_container_width=True)
    with c_right:
        st.plotly_chart(mesoregion_bar_chart(), use_container_width=True)
    with st.expander("About the production data"):
        st.markdown("""
        **IBGE Municipal Agricultural Survey (2018)** — 1,227 municipalities with non-zero
        arabica coffee production. Municipality boundaries are mapped to mesoregions using
        IBGE geocodes. Total 2018 arabica production: **2.67 million tonnes**.\n
        - Minas Gerais accounts for **70.7%** of national production.
        - The **Sul/Sudoeste de Minas** mesoregion alone produces 857k tonnes (32%).
        - Production tonnage is used as the weight when aggregating weather to mesoregion level.
        """)

with tab5:
    weather_data_available = load_analysis_data() is not None
    if not weather_data_available:
        st.warning("Weather data not available. Run the data pipeline first.")
    else:
        st.plotly_chart(anomaly_heatmap(), use_container_width=True)
        st.divider()
        st.plotly_chart(shock_timeline(), use_container_width=True)
        st.divider()
        meso_keys = sorted(MESOREGIONS.keys())
        meso_labels = {k: f"{MESOREGIONS[k]['meso_name']} ({k})" for k in meso_keys}
        selected_meso = st.selectbox(
            "Select mesoregion for seasonal climate profile",
            options=meso_keys,
            format_func=lambda k: meso_labels.get(k, k),
            index=meso_keys.index("31_10") if "31_10" in meso_keys else 0,
        )
        st.plotly_chart(seasonal_climate_profile(selected_meso), use_container_width=True)

with tab6:
    car_df = load_car_results()
    if car_df.empty:
        st.warning("Event study results not available. Run the data pipeline first.")
    else:
        row1_left, row1_right = st.columns(2)
        with row1_left:
            st.plotly_chart(car_by_event_type(), use_container_width=True)
        with row1_right:
            st.plotly_chart(lag_correlation_heatmap(), use_container_width=True)
        row2_left, row2_right = st.columns(2)
        with row2_left:
            st.plotly_chart(car_by_production_quartile(), use_container_width=True)
        with row2_right:
            st.plotly_chart(granger_summary_table(), use_container_width=True)

with tab7:
    analysis = load_analysis_data()
    if analysis is None:
        st.warning("Combined analysis data not available. Run the data pipeline first.")
    else:
        with st.spinner("Running regression models..."):
            models = load_regression_models()
        if not models:
            st.error("No model results returned.")
        else:
            model_names = [m["name"] for m in models]
            selected_idx = st.selectbox(
                "Select model",
                options=range(len(model_names)),
                format_func=lambda i: model_names[i],
                index=3,
            )
            col_left, col_right = st.columns(2)
            with col_left:
                st.plotly_chart(coefficient_plot(models[selected_idx]), use_container_width=True)
            with col_right:
                st.plotly_chart(actual_vs_predicted(models[selected_idx]), use_container_width=True)
            st.divider()
            st.plotly_chart(rsquared_comparison(models), use_container_width=True)
