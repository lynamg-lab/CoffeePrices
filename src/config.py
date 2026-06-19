"""Central configuration constants for the project."""

# Coffee futures ticker (ICE Arabica)
TICKER_COFFEE = "KC=F"

# Default date range for fetching data (5 years)
DEFAULT_START_DATE = "2020-01-01"

# Paths relative to project root
DATA_RAW_DIR = "data/raw"
COFFEE_PARQUET = "data/raw/coffee_futures.parquet"

# Top 5 coffee-producing regions with bounding boxes
REGIONS = {
    "brazil": {
        "country": "Brazil",
        "region_name": "Minas Gerais / Sul de Minas",
        "lat_min": -23.0,
        "lat_max": -17.0,
        "lon_min": -51.0,
        "lon_max": -40.0,
        "production_share": 0.35,
    },
    "vietnam": {
        "country": "Vietnam",
        "region_name": "Central Highlands",
        "lat_min": 11.0,
        "lat_max": 15.0,
        "lon_min": 107.0,
        "lon_max": 109.0,
        "production_share": 0.15,
    },
    "colombia": {
        "country": "Colombia",
        "region_name": "Eje Cafetero",
        "lat_min": 1.0,
        "lat_max": 7.0,
        "lon_min": -77.0,
        "lon_max": -73.0,
        "production_share": 0.08,
    },
    "indonesia": {
        "country": "Indonesia",
        "region_name": "Sumatra",
        "lat_min": -5.0,
        "lat_max": 5.0,
        "lon_min": 95.0,
        "lon_max": 106.0,
        "production_share": 0.07,
    },
    "ethiopia": {
        "country": "Ethiopia",
        "region_name": "Sidama / Yirgacheffe / Oromia",
        "lat_min": 5.0,
        "lat_max": 9.0,
        "lon_min": 36.0,
        "lon_max": 42.0,
        "production_share": 0.05,
    },
}

# Open-Meteo grid resolution (degrees) for spatial averaging
# Use 0.5 for research-grade detail (~928 total grid points), 1.0 for speed (~232)
GRID_RESOLUTION = 1.0

# Open-Meteo daily weather variables to request
WEATHER_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "soil_moisture_0_to_7cm",
    "et0_fao_evapotranspiration",
]

# Open-Meteo Historical API endpoint
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

# Analysis: thresholds for shock event detection
HEATWAVE_PERCENTILE = 90
HEATWAVE_MIN_DAYS = 5
DROUGHT_PERCENTILE = 10
DROUGHT_WINDOW_DAYS = 30

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
