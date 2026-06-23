"""Fetch daily weather from Open-Meteo for Brazil's coffee mesoregions.

Queries weather at each mesoregion centroid and returns a daily panel of
weather variables indexed by (meso_key, date).
"""

import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import requests_cache

from src.config import (
    DATA_PROCESSED_DIR,
    DATA_RAW_DIR,
    DEFAULT_START_DATE,
    MESOREGIONS,
    OPEN_METEO_URL,
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
    except Exception as e:
        print(f"  Error at ({lat:.2f}, {lon:.2f}): {e}")
        return None

    if data.get("error"):
        print(f"  API error at ({lat:.2f}, {lon:.2f}): {data.get('reason', 'unknown')}")
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
    start: str = DEFAULT_START_DATE,
    end: str | None = None,
    delay_s: float = 2.0,
) -> pd.DataFrame:
    """Fetch weather at each mesoregion centroid.

    Returns a DataFrame with MultiIndex (meso_key, date) and weather variable columns.
    A small delay between requests avoids hitting Open-Meteo rate limits.
    """
    if end is None:
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    records = []
    meso_keys = sorted(MESOREGIONS.keys())
    print(f"Fetching weather for {len(meso_keys)} mesoregions ...")

    for i, meso_key in enumerate(meso_keys):
        meso = MESOREGIONS[meso_key]
        lat, lon = meso["centroid_lat"], meso["centroid_lon"]
        name = meso["meso_name"]

        if (i + 1) % 5 == 0 or i == 0:
            print(f"  {i + 1}/{len(meso_keys)}: {name}")

        df = _fetch_point(lat, lon, start, end)
        if df is not None:
            for date_idx, row in df.iterrows():
                rec = {"meso_key": meso_key, "date": date_idx}
                for col in COLUMN_MAP.values():
                    rec[col] = row.get(col)
                records.append(rec)
        else:
            print(f"  WARNING: No data for {name} ({meso_key})")

        time.sleep(delay_s)

    if not records:
        raise RuntimeError("No weather data fetched for any mesoregion")

    result = pd.DataFrame(records).set_index(["meso_key", "date"]).sort_index()
    result.index = result.index.set_levels(
        [result.index.levels[0], pd.to_datetime(result.index.levels[1])]
    )

    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_PROCESSED_DIR / "weather_mesoregion_daily.parquet"
    result.to_parquet(out_path)
    print(f"Saved {len(result)} mesoregion-day records to {out_path}")

    return result


def load_cached_weather() -> pd.DataFrame | None:
    path = DATA_PROCESSED_DIR / "weather_mesoregion_daily.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return None