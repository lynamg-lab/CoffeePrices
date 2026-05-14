"""Central configuration constants for the project."""

# Coffee futures ticker (ICE Arabica)
TICKER_COFFEE = "KC=F"

# Default date range for fetching data (5 years)
DEFAULT_START_DATE = "2020-01-01"

# Cache freshness threshold (seconds) — re-fetch if older than 1 day
CACHE_MAX_AGE_SECONDS = 86400

# Paths relative to project root
DATA_RAW_DIR = "data/raw"
COFFEE_PARQUET = "data/raw/coffee_futures.parquet"

# Chart styling
COLOR_PALETTE = {
    "up": "#26a69a",
    "down": "#ef5350",
    "sma50": "#ffa726",
    "sma200": "#ab47bc",
    "bollinger": "rgba(173,204,255,0.3)",
    "rsi_overbought": "rgba(239,83,80,0.15)",
    "rsi_oversold": "rgba(38,166,154,0.15)",
}
