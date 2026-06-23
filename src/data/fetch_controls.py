"""Fetch control variable data (USD/BRL, Oil, ENSO) for regression models."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from src.config import DATA_PROCESSED_DIR, TICKER_OIL, TICKER_USDBRL


def fetch_usdbrl(start: str, end: str | None = None) -> pd.DataFrame:
    """Fetch USD/BRL exchange rate from Yahoo Finance."""
    import yfinance as yf

    if end is None:
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    df = yf.download(TICKER_USDBRL, start=start, end=end, progress=False)
    if df.empty:
        raise RuntimeError(f"No USD/BRL data for {start} to {end}")
    df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)
    df = df[["Close"]].rename(columns={"Close": "usdbrl"})
    return df.sort_index()


def fetch_oil(start: str, end: str | None = None) -> pd.DataFrame:
    """Fetch crude oil futures (CL=F) from Yahoo Finance."""
    import yfinance as yf

    if end is None:
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    df = yf.download(TICKER_OIL, start=start, end=end, progress=False)
    if df.empty:
        raise RuntimeError(f"No oil data for {start} to {end}")
    df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)
    df = df[["Close"]].rename(columns={"Close": "oil"})
    return df.sort_index()


_SEASON_TO_MID_MONTH = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4,
    "AMJ": 5, "MJJ": 6, "JJA": 7, "JAS": 8,
    "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}


def fetch_enso(start: str, end: str | None = None) -> pd.DataFrame:
    """Fetch Oceanic Nino Index (ONI) from NOAA.

    ONI is a 3-month running mean of SST anomalies in the Nino 3.4 region.
    Each row is labeled by a 3-month season (e.g. DJF, JFM); the midpoint
    month is used as the date index. Returns a monthly-frequency DataFrame.
    """
    url = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    records = []
    for line in resp.text.splitlines():
        line = line.strip()
        if not line or line.startswith("SEAS"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        season, year_str, _, anom_str = parts[:4]
        if season not in _SEASON_TO_MID_MONTH:
            continue
        try:
            year = int(year_str)
            month = _SEASON_TO_MID_MONTH[season]
            oni = float(anom_str)
            records.append({"date": datetime(year, month, 1), "oni": oni})
        except (ValueError, IndexError):
            continue

    if not records:
        raise RuntimeError("Failed to parse ONI data from NOAA")

    df = pd.DataFrame(records).set_index("date").sort_index()
    df.index = pd.to_datetime(df.index)

    if end is not None:
        df = df[df.index <= end]
    if start is not None:
        df = df[df.index >= start]

    return df


def fetch_all_controls(
    start: str,
    end: str | None = None,
) -> dict[str, pd.DataFrame]:
    """Fetch all control variables and cache to parquet."""
    if end is None:
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print("Fetching USD/BRL ...")
    usdbrl = fetch_usdbrl(start, end)

    print("Fetching Oil (CL=F) ...")
    oil = fetch_oil(start, end)

    print("Fetching ENSO (ONI) ...")
    enso = fetch_enso(start, end)

    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    usdbrl.to_parquet(DATA_PROCESSED_DIR / "usdbrl.parquet")
    oil.to_parquet(DATA_PROCESSED_DIR / "oil.parquet")
    enso.to_parquet(DATA_PROCESSED_DIR / "enso.parquet")
    print("Saved controls to processed/")

    return {"usdbrl": usdbrl, "oil": oil, "enso": enso}


def load_cached_controls() -> dict[str, pd.DataFrame | None]:
    result = {}
    for name in ["usdbrl", "oil", "enso"]:
        path = DATA_PROCESSED_DIR / f"{name}.parquet"
        if path.exists():
            result[name] = pd.read_parquet(path)
        else:
            result[name] = None
    return result