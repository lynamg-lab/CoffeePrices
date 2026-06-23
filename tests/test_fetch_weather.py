from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.data.fetch_weather import _fetch_point, COLUMN_MAP, load_cached_weather


@patch("src.data.fetch_weather.requests.get")
def test_fetch_point_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "daily": {
            "time": ["2024-01-01", "2024-01-02"],
            "temperature_2m_max": [30.0, 31.0],
            "precipitation_sum": [0.0, 5.0],
        }
    }
    mock_get.return_value = mock_resp

    result = _fetch_point(-21.6, -45.9, "2024-01-01", "2024-01-02")
    assert result is not None
    assert len(result) == 2
    assert "temp_max" in result.columns
    assert result["temp_max"].iloc[0] == 30.0


@patch("src.data.fetch_weather.requests.get")
def test_fetch_point_api_error(mock_get):
    mock_get.side_effect = Exception("Timeout")
    result = _fetch_point(0.0, 0.0, "2024-01-01", "2024-01-02")
    assert result is None


@patch("src.data.fetch_weather.requests.get")
def test_fetch_point_no_daily_key(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_get.return_value = mock_resp
    result = _fetch_point(0.0, 0.0, "2024-01-01", "2024-01-02")
    assert result is None


def test_column_map_has_all_variables():
    assert "temperature_2m_max" in COLUMN_MAP
    assert "temperature_2m_min" in COLUMN_MAP
    assert "temperature_2m_mean" in COLUMN_MAP
    assert "precipitation_sum" in COLUMN_MAP
    assert "et0_fao_evapotranspiration" in COLUMN_MAP
    assert COLUMN_MAP["temperature_2m_max"] == "temp_max"
    assert COLUMN_MAP["precipitation_sum"] == "precipitation"


def test_load_cached_weather_returns_none_if_missing():
    result = load_cached_weather()
    assert result is None or isinstance(result, pd.DataFrame)


@patch("src.data.fetch_weather.requests.get")
def test_fetch_point_partial_data(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "daily": {
            "time": ["2024-01-01"],
            "temperature_2m_max": [30.0],
        }
    }
    mock_get.return_value = mock_resp
    result = _fetch_point(-21.6, -45.9, "2024-01-01", "2024-01-01")
    assert result is not None
    assert "temp_max" in result.columns
    assert "precipitation" not in result.columns