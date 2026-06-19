"""Fetch daily weather data from Open-Meteo Historical API for coffee-producing regions.

Queries gridded weather data within each region's bounding box and computes
regional daily averages.  Data is cached via requests_cache to avoid re-fetching
identical API calls on repeated runs.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import requests
import requests_cache

from src.config import (
    DATA_RAW_DIR,
    DEFAULT_START_DATE,
    GRID_RESOLUTION,
    OPEN_METEO_URL,
    REGIONS,
    WEATHER_VARIABLES,
)

requests_cache.install_cache(
    str(Path(DATA_RAW_DIR).parent / ".weather_cache"),
    expire_after=86400,
)


COLUMN_MAP = {
    "temperature_2m_max": "temp_max",
    "temperature_2m_min": "temp_min",
    "temperature_2m_mean": "temp_mean",
    "precipitation_sum": "precipitation",
    "soil_moisture_0_to_7cm": "soil_moisture",
    "et0_fao_evapotranspiration": "evapotranspiration",
}


def _generate_grid(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    resolution: float,
) -> list[tuple[float, float]]:
    lats = np.arange(lat_min, lat_max + resolution / 2, resolution)
    lons = np.arange(lon_min, lon_max + resolution / 2, resolution)
    return [(float(lat), float(lon)) for lat in lats for lon in lons]


def _fetch_point(lat: float, lon: float, start: str, end: str) -> pd.DataFrame | None:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": ",".join(WEATHER_VARIABLES),
        "timezone": "UTC",
    }
    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    daily = data.get("daily")
    if daily is None:
        return None

    df = pd.DataFrame({"date": pd.to_datetime(daily["time"])})
    for api_var, col_name in COLUMN_MAP.items():
        if api_var in daily:
            df[col_name] = daily[api_var]

    return df.set_index("date")


def fetch_weather(
    region_key: str,
    start: str = DEFAULT_START_DATE,
    end: str | None = None,
    resolution: float = GRID_RESOLUTION,
) -> pd.DataFrame:
    region = REGIONS[region_key]
    grid = _generate_grid(
        region["lat_min"],
        region["lat_max"],
        region["lon_min"],
        region["lon_max"],
        resolution,
    )

    print(f"Fetching {region['country']}: {len(grid)} grid points …")

    point_dfs: list[pd.DataFrame] = []
    for i, (lat, lon) in enumerate(grid):
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  {i + 1}/{len(grid)}")
        pt_df = _fetch_point(lat, lon, start, end)
        if pt_df is not None and not pt_df.empty:
            point_dfs.append(pt_df)

    if not point_dfs:
        raise RuntimeError(f"All grid points failed for {region['country']}")

    combined = pd.concat(point_dfs)
    regional = combined.groupby(combined.index).mean()

    path = Path(DATA_RAW_DIR) / f"weather_{region_key}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    regional.to_parquet(path)

    print(f"  Saved {len(regional)} days → {path}")
    return regional


def fetch_all_regions(
    start: str = DEFAULT_START_DATE,
    end: str | None = None,
    resolution: float = GRID_RESOLUTION,
) -> dict[str, pd.DataFrame]:
    results: dict[str, pd.DataFrame] = {}
    for key in REGIONS:
        results[key] = fetch_weather(key, start=start, end=end, resolution=resolution)
    return results