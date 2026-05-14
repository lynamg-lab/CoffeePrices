"""Fetch daily coffee futures data from Yahoo Finance via yfinance."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

from src.config import (
    CACHE_MAX_AGE_SECONDS,
    COFFEE_PARQUET,
    DEFAULT_START_DATE,
    TICKER_COFFEE,
)


def _cache_path() -> Path:
    return Path(COFFEE_PARQUET)


def _cache_is_fresh() -> bool:
    path = _cache_path()
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age = (datetime.now(timezone.utc) - mtime).total_seconds()
    return age < CACHE_MAX_AGE_SECONDS


def fetch_coffee(start: str = DEFAULT_START_DATE, end: str | None = None) -> pd.DataFrame:
    """Download KC=F daily OHLCV from Yahoo Finance, caching to parquet.

    Returns a DataFrame with datetime index and columns:
    Open, High, Low, Close, Volume.
    """
    cache = _cache_path()
    now = datetime.now(timezone.utc)

    if end is None:
        end = now.strftime("%Y-%m-%d")

    if _cache_is_fresh():
        df = pd.read_parquet(cache).sort_index()
        last_cached = pd.Timestamp(df.index[-1]).tz_localize(timezone.utc)
        if last_cached >= now - timedelta(days=1):
            return df

    df = yf.download(TICKER_COFFEE, start=start, end=end, progress=False)

    if df.empty:
        if cache.exists():
            return pd.read_parquet(cache).sort_index()
        raise RuntimeError(f"Download failed for {TICKER_COFFEE} and no cache exists")

    df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)

    cache.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache)

    return df.sort_index()
