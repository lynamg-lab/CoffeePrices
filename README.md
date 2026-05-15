# Coffee & Climate: Price-Weather Correlation Dashboard

**Phase 1 — Live Coffee Price Dashboard**

An interactive Streamlit dashboard for monitoring ICE Arabica coffee futures (KC=F) with technical indicators. Phase 1 focuses on price visualization; Phase 2 will add weather correlation analysis across the world's top 5 coffee-producing regions.

---

## Features (Phase 1)

- **Live price data** — daily OHLCV from Yahoo Finance via `yfinance`, cached locally as parquet
- **4 summary metrics** — latest price, daily change, YTD return, 52-week range
- **3 dashboard tabs**:
  - *Price Overview* — candlestick chart with volume
  - *Technical Indicators* — SMA (50/200), Bollinger Bands (20,2sigma), RSI (14)
  - *Returns & Volatility* — daily returns histogram, rolling 30-day volatility, drawdown from ATH
- **Built-in indicator guide** — expandable explanations for every chart (what SMA, RSI, Bollinger Bands, drawdown actually mean)
- **Data source attribution** — full transparency on where data comes from and how it's cached

## Tech Stack

| Layer | Tool |
|-------|------|
| Data | `yfinance` (Yahoo Finance) |
| Processing | `pandas` |
| Visualization | `plotly` |
| Dashboard | `streamlit` |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/lynamg-lab/CoffeePrices.git
cd 03_coffee_pricing

# Install dependencies
pip install yfinance pandas plotly streamlit pyarrow

# Run the dashboard
python -m streamlit run src/dashboard/app.py
```

The app will open at `http://localhost:8501`. On first run, it downloads ~5 years of coffee futures data.

## Project Structure

```
├── src/
│   ├── config.py            # Ticker, date ranges, colour palette
│   ├── data/
│   │   └── fetch_coffee.py  # yfinance ETL with parquet caching
│   ├── visualization/
│   │   └── price_charts.py  # 7 chart builders (candlestick, SMA, BB, RSI, etc.)
│   └── dashboard/
│       └── app.py           # Streamlit app entry point
├── data/                    # Raw/processed caches (gitignored)
├── notebooks/               # Exploratory analysis
├── tests/                   # Unit tests
└── PROJECT_OUTLINE.md       # Full project plan (Phase 1 + Phase 2)
```

## What's Next (Phase 2)

Phase 2 will add:
- Weather data ingestion from Open-Meteo for Brazil, Vietnam, Colombia, Indonesia, Ethiopia
- Heatwave and drought shock event detection
- Lagged cross-correlation analysis between weather anomalies and coffee prices
- Granger causality tests and regression models
- Expanded dashboard with weather maps, correlation explorer, and event study viewer

---

*Built as a portfolio project demonstrating end-to-end data analysis: ETL, time series, visualization, and dashboarding.*
