# Coffee & Climate: A Price-Weather Correlation Dashboard

> **Portfolio-grade data analysis project** — end-to-end pipeline from raw data to interactive dashboard, correlating global coffee futures prices with climate shocks in the world's top 5 producing regions.

---

## 1. Project Overview

### The Question
*Do heatwaves and droughts in major coffee-producing regions measurably move global coffee prices, and with what lag?*

### Why It Matters
Coffee is a $200B+ global commodity acutely sensitive to weather. As climate change intensifies extreme events, understanding price-weather dynamics has real commercial value for traders, roasters, and policymakers. This project demonstrates the full data analyst toolkit — financial time series, geospatial analysis, statistical inference, and interactive visualization.

### Tech Stack
| Layer | Tools |
|-------|-------|
| Language | Python 3.11+ |
| Financial data | `yfinance` (Yahoo Finance) |
| Weather data | Open-Meteo Historical API (free, no key) |
| Geospatial | `geopandas`, `shapely`, GADM shapefiles |
| Analysis | `pandas`, `numpy`, `scipy`, `statsmodels` |
| Visualization | `plotly`, `matplotlib`, `folium` / `keplergl` |
| Dashboard | `streamlit` |
| Automation | GitHub Actions (daily scheduled run) |
| Environment | `uv` or `poetry` for dependency management |

---

## 2. Data Sources

### 2.1 Coffee Futures
- **Ticker**: `KC=F` (ICE Coffee C Arabica futures) via `yfinance`
- **Frequency**: Daily OHLCV (Open, High, Low, Close, Volume)
- **Period**: Last 10 years rolling (2015–present)
- **Supplemental**: `SB=F` (Sugar #11), `BZF=X` (USD/BRL) as control variables

### 2.2 Weather Data — Open-Meteo Historical API
- **Endpoint**: `https://archive-api.open-meteo.com/v1/archive`
- **Variables**:
  - `temperature_2m_max`, `temperature_2m_min`, `temperature_2m_mean`
  - `precipitation_sum`
  - `soil_moisture_0_to_7cm` (drought indicator)
  - `et0_fao_evapotranspiration` (water stress)
- **No API key required** — fully open

### 2.3 Top 5 Producing Regions & Bounding Boxes

| # | Country | Key Region | Lat Range | Lon Range | % of Global Production |
|---|---------|------------|-----------|-----------|------------------------|
| 1 | Brazil | Minas Gerais / Sul de Minas | -23° to -17° | -51° to -40° | ~35% |
| 2 | Vietnam | Central Highlands (Dak Lak, Lam Dong) | 11° to 15° | 107° to 109° | ~15% |
| 3 | Colombia | Eje Cafetero (Huila, Antioquia) | 1° to 7° | -77° to -73° | ~8% |
| 4 | Indonesia | Sumatra (Aceh, Lampung) | -5° to 5° | 95° to 106° | ~7% |
| 5 | Ethiopia | Sidama / Yirgacheffe / Oromia | 5° to 9° | 36° to 42° | ~5% |

**Approach**: Query Open-Meteo on a 0.5°×0.5° grid within each bounding box, then compute area-weighted means. Optionally refine with GADM level-1 admin shapefiles for precise cropping.

### 2.4 Optional Enrichment
- **GADM shapefiles**: For precise agricultural region boundaries (level 1 or 2)
- **USD/BRL exchange rate**: Controls for currency effects on Brazil-origin pricing
- **NOAA ENSO index**: El Niño/La Niña as a confounding climate variable
- **Oil prices** (`CL=F`): Energy/transport cost pass-through

---

## 3. Project Structure

```
03_coffee_pricing/
├── README.md                    # Portfolio-facing project page
├── PROJECT_OUTLINE.md           # This document
├── pyproject.toml               # Dependencies (uv/poetry)
├── .github/
│   └── workflows/
│       └── daily_update.yml     # GitHub Actions daily refresh
│
├── data/
│   ├── raw/                     # Immutable raw downloads
│   │   ├── coffee_futures.parquet
│   │   ├── weather_brazil.parquet
│   │   ├── weather_vietnam.parquet
│   │   ├── weather_colombia.parquet
│   │   ├── weather_indonesia.parquet
│   │   └── weather_ethiopia.parquet
│   ├── processed/               # Cleaned & merged datasets
│   │   ├── combined_daily.parquet
│   │   └── shock_events.parquet
│   └── external/                # Shapefiles, reference data
│       └── gadm_regions.geojson
│
├── src/
│   ├── __init__.py
│   ├── config.py                # Constants, bounding boxes, tickers
│   ├── data/
│   │   ├── __init__.py
│   │   ├── fetch_coffee.py      # yfinance ETL
│   │   ├── fetch_weather.py     # Open-Meteo ETL
│   │   ├── process_weather.py   # Grid aggregation, anomaly calc
│   │   └── merge_data.py        # Combine into analysis-ready format
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── detect_shocks.py     # Identify heatwave/drought events
│   │   ├── event_study.py       # Event-study around shock dates
│   │   ├── correlation.py       # Cross-correlation, Granger causality
│   │   └── models.py            # Regression: price ~ weather + controls
│   │
│   ├── visualization/
│   │   ├── __init__.py
│   │   ├── price_charts.py      # OHLC, rolling stats, volatility
│   │   ├── weather_maps.py      # Anomaly maps, regional dashboards
│   │   ├── correlation_plots.py # Heatmaps, lag diagrams, scatter
│   │   └── report_figures.py    # Publication-quality static figures
│   │
│   └── dashboard/
│       ├── __init__.py
│       └── app.py               # Streamlit dashboard entry point
│
├── notebooks/
│   ├── 01_eda_prices.ipynb      # Exploratory: price distribution, trends
│   ├── 02_eda_weather.ipynb     # Exploratory: climate baselines
│   ├── 03_correlation_analysis.ipynb  # Core analysis notebook
│   └── 04_event_study.ipynb     # Event study deep-dive
│
├── tests/
│   ├── __init__.py
│   ├── test_fetch_coffee.py
│   ├── test_fetch_weather.py
│   ├── test_detect_shocks.py
│   └── test_event_study.py
│
└── reports/
    └── figures/                 # Exported publication-ready charts
```

---

## 4. Methodology

### 4.1 Shock Event Detection

Define extreme weather events relative to each region's baseline climate:

| Event Type | Definition | Parameters |
|------------|------------|------------|
| **Heatwave** | Daily max temp > 90th percentile for ≥ 5 consecutive days | Window: 5 days, Threshold: P90 |
| **Drought** | Rolling 30-day precipitation < 10th percentile | Window: 30 days, Threshold: P10 |
| **Compound** | Heatwave + drought co-occurring | Intersection of above |

Percentiles calculated per region, per calendar month (accounts for seasonality).

### 4.2 Event Study Analysis

For each shock event, analyse coffee futures behaviour in a window from **30 days before** to **90 days after**:

1. **Cumulative Abnormal Return (CAR)**: Price change relative to 30-day pre-event trend
2. **Average CAR across events**: Do prices systematically rise post-shock?
3. **Statistical significance**: t-test on CAR distribution against zero
4. **By region**: Does Brazil (35% share) drive more price impact than Ethiopia (5%)?

### 4.3 Correlation Analysis

- **Cross-correlation function (CCF)**: Weather anomalies vs. price at lags 0–180 days
- **Rolling correlation**: How has the weather-price link evolved over time?
- **Granger causality test**: Do weather anomalies "Granger-cause" price movements?

### 4.4 Regression Model

```
ΔCoffeePrice_t = β₀ + β₁·Heatwave_t + β₂·Drought_t-30 + β₃·ENSO_t + β₄·USD_BRL_t + ε_t
```

Controls isolate the weather signal from macro confounders.

---

## 5. Dashboard (Streamlit)

### Pages / Sections

1. **Live Price Dashboard**
   - Candlestick chart, SMA(50/200), Bollinger Bands, RSI
   - Daily price change, YTD return, volatility cone

2. **Weather Monitor**
   - 5-panel regional view: current conditions vs. 10-year average
   - Anomaly alerts (active heatwaves/droughts highlighted)
   - Forecast overlay (next 7 days, if API available)

3. **Correlation Explorer**
   - Interactive lag-correlation heatmap (region × lag × variable)
   - Select a region, see the price response timeline
   - "What-if" slider: simulate a drought in Brazil → estimated price impact

4. **Event Study Viewer**
   - Timeline of all detected shock events
   - Click any event to see the CAR path
   - Aggregate statistics by region, year, event type

5. **Download / Export**
   - CSV export of filtered data
   - PNG/PDF export of charts

---

## 6. Automation

### GitHub Actions Daily Pipeline

```yaml
schedule:
  - cron: "0 14 * * 1-5"  # Weekdays at 14:00 UTC (after NY market close)
```

Each run:
1. Fetches latest coffee futures from yfinance
2. Fetches latest weather data from Open-Meteo
3. Updates processed datasets
4. Recalculates shock events & correlations
5. Redeploys Streamlit dashboard (if hosted)

Alternatively: schedule a local Windows Task Scheduler job or use `cron` on a cloud VM.

---

## 7. Portfolio & Job Market Positioning

### What This Demonstrates
| Skill | How It's Shown |
|-------|----------------|
| **Data Engineering** | ETL pipeline with multiple APIs, parquet storage, incremental updates |
| **Geospatial Analysis** | Grid-based spatial aggregation, shapefile processing (GADM) |
| **Time Series Analysis** | Decomposition, stationarity, cross-correlation, Granger causality |
| **Statistical Inference** | Event study methodology, hypothesis testing, confidence intervals |
| **Causal Thinking** | Confounder control (FX, ENSO), causal graph reasoning |
| **Data Visualization** | Interactive Plotly charts, Streamlit dashboard, publication plots |
| **Software Engineering** | Modular package structure, tests, type hints, CI/CD |
| **Domain Knowledge** | Commodity markets, agricultural economics, climate impacts |

### Resume Bullet Points (draft)
- Built an automated Python pipeline ingesting daily coffee futures and gridded weather data for the 5 largest producing regions (70% of global supply)
- Applied event-study methodology to quantify the causal effect of heatwaves and droughts on commodity prices, finding statistically significant price responses with 30–60 day lags
- Developed an interactive Streamlit dashboard for real-time monitoring of global coffee supply risks

### Interview Talking Points
- Why lagged correlation vs. simple correlation
- How you handled the confounders (USD, ENSO, oil)
- Limitations: observational data, no true experiment, omitted variable bias
- Potential extensions: satellite vegetation indices (NDVI), NLP on crop reports, freight cost data

---

## 8. Phased Implementation Plan

### Phase 1 — Core Pipeline (Week 1)
- [ ] Project scaffolding (`pyproject.toml`, `src/`, `data/`)
- [ ] yfinance fetcher for KC=F
- [ ] Open-Meteo fetcher for 5 regions
- [ ] Basic data cleaning & storage (parquet)

### Phase 2 — Analysis Engine (Week 2)
- [ ] Shock event detection algorithm
- [ ] Event study framework
- [ ] Cross-correlation analysis
- [ ] Regression models with controls

### Phase 3 — Visualization & Dashboard (Week 3)
- [ ] Static plotting functions (publication quality)
- [ ] Streamlit dashboard with all pages
- [ ] Interactive correlation explorer

### Phase 4 — Polish & Deploy (Week 4)
- [ ] GitHub Actions daily refresh
- [ ] README & documentation
- [ ] Tests for critical path
- [ ] Deploy to Streamlit Cloud / Hugging Face Spaces

---

## 9. Key Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"
yfinance = "^0.2"
pandas = "^2.2"
numpy = "^1.26"
openmeteo-requests = "^1.3"
requests-cache = "^1.2"
scipy = "^1.12"
statsmodels = "^0.14"
plotly = "^5.18"
dash = "^2.15"          # Alternative to streamlit
streamlit = "^1.32"
geopandas = "^0.14"
shapely = "^2.0"
folium = "^0.16"
matplotlib = "^3.8"
pytest = "^8.0"
```

---

## 10. Potential Extensions (for Extra Impact)

1. **Satellite NDVI**: Use Google Earth Engine or MODIS data to add vegetation health as a predictor
2. **NLP on crop reports**: Scrape USDA WASDE or CONAB (Brazil) bulletins for supply forecast sentiment
3. **Freight cost integration**: Shipping rates impact landed cost of coffee
4. **Option-implied volatility**: Use coffee options data to capture market uncertainty around weather events
5. **Deploy as a live web app**: Streamlit Cloud (free) or Hugging Face Spaces
6. **Add robust coffee**: KC=F is Arabica; add `RC=F` for Robusta (London) for comparison
7. **Machine learning**: ARIMAX or XGBoost model to forecast price given weather forecast inputs

---

*Last updated: May 2026*
