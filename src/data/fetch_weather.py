"""Fetch daily weather data from Open-Meteo Historical API for coffee-producing regions.

Queries gridded weather data within each region's bounding box, filters grid points
to land-only via Natural Earth coastline data, and computes regional daily averages.
Data is cached via requests_cache to avoid re-fetching identical API calls.
"""

import io
import zipfile
from datetime import datetime, timezone
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
    "et0_fao_evapotranspiration": "evapotranspiration",
}

_NE_110M_LAND_URL = (
    "https://naciscdn.org/naturalearth/110m/physical/ne_110m_land.zip"
)
_land_polygon = None


def _load_land_mask():
    global _land_polygon
    if _land_polygon is not None:
        return _land_polygon

    from shapely.ops import unary_union

    external_dir = Path(DATA_RAW_DIR).parent / "external"
    external_dir.mkdir(parents=True, exist_ok=True)
    shp_path = external_dir / "ne_110m_land.shp"

    if not shp_path.exists():
        print("Downloading Natural Earth land mask (600 KB) …")
        resp = requests.get(_NE_110M_LAND_URL, timeout=30)
        resp.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            zf.extractall(external_dir)

    import geopandas as gpd

    land = gpd.read_file(shp_path)
    _land_polygon = unary_union(land.geometry.values)
    return _land_polygon


def _is_land(lat: float, lon: float) -> bool:
    from shapely.geometry import Point

    return _load_land_mask().contains(Point(lon, lat))


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
    if end is None:
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    grid = _generate_grid(
        region["lat_min"],
        region["lat_max"],
        region["lon_min"],
        region["lon_max"],
        resolution,
    )

    land_points = [(lat, lon) for lat, lon in grid if _is_land(lat, lon)]
    dropped = len(grid) - len(land_points)
    print(
        f"Fetching {region['country']}: {len(land_points)}/{len(grid)} land points "
        f"({dropped} ocean dropped)"
    )

    point_dfs: list[pd.DataFrame] = []
    for i, (lat, lon) in enumerate(land_points):
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  {i + 1}/{len(land_points)}")
        pt_df = _fetch_point(lat, lon, start, end)
        if pt_df is not None and not pt_df.empty:
            point_dfs.append(pt_df)

    if not point_dfs:
        raise RuntimeError(f"All land points failed for {region['country']}")

    combined = pd.concat(point_dfs)
    regional = combined.groupby(combined.index).mean()

    path = Path(DATA_RAW_DIR) / f"weather_{region_key}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    regional.to_parquet(path)

    print(f"  Saved {len(regional)} days to {path}")
    return regional


def fetch_all_regions(
    start: str = DEFAULT_START_DATE,
    end: str | None = None,
    resolution: float = GRID_RESOLUTION,
) -> dict[str, pd.DataFrame]:
    if end is None:
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results: dict[str, pd.DataFrame] = {}
    for key in REGIONS:
        results[key] = fetch_weather(key, start=start, end=end, resolution=resolution)
    return results
