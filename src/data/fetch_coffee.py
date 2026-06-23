"""Fetch daily coffee futures data from Yahoo Finance via yfinance."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.config import COFFEE_PARQUET, DEFAULT_START_DATE, TICKER_COFFEE


def load_cached(path: str = COFFEE_PARQUET) -> pd.DataFrame | None:
    try:
        df = pd.read_parquet(path).sort_index()
        df.index = pd.to_datetime(df.index)
        return df
    except FileNotFoundError:
        return None


def fetch_coffee(
    start: str = DEFAULT_START_DATE,
    end: str | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    """Load coffee futures data from PostgreSQL, cached parquet, or download fresh."""
    try:
        from src.database.repositories.prices import get_prices_in_range, save_prices
        db_available = True
    except Exception:
        db_available = False
        save_prices = None

    if not refresh and db_available:
        try:
            result = get_prices_in_range(start, end or datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            if not result.empty:
                return result
        except Exception:
            cached = load_cached()
            if cached is not None:
                return cached
    elif not refresh:
        cached = load_cached()
        if cached is not None:
            return cached

    import yfinance as yf

    if end is None:
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    df = yf.download(TICKER_COFFEE, start=start, end=end, progress=False)

    if df.empty:
        cached = load_cached()
        if cached is not None:
            return cached
        raise RuntimeError("Download failed and no cache exists")

    df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)

    if db_available:
        try:
            save_prices(df)
            return df.sort_index()
        except Exception:
            pass

    Path(COFFEE_PARQUET).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(COFFEE_PARQUET)

    return df.sort_index()
