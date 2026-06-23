from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import yfinance as yf

from src.config import COFFEE_PARQUET, DEFAULT_START_DATE
from src.data.fetch_coffee import fetch_coffee, load_cached


def test_load_cached_returns_none_when_file_missing():
    result = load_cached(str(Path("nonexistent.parquet")))
    assert result is None


def test_load_cached_returns_dataframe(tmp_path):
    df = pd.DataFrame({"Close": [100.0], "Volume": [1000]},
                      index=pd.to_datetime(["2024-01-02"]))
    path = tmp_path / "test.parquet"
    df.to_parquet(path)
    result = load_cached(str(path))
    assert result is not None
    assert "Close" in result.columns


@patch("yfinance.download")
def test_fetch_coffee_downloads_fresh(mock_download):
    dates = pd.date_range("2024-01-02", periods=3, freq="B")
    mock_df = pd.DataFrame({
        ("Close", "KC=F"): [150.0, 151.0, 152.0],
        ("Volume", "KC=F"): [1000, 1100, 1200],
        ("Open", "KC=F"): [149.0, 150.0, 151.0],
        ("High", "KC=F"): [151.0, 152.0, 153.0],
        ("Low", "KC=F"): [148.0, 149.0, 150.0],
    }, index=dates)
    mock_df.columns = pd.MultiIndex.from_tuples(mock_df.columns)
    mock_download.return_value = mock_df

    result = fetch_coffee(start="2024-01-01", end="2024-01-05", refresh=True)
    assert result is not None
    assert "Close" in result.columns
    assert len(result) == 3


@patch("yfinance.download")
def test_fetch_coffee_falls_back_to_cache_on_empty(mock_download):
    mock_download.return_value = pd.DataFrame()
    result = fetch_coffee(start="2099-01-01", end="2099-01-05", refresh=True)
    assert result is not None
    assert "Close" in result.columns


def test_fetch_coffee_returns_valid_columns():
    df = fetch_coffee(start=DEFAULT_START_DATE)
    assert df is not None
    required = {"Close", "Volume", "Open", "High", "Low"}
    assert required.issubset(set(df.columns))
    assert df.index.dtype.kind == "M"


def test_fetch_coffee_date_range():
    df = fetch_coffee(start="2024-01-01", end="2024-03-01")
    if len(df) > 0:
        assert df.index.max() <= pd.Timestamp("2024-03-01")