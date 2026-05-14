# Phase 1: Price Dashboard MVP

> **Branch**: `phase-1-price-dashboard`
> **Goal**: Fetch daily coffee futures data via yfinance and serve an interactive Streamlit dashboard with technical indicators. No weather analysis yet.

---

## Task List

### 1.1 Project Scaffolding
- [ ] Create `pyproject.toml` with project metadata and dependencies (yfinance, pandas, plotly, streamlit)
- [ ] Create `src/__init__.py` (empty, marks package)
- [ ] Create `src/config.py` with constants: ticker symbol (`KC=F`), default date range, cache expiry, style/colour palette
- [ ] Create directory structure: `src/data/`, `src/visualization/`, `src/dashboard/`, `data/raw/`
- [ ] Add `__init__.py` to each sub-package

### 1.2 yfinance Fetcher
- [ ] Implement `src/data/__init__.py`
- [ ] Implement `src/data/fetch_coffee.py`:
  - [ ] Function to download KC=F daily OHLCV from yfinance
  - [ ] Configurable date range (default: last 5 years)
  - [ ] Cache data to `data/raw/coffee_futures.parquet`
  - [ ] Function to load from cache if fresh (<1 day old), else re-fetch
  - [ ] Return clean pandas DataFrame with datetime index

### 1.3 Price Visualization Module
- [ ] Implement `src/visualization/__init__.py`
- [ ] Implement `src/visualization/price_charts.py`:
  - [ ] Candlestick chart (OHLC) using plotly
  - [ ] Line chart with SMA (50 & 200 day)
  - [ ] Bollinger Bands overlay (20-day, 2σ)
  - [ ] RSI (14-day) subplot with overbought/oversold lines
  - [ ] Volume bar chart subplot
  - [ ] Daily returns histogram
  - [ ] Volatility cone or rolling 30-day volatility line

### 1.4 Streamlit Dashboard
- [ ] Implement `src/dashboard/__init__.py`
- [ ] Implement `src/dashboard/app.py`:
  - [ ] Sidebar: date range picker, refresh button, ticker selector (future-proof for RC=F)
  - [ ] Page 1 — Price Overview: candlestick chart + volume
  - [ ] Page 2 — Technical Indicators: SMA, Bollinger Bands, RSI
  - [ ] Page 3 — Returns & Volatility: histogram, rolling vol, drawdown chart
  - [ ] Summary stat cards at top: latest price, daily change %, YTD return, 52-week range

### 1.5 Run & Verify
- [ ] Install dependencies (`pip install -e .` or `uv sync`)
- [ ] Run `streamlit run src/dashboard/app.py`
- [ ] Verify data fetches on first load (yfinance API responding)
- [ ] Verify all charts render without errors
- [ ] Test date range changes in sidebar update charts correctly
- [ ] Verify cached parquet load skips API call on refresh

### 1.6 Finalize
- [ ] Write a brief Phase 1 `README.md` (how to install, run, screenshot)
- [ ] Commit all files on `phase-1-price-dashboard`
- [ ] Merge `phase-1-price-dashboard` into `main`

---

## Success Criteria
- [ ] App launches with `streamlit run src/dashboard/app.py`
- [ ] Coffee price data displays within 3 seconds of load
- [ ] At least 4 distinct chart types visible
- [ ] Date range filtering works via sidebar
- [ ] Code is modular (separate files for fetch, viz, app)

---

*Part of the Coffee & Climate project — see `PROJECT_OUTLINE.md` for full scope.*
