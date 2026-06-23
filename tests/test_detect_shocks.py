import pandas as pd
import pytest

from src.analysis.detect_shocks import (
    compute_thresholds,
    detect_heatwaves,
    detect_droughts,
    find_compound,
)


@pytest.fixture
def sample_weather():
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    meso_keys = ["31_10", "31_05"]
    records = []
    for mk in meso_keys:
        for i, d in enumerate(dates):
            records.append({
                "meso_key": mk,
                "date": d,
                "temp_max_anom": 5.0 if (i >= 5 and i <= 12) else 0.0,
                "precip_roll30_sum": 10.0 if (i >= 10 and i <= 20) else 50.0,
            })
    df = pd.DataFrame(records).set_index(["meso_key", "date"]).sort_index()
    return df


def test_compute_thresholds_returns_dict(sample_weather):
    thresholds = compute_thresholds(sample_weather, heat_pct=90, drought_pct=10)
    assert "31_10" in thresholds
    assert "31_05" in thresholds
    assert "heatwave" in thresholds["31_10"]
    assert "drought" in thresholds["31_10"]


def test_detect_heatwaves_finds_events(sample_weather):
    thresholds = compute_thresholds(sample_weather, heat_pct=50, drought_pct=10)
    events = detect_heatwaves(sample_weather, thresholds)
    assert len(events) > 0
    assert all(e["event_type"] == "heatwave" for e in events)
    for e in events:
        assert "meso_key" in e
        assert "start_date" in e
        assert e["duration_days"] >= 5


def test_detect_heatwaves_no_events_with_high_threshold():
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    records = []
    for d in dates:
        records.append({"meso_key": "31_10", "date": d,
                        "temp_max_anom": 0.5, "precip_roll30_sum": 50.0})
    df = pd.DataFrame(records).set_index(["meso_key", "date"]).sort_index()
    thresholds = compute_thresholds(df, heat_pct=99, drought_pct=10)
    events = detect_heatwaves(df, thresholds)
    assert len(events) == 0


def test_detect_droughts_finds_events(sample_weather):
    thresholds = compute_thresholds(sample_weather, heat_pct=80, drought_pct=50)
    events = detect_droughts(sample_weather, thresholds)
    assert len(events) > 0
    for e in events:
        assert e["event_type"] == "drought"


def test_find_compound_returns_overlapping_events():
    heatwaves = [
        {"meso_key": "31_10", "start_date": pd.Timestamp("2024-01-05"),
         "end_date": pd.Timestamp("2024-01-10"), "duration_days": 6,
         "event_type": "heatwave", "severity": 4.0, "peak_anomaly": 5.0},
    ]
    droughts = [
        {"meso_key": "31_10", "start_date": pd.Timestamp("2024-01-08"),
         "end_date": pd.Timestamp("2024-01-15"), "duration_days": 8,
         "event_type": "drought", "severity": 30.0, "peak_anomaly": 40.0},
    ]
    compounds = find_compound(heatwaves, droughts)
    assert len(compounds) == 1
    assert compounds[0]["event_type"] == "compound"
    assert compounds[0]["start_date"] == pd.Timestamp("2024-01-08")
    assert compounds[0]["duration_days"] == 3


def test_find_compound_no_overlap():
    heatwaves = [
        {"meso_key": "31_10", "start_date": pd.Timestamp("2024-01-01"),
         "end_date": pd.Timestamp("2024-01-05"), "duration_days": 5,
         "event_type": "heatwave", "severity": 4.0, "peak_anomaly": 5.0},
    ]
    droughts = [
        {"meso_key": "31_10", "start_date": pd.Timestamp("2024-02-01"),
         "end_date": pd.Timestamp("2024-02-05"), "duration_days": 5,
         "event_type": "drought", "severity": 30.0, "peak_anomaly": 40.0},
    ]
    compounds = find_compound(heatwaves, droughts)
    assert len(compounds) == 0


def test_find_compound_different_mesoregion_no_match():
    heatwaves = [
        {"meso_key": "31_10", "start_date": pd.Timestamp("2024-01-01"),
         "end_date": pd.Timestamp("2024-01-05"), "duration_days": 5,
         "event_type": "heatwave", "severity": 4.0, "peak_anomaly": 5.0},
    ]
    droughts = [
        {"meso_key": "31_05", "start_date": pd.Timestamp("2024-01-01"),
         "end_date": pd.Timestamp("2024-01-05"), "duration_days": 5,
         "event_type": "drought", "severity": 30.0, "peak_anomaly": 40.0},
    ]
    assert find_compound(heatwaves, droughts) == []


def test_detect_heatwaves_short_run_not_counted():
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    records = []
    for i, d in enumerate(dates):
        anom = 10.0 if i in (3, 4, 5) else 0.0
        records.append({"meso_key": "31_10", "date": d,
                        "temp_max_anom": anom, "precip_roll30_sum": 50.0})
    df = pd.DataFrame(records).set_index(["meso_key", "date"]).sort_index()
    thresholds = compute_thresholds(df, heat_pct=80, drought_pct=10)
    events = detect_heatwaves(df, thresholds)
    assert len(events) == 0