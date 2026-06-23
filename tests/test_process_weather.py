import pandas as pd
import pytest

from src.data.process_weather import (
    compute_anomalies,
    compute_climatology,
    compute_rolling_stats,
)


@pytest.fixture
def sample_weather():
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    meso_keys = ["31_10", "31_05"]
    records = []
    for mk in meso_keys:
        for i, d in enumerate(dates):
            records.append({
                "meso_key": mk,
                "date": d,
                "temp_max": 25.0 + (i % 10),
                "temp_min": 15.0,
                "temp_mean": 20.0,
                "precipitation": 2.0 if (i % 5 == 0) else 0.0,
                "evapotranspiration": 4.0,
            })
    df = pd.DataFrame(records).set_index(["meso_key", "date"]).sort_index()
    return df


def test_compute_climatology_returns_all_meso_months(sample_weather):
    clim = compute_climatology(sample_weather)
    assert "meso_key" in clim.columns
    assert "month" in clim.columns
    assert "temp_max_mean" in clim.columns
    assert "temp_max_std" in clim.columns
    assert len(clim) == 4


def test_compute_anomalies_adds_anom_columns(sample_weather):
    clim = compute_climatology(sample_weather)
    anom = compute_anomalies(sample_weather, climatology=clim)
    assert "temp_max_anom" in anom.columns
    assert "precipitation_anom" in anom.columns
    assert "temp_mean_anom" in anom.columns


def test_compute_anomalies_mean_anom_near_zero(sample_weather):
    clim = compute_climatology(sample_weather)
    anom = compute_anomalies(sample_weather, climatology=clim)
    mean_anom = anom["temp_max_anom"].mean()
    assert abs(mean_anom) < 1.0


def test_compute_rolling_stats_adds_columns(sample_weather):
    rolled = compute_rolling_stats(sample_weather, window=10)
    assert "precip_roll10_sum" in rolled.columns
    assert "temp_max_roll10_mean" in rolled.columns


def test_compute_rolling_stats_first_n_rows_nan(sample_weather):
    rolled = compute_rolling_stats(sample_weather, window=10)
    first_meso = rolled.loc["31_10"]
    assert pd.isna(first_meso["precip_roll10_sum"].iloc[0])
    assert not pd.isna(first_meso["precip_roll10_sum"].iloc[15])