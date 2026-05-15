"""Central configuration constants for the project."""

# Coffee futures ticker (ICE Arabica)
TICKER_COFFEE = "KC=F"

# Default date range for fetching data (5 years)
DEFAULT_START_DATE = "2020-01-01"

# Paths relative to project root
DATA_RAW_DIR = "data/raw"
COFFEE_PARQUET = "data/raw/coffee_futures.parquet"

# Chart styling — earthy pastel palette
COLOR_UP = "#8fbc8f"
COLOR_DOWN = "#c08080"
COLOR_SMA50 = "#b8860b"
COLOR_SMA200 = "#8b7355"
COLOR_BOLLINGER_FILL = "rgba(139,115,85,0.12)"
COLOR_RSI_OVERBOUGHT = "rgba(192,128,128,0.15)"
COLOR_RSI_OVERSOLD = "rgba(143,188,143,0.15)"
COLOR_VOLUME = "rgba(192,128,128,0.35)"
COLOR_VOLATILITY = "#8b7355"
COLOR_DRAWDOWN = "rgba(192,128,128,0.15)"
COLOR_CLOSE_LINE = "#4a3728"
COLOR_GRID = "rgba(74,55,40,0.08)"

PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "#faf6f0",
        "plot_bgcolor": "#faf6f0",
        "font": {"color": "#4a3728", "family": "Segoe UI, sans-serif"},
        "xaxis": {
            "gridcolor": COLOR_GRID,
            "zerolinecolor": COLOR_GRID,
            "tickfont": {"color": "#8b7355"},
        },
        "yaxis": {
            "gridcolor": COLOR_GRID,
            "zerolinecolor": COLOR_GRID,
            "tickfont": {"color": "#8b7355"},
        },
        "hoverlabel": {
            "bgcolor": "#f0ebe3",
            "font": {"color": "#4a3728"},
        },
    }
}
