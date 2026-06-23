import numpy as np
import pandas as pd
import pytest

from src.analysis.event_study import compute_car


def test_compute_car_returns_series_with_correct_length():
    dates = pd.date_range("2024-01-01", periods=150, freq="D")
    prices = pd.Series(np.linspace(100, 110, 150), index=dates)
    event_start = pd.Timestamp("2024-02-15")
    result = compute_car(prices, event_start, pre_window=30, post_window=90)
    assert result is not None
    assert len(result) <= 91


def test_compute_car_positive_trend_gives_positive_car():
    dates = pd.date_range("2024-01-01", periods=150, freq="D")
    prices = pd.Series(np.linspace(100, 110, 150), index=dates)
    event_start = pd.Timestamp("2024-02-15")
    result = compute_car(prices, event_start, pre_window=30, post_window=90)
    assert result is not None
    assert result.iloc[-1] > 0


def test_compute_car_negative_trend_gives_negative_car():
    dates = pd.date_range("2024-01-01", periods=150, freq="D")
    pre = np.linspace(105, 110, 46)
    post = np.linspace(100, 95, 105)
    prices = pd.Series(np.concatenate([pre, post[1:]]), index=dates)
    event_start = pd.Timestamp("2024-02-15")
    result = compute_car(prices, event_start, pre_window=30, post_window=90)
    assert result is not None
    assert result.iloc[-1] < 0


def test_compute_car_falling_post_prices_gives_negative_car():
    dates = pd.date_range("2024-01-01", periods=150, freq="D")
    pre = np.linspace(100, 105, 46)
    post = np.linspace(100, 85, 105)
    prices = pd.Series(np.concatenate([pre, post[1:]]), index=dates)
    event_start = pd.Timestamp("2024-02-15")
    result = compute_car(prices, event_start, pre_window=30, post_window=90)
    assert result is not None
    assert result.iloc[-1] < 0


def test_compute_car_returns_none_with_insufficient_pre_data():
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    prices = pd.Series(np.linspace(100, 105, 10), index=dates)
    event_start = pd.Timestamp("2024-01-05")
    result = compute_car(prices, event_start, pre_window=30, post_window=90)
    assert result is None


def test_compute_car_returns_none_with_insufficient_post_data():
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    prices = pd.Series(np.linspace(100, 105, 10), index=dates)
    event_start = pd.Timestamp("2024-01-01")
    result = compute_car(prices, event_start, pre_window=5, post_window=30)
    assert result is None


def test_compute_car_index_is_datetime():
    dates = pd.date_range("2024-01-01", periods=150, freq="D")
    prices = pd.Series(np.linspace(100, 110, 150), index=dates)
    event_start = pd.Timestamp("2024-02-15")
    result = compute_car(prices, event_start)
    assert result is not None
    assert result.index.dtype.kind == "M"


def test_compute_car_exact_linear_trend():
    dates = pd.date_range("2024-01-01", periods=150, freq="D")
    prices = pd.Series(100.0 + np.arange(150) * 0.1, index=dates)
    event_start = pd.Timestamp("2024-03-01")
    result = compute_car(prices, event_start, pre_window=30, post_window=60)
    assert result is not None
    assert abs(result.iloc[-1]) < 1.0