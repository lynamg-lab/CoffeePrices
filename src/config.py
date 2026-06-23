"""Central configuration constants for the project."""

from pathlib import Path

# Coffee futures ticker (ICE Arabica)
TICKER_COFFEE = "KC=F"

# Control variable tickers
TICKER_USDBRL = "BRL=X"
TICKER_OIL = "CL=F"

# Default date range for fetching data
DEFAULT_START_DATE = "2021-01-01"

# Paths relative to project root
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_EXTERNAL_DIR = ROOT_DIR / "data" / "external"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"

COFFEE_PARQUET = str(DATA_RAW_DIR / "coffee_futures.parquet")
MUNICIPALITY_GEOJSON = str(DATA_RAW_DIR / "spatial-metrics-brazil-coffee-arabica_tn_municipality.geojson")
PRODUCING_GEOJSON = str(DATA_RAW_DIR / "coffee_producing_municipalities.geojson")
MESO_LOOKUP_JSON = str(DATA_EXTERNAL_DIR / "ibge_meso_lookup.json")

# IBGE state codes for coffee-producing states
IBGE_STATE_CODES = {
    "MINAS GERAIS": "31",
    "SAO PAULO": "35",
    "ESPIRITO SANTO": "32",
    "BAHIA": "29",
    "PARANA": "41",
}

# Coffee-producing mesoregions of Brazil
# Each key is "{ibge_state_code}_{meso_id:02d}" for easy IBGE API matching
# Production data from 2018 IBGE municipality survey
MESOREGIONS = {
    "31_01": {
        "state_name": "MINAS GERAIS",
        "meso_name": "Noroeste de Minas",
        "ibge_state_code": "31",
        "meso_id": 1,
        "centroid_lat": -17.0872,
        "centroid_lon": -46.4408,
        "production_tonnes_2018": 39812,
        "municipalities": 12,
    },
    "31_02": {
        "state_name": "MINAS GERAIS",
        "meso_name": "Norte de Minas",
        "ibge_state_code": "31",
        "meso_id": 2,
        "centroid_lat": -16.4848,
        "centroid_lon": -43.3237,
        "production_tonnes_2018": 22591,
        "municipalities": 33,
    },
    "31_03": {
        "state_name": "MINAS GERAIS",
        "meso_name": "Jequitinhonha",
        "ibge_state_code": "31",
        "meso_id": 3,
        "centroid_lat": -17.0868,
        "centroid_lon": -42.1126,
        "production_tonnes_2018": 20102,
        "municipalities": 33,
    },
    "31_04": {
        "state_name": "MINAS GERAIS",
        "meso_name": "Vale do Mucuri",
        "ibge_state_code": "31",
        "meso_id": 4,
        "centroid_lat": -17.8220,
        "centroid_lon": -41.5764,
        "production_tonnes_2018": 2924,
        "municipalities": 11,
    },
    "31_05": {
        "state_name": "MINAS GERAIS",
        "meso_name": "Triangulo Mineiro/Alto Paranaiba",
        "ibge_state_code": "31",
        "meso_id": 5,
        "centroid_lat": -19.0588,
        "centroid_lon": -47.4137,
        "production_tonnes_2018": 378131,
        "municipalities": 40,
    },
    "31_06": {
        "state_name": "MINAS GERAIS",
        "meso_name": "Central Mineira",
        "ibge_state_code": "31",
        "meso_id": 6,
        "centroid_lat": -19.4169,
        "centroid_lon": -45.5842,
        "production_tonnes_2018": 1316,
        "municipalities": 5,
    },
    "31_07": {
        "state_name": "MINAS GERAIS",
        "meso_name": "Metropolitana de Belo Horizonte",
        "ibge_state_code": "31",
        "meso_id": 7,
        "centroid_lat": -19.7058,
        "centroid_lon": -43.4956,
        "production_tonnes_2018": 1356,
        "municipalities": 35,
    },
    "31_08": {
        "state_name": "MINAS GERAIS",
        "meso_name": "Vale do Rio Doce",
        "ibge_state_code": "31",
        "meso_id": 8,
        "centroid_lat": -19.1032,
        "centroid_lon": -42.0455,
        "production_tonnes_2018": 78361,
        "municipalities": 58,
    },
    "31_09": {
        "state_name": "MINAS GERAIS",
        "meso_name": "Oeste de Minas",
        "ibge_state_code": "31",
        "meso_id": 9,
        "centroid_lat": -20.5061,
        "centroid_lon": -45.4510,
        "production_tonnes_2018": 136866,
        "municipalities": 32,
    },
    "31_10": {
        "state_name": "MINAS GERAIS",
        "meso_name": "Sul/Sudoeste de Minas",
        "ibge_state_code": "31",
        "meso_id": 10,
        "centroid_lat": -21.6239,
        "centroid_lon": -45.9638,
        "production_tonnes_2018": 857264,
        "municipalities": 121,
    },
    "31_11": {
        "state_name": "MINAS GERAIS",
        "meso_name": "Campo das Vertentes",
        "ibge_state_code": "31",
        "meso_id": 11,
        "centroid_lat": -21.2053,
        "centroid_lon": -44.4499,
        "production_tonnes_2018": 37464,
        "municipalities": 23,
    },
    "31_12": {
        "state_name": "MINAS GERAIS",
        "meso_name": "Zona da Mata",
        "ibge_state_code": "31",
        "meso_id": 12,
        "centroid_lat": -20.8166,
        "centroid_lon": -42.6240,
        "production_tonnes_2018": 309088,
        "municipalities": 88,
    },
    "35_01": {
        "state_name": "SAO PAULO",
        "meso_name": "Sao Jose do Rio Preto",
        "ibge_state_code": "35",
        "meso_id": 1,
        "centroid_lat": -20.6156,
        "centroid_lon": -49.7726,
        "production_tonnes_2018": 808,
        "municipalities": 46,
    },
    "35_02": {
        "state_name": "SAO PAULO",
        "meso_name": "Ribeirao Preto",
        "ibge_state_code": "35",
        "meso_id": 2,
        "centroid_lat": -20.8373,
        "centroid_lon": -47.6688,
        "production_tonnes_2018": 156831,
        "municipalities": 39,
    },
    "35_03": {
        "state_name": "SAO PAULO",
        "meso_name": "Aracatuba",
        "ibge_state_code": "35",
        "meso_id": 3,
        "centroid_lat": -21.3759,
        "centroid_lon": -50.3834,
        "production_tonnes_2018": 1073,
        "municipalities": 13,
    },
    "35_04": {
        "state_name": "SAO PAULO",
        "meso_name": "Bauru",
        "ibge_state_code": "35",
        "meso_id": 4,
        "centroid_lat": -22.4043,
        "centroid_lon": -49.0417,
        "production_tonnes_2018": 19362,
        "municipalities": 48,
    },
    "35_05": {
        "state_name": "SAO PAULO",
        "meso_name": "Araraquara",
        "ibge_state_code": "35",
        "meso_id": 5,
        "centroid_lat": -21.8164,
        "centroid_lon": -48.2528,
        "production_tonnes_2018": 2295,
        "municipalities": 18,
    },
    "35_06": {
        "state_name": "SAO PAULO",
        "meso_name": "Piracicaba",
        "ibge_state_code": "35",
        "meso_id": 6,
        "centroid_lat": -22.4496,
        "centroid_lon": -47.6978,
        "production_tonnes_2018": 5087,
        "municipalities": 13,
    },
    "35_07": {
        "state_name": "SAO PAULO",
        "meso_name": "Campinas",
        "ibge_state_code": "35",
        "meso_id": 7,
        "centroid_lat": -22.2070,
        "centroid_lon": -46.8964,
        "production_tonnes_2018": 81609,
        "municipalities": 35,
    },
    "35_08": {
        "state_name": "SAO PAULO",
        "meso_name": "Presidente Prudente",
        "ibge_state_code": "35",
        "meso_id": 8,
        "centroid_lat": -21.9027,
        "centroid_lon": -51.4668,
        "production_tonnes_2018": 6808,
        "municipalities": 30,
    },
    "35_09": {
        "state_name": "SAO PAULO",
        "meso_name": "Marilia",
        "ibge_state_code": "35",
        "meso_id": 9,
        "centroid_lat": -22.1771,
        "centroid_lon": -50.0313,
        "production_tonnes_2018": 36578,
        "municipalities": 17,
    },
    "35_10": {
        "state_name": "SAO PAULO",
        "meso_name": "Assis",
        "ibge_state_code": "35",
        "meso_id": 10,
        "centroid_lat": -22.8842,
        "centroid_lon": -49.8839,
        "production_tonnes_2018": 28555,
        "municipalities": 23,
    },
    "35_11": {
        "state_name": "SAO PAULO",
        "meso_name": "Itapetininga",
        "ibge_state_code": "35",
        "meso_id": 11,
        "centroid_lat": -23.6874,
        "centroid_lon": -48.6604,
        "production_tonnes_2018": 1698,
        "municipalities": 14,
    },
    "35_12": {
        "state_name": "SAO PAULO",
        "meso_name": "Macro Metropolitana Paulista",
        "ibge_state_code": "35",
        "meso_id": 12,
        "centroid_lat": -23.2086,
        "centroid_lon": -46.9295,
        "production_tonnes_2018": 1734,
        "municipalities": 13,
    },
    "35_13": {
        "state_name": "SAO PAULO",
        "meso_name": "Vale do Paraiba Paulista",
        "ibge_state_code": "35",
        "meso_id": 13,
        "centroid_lat": -22.7871,
        "centroid_lon": -45.5528,
        "production_tonnes_2018": 26,
        "municipalities": 2,
    },
    "35_14": {
        "state_name": "SAO PAULO",
        "meso_name": "Litoral Sul Paulista",
        "ibge_state_code": "35",
        "meso_id": 14,
        "centroid_lat": -24.5238,
        "centroid_lon": -48.0675,
        "production_tonnes_2018": 7,
        "municipalities": 3,
    },
    "35_15": {
        "state_name": "SAO PAULO",
        "meso_name": "Metropolitana de Sao Paulo",
        "ibge_state_code": "35",
        "meso_id": 15,
        "centroid_lat": -23.5901,
        "centroid_lon": -46.6695,
        "production_tonnes_2018": 3,
        "municipalities": 2,
    },
    "32_01": {
        "state_name": "ESPIRITO SANTO",
        "meso_name": "Noroeste Espírito-santense",
        "ibge_state_code": "32",
        "meso_id": 1,
        "centroid_lat": -18.8787,
        "centroid_lon": -40.8533,
        "production_tonnes_2018": 12727,
        "municipalities": 8,
    },
    "32_02": {
        "state_name": "ESPIRITO SANTO",
        "meso_name": "Litoral Norte Espírito-santense",
        "ibge_state_code": "32",
        "meso_id": 2,
        "centroid_lat": -19.7748,
        "centroid_lon": -40.4260,
        "production_tonnes_2018": 47,
        "municipalities": 2,
    },
    "32_03": {
        "state_name": "ESPIRITO SANTO",
        "meso_name": "Central Espírito-santense",
        "ibge_state_code": "32",
        "meso_id": 3,
        "centroid_lat": -20.2100,
        "centroid_lon": -40.8661,
        "production_tonnes_2018": 79445,
        "municipalities": 19,
    },
    "32_04": {
        "state_name": "ESPIRITO SANTO",
        "meso_name": "Sul Espírito-santense",
        "ibge_state_code": "32",
        "meso_id": 4,
        "centroid_lat": -20.6853,
        "centroid_lon": -41.4736,
        "production_tonnes_2018": 129339,
        "municipalities": 18,
    },
    "29_01": {
        "state_name": "BAHIA",
        "meso_name": "Extremo Oeste Baiano",
        "ibge_state_code": "29",
        "meso_id": 1,
        "centroid_lat": -13.0807,
        "centroid_lon": -45.5464,
        "production_tonnes_2018": 29500,
        "municipalities": 4,
    },
    "29_03": {
        "state_name": "BAHIA",
        "meso_name": "Centro Norte Baiano",
        "ibge_state_code": "29",
        "meso_id": 3,
        "centroid_lat": -11.6653,
        "centroid_lon": -40.9200,
        "production_tonnes_2018": 2577,
        "municipalities": 11,
    },
    "29_06": {
        "state_name": "BAHIA",
        "meso_name": "Centro Sul Baiano",
        "ibge_state_code": "29",
        "meso_id": 6,
        "centroid_lat": -13.9520,
        "centroid_lon": -41.0678,
        "production_tonnes_2018": 77900,
        "municipalities": 62,
    },
    "29_07": {
        "state_name": "BAHIA",
        "meso_name": "Sul Baiano",
        "ibge_state_code": "29",
        "meso_id": 7,
        "centroid_lat": -14.0153,
        "centroid_lon": -39.6434,
        "production_tonnes_2018": 53,
        "municipalities": 5,
    },
    "41_01": {
        "state_name": "PARANA",
        "meso_name": "Noroeste Paranaense",
        "ibge_state_code": "41",
        "meso_id": 1,
        "centroid_lat": -23.4064,
        "centroid_lon": -53.0902,
        "production_tonnes_2018": 2136,
        "municipalities": 48,
    },
    "41_02": {
        "state_name": "PARANA",
        "meso_name": "Centro Ocidental Paranaense",
        "ibge_state_code": "41",
        "meso_id": 2,
        "centroid_lat": -24.2232,
        "centroid_lon": -52.4809,
        "production_tonnes_2018": 928,
        "municipalities": 21,
    },
    "41_03": {
        "state_name": "PARANA",
        "meso_name": "Norte Central Paranaense",
        "ibge_state_code": "41",
        "meso_id": 3,
        "centroid_lat": -23.5582,
        "centroid_lon": -51.6382,
        "production_tonnes_2018": 15670,
        "municipalities": 70,
    },
    "41_04": {
        "state_name": "PARANA",
        "meso_name": "Norte Pioneiro Paranaense",
        "ibge_state_code": "41",
        "meso_id": 4,
        "centroid_lat": -23.4525,
        "centroid_lon": -50.3149,
        "production_tonnes_2018": 44786,
        "municipalities": 45,
    },
    "41_05": {
        "state_name": "PARANA",
        "meso_name": "Centro Oriental Paranaense",
        "ibge_state_code": "41",
        "meso_id": 5,
        "centroid_lat": -24.0937,
        "centroid_lon": -50.6783,
        "production_tonnes_2018": 239,
        "municipalities": 2,
    },
    "41_06": {
        "state_name": "PARANA",
        "meso_name": "Oeste Paranaense",
        "ibge_state_code": "41",
        "meso_id": 6,
        "centroid_lat": -24.6354,
        "centroid_lon": -53.4989,
        "production_tonnes_2018": 1411,
        "municipalities": 14,
    },
}

# Open-Meteo daily weather variables to request
WEATHER_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
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

# Colour scale for production choropleths
PRODUCTION_COLORSCALE = [
    (0.0, "#f0ebe3"),
    (0.3, "#c8b89a"),
    (0.6, "#8b7355"),
    (0.8, "#6b5740"),
    (1.0, "#4a3728"),
]
