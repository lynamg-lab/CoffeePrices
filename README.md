# Coffee & Climate: Brazil Arabica Price-Weather Dashboard

**Phase 1 — Live Coffee Price Dashboard** | **Phase 2 — Brazil Mesoregion Weather Analysis (complete)**

An interactive Streamlit dashboard monitoring ICE Arabica coffee futures (KC=F) with technical indicators. Phase 2 adds production-weighted climate analysis across Brazil's 41 coffee-producing mesoregions, with shock event detection, event study methodology, and regression modelling.

---

## Features (Phase 1 — Complete)

- **Live price data** — daily OHLCV from Yahoo Finance via `yfinance`, cached locally as parquet
- **4 summary metrics** — latest price, daily change, YTD return, 52-week range
- **3 dashboard tabs**:
  - *Price Overview* — candlestick chart with volume
  - *Technical Indicators* — SMA (50/200), Bollinger Bands (20,2sigma), RSI (14)
  - *Returns & Volatility* — daily returns histogram, rolling 30-day volatility, drawdown from ATH
- **Built-in indicator guide** — expandable explanations for every chart
- **Data source attribution** — full transparency on where data comes from and how it's cached

## Features (Phase 2 — Complete)

- **High-resolution spatial foundation** — 1,227 coffee-producing Brazilian municipalities mapped to 41 mesoregions via IBGE geocodes
- **Production-weighted weather indices** — Open-Meteo (temp_max/min/mean, precipitation, evapotranspiration) at municipality centroids, aggregated to mesoregion weighted by arabica production tonnage
- **Shock event detection** — heatwave (>90th percentile temp, ≥5 days), drought (<10th percentile 30-day precip), and compound events, per mesoregion (1,122 events detected)
- **Event study analysis** — cumulative abnormal returns (CAR) around weather shocks across 10/30/60/90 day horizons (+17.3% CAR for compound events at 90d)
- **Cross-correlation & Granger causality** — lag analysis across all mesoregions, causality tests on top 6 producing zones
- **5 OLS regression models** — Newey-West standard errors with weather anomalies, USD/BRL, oil, and ENSO controls
- **7 dashboard tabs** — price overview, technical indicators, returns & volatility, production choropleth, weather monitor, correlation explorer, regression viewer
- **5 Jupyter notebooks** — EDA prices, EDA weather, spatial exploration, correlation analysis, event study deep-dive
- **33 unit tests** — covering fetch, processing, detection, and event study modules

## Tech Stack

| Layer | Tool |
|-------|------|
| Data | `yfinance`, Open-Meteo API |
| Spatial | `geopandas`, `shapely`, IBGE municipality GeoJSON |
| Analysis | `pandas`, `numpy`, `scipy`, `statsmodels` |
| Visualization | `plotly`, `matplotlib` |
| Dashboard | `streamlit` |

## Quick Start

```bash
git clone https://github.com/lynamg-lab/CoffeePrices.git
cd 03_coffee_pricing
pip install yfinance pandas plotly streamlit pyarrow
python -m streamlit run src/dashboard/app.py
```

The app opens at `http://localhost:8501`.

## Project Structure

```
├── src/
│   ├── config.py              # Ticker, mesoregions, thresholds, colour palette
│   ├── data/
│   │   ├── fetch_coffee.py    # yfinance ETL with parquet caching
│   │   ├── fetch_weather.py   # Open-Meteo ETL at municipality centroids
│   │   ├── fetch_controls.py  # USD/BRL, oil, ENSO ONI
│   │   ├── process_weather.py # Production-weighted mesoregion aggregation
│   │   ├── spatial_lookup.py  # IBGE: municipality → mesoregion mapping
│   │   └── merge_data.py      # Coffee + weather + controls
│   ├── analysis/
│   │   ├── detect_shocks.py   # Heatwave/drought/compound event detection
│   │   ├── event_study.py     # CAR analysis around shock dates
│   │   ├── correlation.py     # Cross-correlation, Granger causality
│   │   └── models.py          # OLS regression with Newey-West SE
│   ├── visualization/
│   │   ├── price_charts.py    # 7 chart builders (Phase 1)
│   │   ├── production_maps.py # Municipality choropleth + mesoregion bar chart
│   │   ├── weather_maps.py    # Anomaly heatmaps, shock timeline, climate profiles
│   │   ├── correlation_plots.py # CAR paths, lag heatmap, Granger table
│   │   └── regression_plots.py  # Coefficient plots, R² comparison, actual vs predicted
│   └── dashboard/
│       └── app.py             # 7-tab Streamlit entry point
├── data/                      # Raw/processed parquet caches
├── notebooks/                 # 5 Jupyter notebooks for EDA & analysis
│   ├── 01_eda_prices.ipynb
│   ├── 02_eda_weather.ipynb
│   ├── 03_spatial_exploration.ipynb
│   ├── 04_correlation_analysis.ipynb
│   └── 05_event_study.ipynb
├── tests/                     # 33 unit tests (pytest)
│   ├── test_fetch_coffee.py
│   ├── test_fetch_weather.py
│   ├── test_process_weather.py
│   ├── test_detect_shocks.py
│   └── test_event_study.py
└── PROJECT_OUTLINE.md         # Full project plan
```

---

*Built as a portfolio project demonstrating end-to-end data analysis: geospatial ETL, production-weighted aggregation, time series econometrics, and interactive dashboarding.*