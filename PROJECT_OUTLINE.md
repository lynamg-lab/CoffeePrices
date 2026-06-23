# Coffee & Climate: Brazil Arabica Price-Weather Dashboard

> **Portfolio-grade data analysis project** — end-to-end pipeline from raw data to interactive dashboard, correlating ICE Arabica coffee futures prices with climate shocks across Brazil's coffee-producing mesoregions.

---

## 1. Project Overview

### The Question
*Do heatwaves and droughts in Brazil's coffee-growing mesoregions measurably move global arabica prices, and with what lag? How does the price impact differ between high-altitude Sul de Minas, the hotter Cerrado, and the Atlantic Forest zones?*

### Why It Matters
Brazil produces ~35% of the world's coffee, making its weather the single most important supply-side variable in global arabica pricing. As climate change drives more frequent temperature extremes and irregular rainfall, understanding the price-weather relationship at the sub-state level has real commercial value for traders, roasters, and policymakers. This project demonstrates the full data analyst toolkit — financial time series, high-resolution geospatial analysis, statistical inference, and interactive visualization — all focused on the world's dominant coffee origin.

### Why Brazil-Only (vs. Multi-Country)
- **Depth over breadth**: Instead of shallow bounding-box averages across 5 countries, we use municipality-level production data (1,227 producing municipalities) to generate precise, production-weighted weather indices.
- **Granular spatial analysis**: Brazil's coffee regions span very different climates — high-altitude Sul de Minas (900–1,300m), hot Cerrado savanna, and humid Atlantic Forest — each likely responding differently to weather shocks.
- **Unique data asset**: The `spatial-metrics-brazil-coffee-arabica_tn_municipality.geojson` dataset (5,563 municipalities, 2015–2018 production) enables production-weighted aggregation at any administrative level: municipality, microregion, or mesoregion.
- **Stronger interview narrative**: "I built a production-weighted weather model for Brazil's 15 coffee mesoregions using IBGE municipality data" beats "I averaged weather over a box in 5 countries."

### Tech Stack
| Layer | Tools |
|-------|-------|
| Language | Python 3.11+ |
| Financial data | `yfinance` (Yahoo Finance) |
| Weather data | Open-Meteo Historical API (free, no key) |
| Spatial | `geopandas`, `shapely`, IBGE municipality GeoJSON |
| Analysis | `pandas`, `numpy`, `scipy`, `statsmodels` |
| Visualization | `plotly`, `matplotlib` |
| Dashboard | `streamlit` |
| Automation | GitHub Actions (daily scheduled run) |
| Environment | `uv` or `poetry` for dependency management |

---

## 2. Data Sources

### 2.1 Coffee Futures
- **Ticker**: `KC=F` (ICE Coffee C Arabica futures) via `yfinance`
- **Frequency**: Daily OHLCV (Open, High, Low, Close, Volume)
- **Period**: Last 10 years rolling (2015–present)
- **Supplemental**: `SB=F` (Sugar #11), `CL=F` (Crude Oil) as control variables

### 2.2 Weather Data — Open-Meteo Historical API
- **Endpoint**: `https://archive-api.open-meteo.com/v1/archive`
- **Variables**:
  - `temperature_2m_max`, `temperature_2m_min`, `temperature_2m_mean`
  - `precipitation_sum`
  - `et0_fao_evapotranspiration` (water stress)
- **No API key required** — fully open
- **Query strategy**: Fetch weather at each coffee-producing municipality's centroid, then aggregate to mesoregion weighted by production tonnage.

### 2.3 Spatial Production Data — IBGE Municipality GeoJSON

**Source file**: `data/raw/spatial-metrics-brazil-coffee-arabica_tn_municipality.geojson`

**What it contains**:
- 5,563 Brazilian municipalities with MultiPolygon boundaries
- Arabica production (tonnes) for 2015, 2016, 2017, 2018
- 1,227 municipalities have non-zero arabica production (2018 data: 2.67M tonnes total)

**Coffee-producing states and mesoregions** (2018 production):

| State | Production | % National | Key Mesoregions |
|-------|-----------|------------|-----------------|
| **Minas Gerais** | 1,885k t | 70.7% | Sul/Sudoeste (45%), Triângulo/Alto Paranaíba (20%), Zona da Mata (16%), Oeste (7%), Vale do Rio Doce (4%) |
| **São Paulo** | 342k t | 12.8% | Ribeirão Preto (46%), Campinas (24%), Marília (11%), Assis (8%) |
| **Espírito Santo** | 222k t | 8.3% | Sul (58%), Central (36%) |
| **Bahia** | 110k t | 4.1% | Centro Sul (71%), Extremo Oeste (27%) |
| **Paraná** | 65k t | 2.4% | Norte Pioneiro (69%), Norte Central (24%) |
| *Others* | <1% | — | — |

**Aggregation approach**: Weather fetched at municipality centroids, then aggregated to mesoregion level using production tonnage as weights. This gives a true production-weighted climate signal rather than an area-weighted average.

**Brazil Geographic Hierarchy**:
```
State (UF) → Mesoregion (15 coffee-relevant) → Microregion → Municipality (1,227 producing)
```

### 2.4 Control Variables
| Variable | Source | Rationale |
|----------|--------|-----------|
| **USD/BRL** | `BRL=X` via yfinance | Real depreciation inflates local BRL prices, incentivizing exports |
| **Oil prices** | `CL=F` via yfinance | Energy/fertilizer/transport cost pass-through to agriculture |
| **ENSO index** | NOAA ONI | El Niño/La Niña affects rainfall patterns across Brazil's coffee zones |

---

## 3. Project Structure

```
03_coffee_pricing/
├── README.md                    # Portfolio-facing project page
├── PROJECT_OUTLINE.md           # This document
├── pyproject.toml               # Dependencies (uv/poetry)
├── requirements.txt
├── .github/
│   └── workflows/
│       └── daily_update.yml     # GitHub Actions daily refresh
│
├── data/
│   ├── raw/                     # Immutable raw downloads
│   │   ├── coffee_futures.parquet
│   │   ├── coffee_producing_municipalities.geojson   # Production-weighted
│   │   ├── weather_brazil.parquet
│   │   └── weather_by_municipality.parquet           # Per-municipality weather
│   ├── processed/               # Cleaned & merged datasets
│   │   ├── weather_mesoregion_daily.parquet          # Production-weighted meso avg
│   │   ├── combined_daily.parquet                    # Coffee + weather merged
│   │   └── shock_events.parquet                      # Detected events
│   └── external/                # Shapefiles, reference data
│       ├── ne_50m_land/         # Natural Earth land mask
│       └── ibge_meso_lookup.json                     # Municipality → mesoregion map
│
├── src/
│   ├── __init__.py
│   ├── config.py                # Constants, mesoregions, tickers, thresholds
│   ├── data/
│   │   ├── __init__.py
│   │   ├── fetch_coffee.py      # yfinance ETL (DONE)
│   │   ├── fetch_weather.py     # Open-Meteo ETL for municipality centroids
│   │   ├── process_weather.py   # Production-weighted mesoregion aggregation
│   │   ├── spatial_lookup.py    # IBGE API: municipality → mesoregion mapping
│   │   └── merge_data.py        # Combine coffee + weather + controls
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── detect_shocks.py     # Identify heatwave/drought events per mesoregion
│   │   ├── event_study.py       # Event-study around shock dates
│   │   ├── correlation.py       # Cross-correlation, Granger causality
│   │   └── models.py            # Regression: price ~ weather + controls
│   │
│   ├── visualization/
│   │   ├── __init__.py
│   │   ├── price_charts.py      # OHLC, rolling stats, volatility (DONE)
│   │   ├── production_maps.py   # Municipal/mesoregion production choropleth
│   │   ├── weather_maps.py      # Anomaly maps, regional dashboards
│   │   ├── correlation_plots.py # Heatmaps, lag diagrams, scatter
│   │   └── report_figures.py    # Publication-quality static figures
│   │
│   └── dashboard/
│       ├── __init__.py
│       └── app.py               # Streamlit dashboard entry point
│
├── notebooks/
│   ├── 01_eda_prices.ipynb          # Exploratory: price distribution, trends
│   ├── 02_eda_weather.ipynb         # Exploratory: climate baselines by mesoregion
│   ├── 03_spatial_exploration.ipynb # Production maps, municipality analysis
│   ├── 04_correlation_analysis.ipynb  # Core analysis notebook
│   └── 05_event_study.ipynb         # Event study deep-dive
│
├── tests/
│   ├── __init__.py
│   ├── test_fetch_coffee.py
│   ├── test_fetch_weather.py
│   ├── test_process_weather.py
│   ├── test_detect_shocks.py
│   └── test_event_study.py
│
├── tools/
│   ├── visualize_regions.py     # Debugging: region map with land mask
│   └── region_map.html          # Generated output
│
└── reports/
    └── figures/                 # Exported publication-ready charts
```

---

## 4. Methodology

### 4.1 Production-Weighted Weather Indices

Instead of area-weighted grid averaging, we produce a production-weighted climate signal:

1. **Municipality centroid weather query**: Open-Meteo at each producing municipality's centroid
2. **Aggregate to mesoregion**: Weighted average of weather variables, using `production_of_arabica_coffee_tonnes_2018` as weight
3. **Anomaly calculation**: Deviation from that mesoregion's 10-year monthly baseline

```
weather_meso_t = Σ(municipality_i.production * weather_i_t) / Σ(municipality_i.production)
```

This means a municipality producing 50,000 tonnes has 500× the weight of one producing 100 tonnes — accurately reflecting supply exposure.

### 4.2 Mesoregion-Level Climate Profiles

Each of the ~15 key mesoregions has a distinct climate:

| Mesoregion | Altitude | Climate Character | Key Risk |
|-----------|----------|-------------------|----------|
| Sul/Sudoeste de Minas | 900–1,300m | Mild, seasonal rainfall | Drought, late frost |
| Triângulo/Alto Paranaíba | 800–1,100m | Hotter, Cerrado savanna | Heatwaves, irregular rain |
| Zona da Mata (MG) | 400–800m | Humid, Atlantic Forest | Excess rainfall during harvest |
| Oeste de Minas | 600–900m | Transitional Cerrado-Atlantic | Drought |
| Centro Sul Baiano | 600–900m | Semi-arid to sub-humid | Prolonged drought |
| Norte Pioneiro Paranaense | 400–700m | Subtropical, frost risk | Winter frost events |
| Sul Espírito-santense | 700–1,100m | Mountain tropical | Landslides, excess rain |

This heterogeneity is a key analytical advantage: we can compare price responses between hot/dry regions (Cerrado) and cool/humid regions (Sul de Minas) hit by the same weather system.

### 4.3 Shock Event Detection

Define extreme weather events relative to each mesoregion's baseline climate:

| Event Type | Definition | Parameters |
|------------|------------|------------|
| **Heatwave** | Daily max temp > 90th percentile for ≥ 5 consecutive days | Window: 5 days, Threshold: P90 |
| **Drought** | Rolling 30-day precipitation < 10th percentile | Window: 30 days, Threshold: P10 |
| **Compound** | Heatwave + drought co-occurring | Intersection of above |

Percentiles calculated per mesoregion, per calendar month (accounts for seasonality and different climate baselines).

### 4.4 Event Study Analysis

For each shock event, analyse coffee futures behaviour in a window from **30 days before** to **90 days after**:

1. **Cumulative Abnormal Return (CAR)**: Price change relative to pre-event trend
2. **Average CAR across events**: Do prices systematically rise post-shock?
3. **Statistical significance**: t-test on CAR distribution against zero
4. **By mesoregion**: Does a drought in Sul de Minas (45% of MG production) drive more price impact than one in Vale do Rio Doce (4%)?
5. **Production-weighted vs. unweighted**: Does weighting matter for the price signal?

### 4.5 Correlation Analysis

- **Cross-correlation function (CCF)**: Each mesoregion's weather anomalies vs. price at lags 0–180 days
- **Rolling correlation**: How has the weather-price link evolved over time? Has it strengthened with climate change?
- **Granger causality test**: Do Sul de Minas weather anomalies "Granger-cause" KC=F price movements?
- **Cross-mesoregion comparison**: Do heatwaves in Triângulo Mineiro matter more than heatwaves in Zona da Mata?

### 4.6 Regression Model

```
ΔKC_t = β₀ + β₁·Heatwave_MG_Sul_t     + β₂·Drought_MG_Sul_t-30
            + β₃·Heatwave_MG_Tri_t     + β₄·Drought_MG_Tri_t-30
            + β₅·Heatwave_ES_Sul_t     + β₆·Drought_ES_Sul_t-30
            + β₇·ENSO_t + β₈·USD_BRL_t + β₉·Oil_t
            + ε_t
```

The model lets us:
- See which regions matter most for pricing
- Isolate weather signals from macro (FX, ENSO, oil)
- Test if production-weighted indices outperform simple area averages

---

## 5. Dashboard (Streamlit)

### Pages / Sections

**Tab 1: Price Dashboard** (Phase 1 — DONE)
- Candlestick chart, SMA(50/200), Bollinger Bands, RSI
- Daily price change, YTD return, 52-week range

**Tab 2: Production & Regions**
- Interactive choropleth map: Brazilian municipalities colored by arabica production
- Toggle between municipality view and mesoregion aggregation
- Top-producing mesoregions table with production share, climate profile

**Tab 3: Weather Monitor**
- Per-mesoregion current conditions vs. 10-year average
- Anomaly heatmap: all mesoregions × weather variables
- Active heatwave/drought alerts

**Tab 4: Correlation Explorer**
- Interactive lag-correlation heatmap (mesoregion × lag × variable)
- Select a mesoregion, see the price response timeline
- "What-if" slider: simulate a drought in Sul de Minas → estimated price impact

**Tab 5: Event Study Viewer**
- Timeline of all detected shock events
- Click any event to see the CAR path
- Aggregate statistics by mesoregion, event type
- Compare events by production weight

**Tab 6: Download / Export**
- CSV export of filtered data
- PNG/PDF export of charts

---

## 6. Automation

### GitHub Actions Daily Pipeline

Each run:
1. Fetches latest coffee futures & controls from yfinance
2. Fetches latest weather from Open-Meteo for all producing municipalities
3. Aggregates to production-weighted mesoregion indices
4. Recalculates shock events & correlations
5. Redeploys Streamlit dashboard (if hosted)

---

## 7. Portfolio & Job Market Positioning

### What This Demonstrates
| Skill | How It's Shown |
|-------|----------------|
| **Data Engineering** | ETL pipeline with yfinance + Open-Meteo, parquet storage, municipality lookup via IBGE API |
| **Geospatial Analysis** | Municipality GeoJSON processing, production-weighted spatial aggregation, mesoregion mapping |
| **Time Series Analysis** | Decomposition, cross-correlation, Granger causality by mesoregion |
| **Statistical Inference** | Event study methodology, production-weighted vs. unweighted comparison |
| **Domain Knowledge** | Brazil coffee geography, mesoregion climate profiles, FX pass-through to commodities |
| **Data Visualization** | Interactive choropleth maps, Plotly charts, Streamlit multi-tab dashboard |
| **Software Engineering** | Modular package structure, tests, type hints, CI/CD |

### Resume Bullet Points (draft)
- Built a production-weighted climate risk model for Brazilian arabica coffee covering 1,227 municipalities across 15 mesoregions that produce 70% of Brazil's arabica
- Applied event-study methodology to quantify the causal effect of mesoregion-level heatwaves and droughts on ICE arabica futures, with production-weighting yielding stronger price signals than area-weighted approaches
- Developed an interactive Streamlit dashboard with choropleth maps, anomaly alerts, and correlation explorer for real-time monitoring of Brazil's coffee supply risks

### Interview Talking Points
- *"Why Brazil-only and not global?"* — Depth over breadth; municipality-level production data enables precise weighting that a multi-country bounding-box approach cannot match.
- *"Why mesoregions and not just states?"* — Minas Gerais alone spans 6 distinct climate zones from Cerrado savanna to Atlantic Forest. A statewide average washes out the signal.
- *"How do you handle confounders?"* — USD/BRL exchange rate controls for FX-driven export incentives; ENSO index controls for the broader climate cycle that affects coffee globally, not just in Brazil.
- *"What did production-weighting change vs. simple averaging?"* — (To be filled from analysis)
- *Limitations*: Observational data, no true experiment, omitted variable bias (pest/disease, labour strikes, logistics disruptions)
- *Potential extensions*: Satellite NDVI for vegetation health, CONAB crop report NLP, freight cost data, Robusta futures for comparison

---

## 8. Phased Implementation Plan

**Current branch**: `phase-2-weather-analysis`
**Status**: Phase 1 complete. Phase 2 complete.

```
main                              ← Phase 1: price dashboard MVP (MERGED)
  └── phase-2-weather-analysis     ← Phase 2: Brazil weather analysis (COMPLETE)
```

---

### Phase 1 — Price Dashboard ✓ COMPLETE

| Step | Task | Status |
|------|------|--------|
| 1.1 | Project scaffolding, config.py | ✓ |
| 1.2 | yfinance fetcher (KC=F) | ✓ |
| 1.3 | 7 price chart builders | ✓ |
| 1.4 | Streamlit dashboard (3 tabs) | ✓ |
| 1.5 | Earthy pastel theme | ✓ |
| 1.6 | PostgreSQL caching layer | ✓ |

---

### Phase 2 — Brazil Mesoregion Weather Analysis

| Step | Task | Files | Status |
|------|------|-------|--------|
| **2a** | **Spatial foundation** | | |
| 2a.1 | Build municipality → mesoregion lookup via IBGE API | `src/data/spatial_lookup.py` | ✓ |
| 2a.2 | Filter GeoJSON to producing municipalities only | `src/data/spatial_lookup.py` | ✓ |
| 2a.3 | Save production-weighted municipality metadata | `data/raw/coffee_producing_municipalities.geojson` | ✓ |
| **2b** | **Weather data** | | |
| 2b.1 | Fetch weather at municipality centroids | `src/data/fetch_weather.py` | ✓ |
| 2b.2 | Production-weighted mesoregion aggregation | `src/data/process_weather.py` | ✓ |
| 2b.3 | Fetch control variables (USD/BRL, oil, ENSO) | `src/data/fetch_controls.py` | ✓ |
| **2c** | **Merge & analysis-ready dataset** | | |
| 2c.1 | Merge coffee + weather + controls into daily panel | `src/data/merge_data.py` | ✓ |
| **2d** | **Analysis** | | |
| 2d.1 | Shock event detection (heatwave/drought per mesoregion) | `src/analysis/detect_shocks.py` | ✓ |
| 2d.2 | Event study framework | `src/analysis/event_study.py` | ✓ |
| 2d.3 | Cross-correlation & Granger causality | `src/analysis/correlation.py` | ✓ |
| 2d.4 | Regression models with controls | `src/analysis/models.py` | ✓ |
| **2e** | **Visualization** | | |
| 2e.1 | Production choropleth maps (municipality + mesoregion) | `src/visualization/production_maps.py` | ✓ |
| 2e.2 | Weather anomaly maps & dashboards | `src/visualization/weather_maps.py` | ✓ |
| 2e.3 | Correlation plots & lag diagrams | `src/visualization/correlation_plots.py` | ✓ |
| **2f** | **Dashboard expansion** | | |
| 2f.1 | Production & Regions tab | `src/dashboard/app.py` | ✓ |
| 2f.2 | Weather Monitor tab | `src/dashboard/app.py` | ✓ |
| 2f.3 | Correlation Explorer tab | `src/dashboard/app.py` | ✓ |
| 2f.4 | Event Study Viewer tab | `src/dashboard/app.py` | ✓ |
| **2g** | **Polish & deploy** | | |
| 2g.1 | GitHub Actions daily refresh | `.github/workflows/daily_update.yml` | ✓ |
| 2g.2 | Tests | `tests/` | ✓ |
| 2g.3 | Jupyter notebooks for EDA | `notebooks/` | ✓ |
| 2g.4 | Updated README | `README.md` | ✓ |

---

## 9. Key Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"
yfinance = "^0.2"
pandas = "^2.2"
numpy = "^1.26"
requests-cache = "^1.2"
scipy = "^1.12"
statsmodels = "^0.14"
plotly = "^5.18"
streamlit = "^1.32"
geopandas = "^0.14"
shapely = "^2.0"
matplotlib = "^3.8"
pytest = "^8.0"
```

---

## 10. Potential Extensions

1. **Satellite NDVI**: Google Earth Engine or MODIS vegetation health per municipality as a predictor
2. **CONAB crop report NLP**: Scrape Brazil's official crop forecasts for supply sentiment
3. **Frost event detection**: Add temperature_2m_min < 2°C as a frost shock event (critical for Paraná)
4. **Robusta comparison**: Add `RC=F` (London Robusta) — Espírito Santo and Bahia also grow robusta
5. **Machine learning**: XGBoost model to forecast 30/60/90-day price impact given weather forecasts
6. **Deploy as live web app**: Streamlit Cloud (free tier) or Hugging Face Spaces
7. **Seasonal analysis**: Split by growing season (Oct–Mar flowering/filling) vs. harvest (May–Sep)

---

*Last updated: June 2026 — rescoped to Brazil mesoregion analysis*