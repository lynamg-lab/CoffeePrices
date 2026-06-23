"""Detect heatwave, drought, and compound shock events per mesoregion.

Heatwave:  temp_max_anom > P90 threshold for >= 5 consecutive days
Drought:   30-day rolling precipitation < P10 threshold
Compound:  heatwave + drought overlapping

Events saved to processed/shock_events.parquet.
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    DATA_PROCESSED_DIR,
    DROUGHT_PERCENTILE,
    DROUGHT_WINDOW_DAYS,
    HEATWAVE_MIN_DAYS,
    HEATWAVE_PERCENTILE,
    MESOREGIONS,
)


def load_weather() -> pd.DataFrame:
    return pd.read_parquet(DATA_PROCESSED_DIR / "weather_processed.parquet")


def compute_thresholds(
    df: pd.DataFrame,
    heat_pct: int = HEATWAVE_PERCENTILE,
    drought_pct: int = DROUGHT_PERCENTILE,
) -> dict[str, dict[str, float]]:
    """Compute per-mesoregion shock thresholds from anomaly distributions."""
    thresholds: dict[str, dict[str, float]] = {}
    for meso_key in df.index.get_level_values("meso_key").unique():
        meso_data = df.loc[meso_key]
        thresholds[meso_key] = {
            "heatwave": meso_data["temp_max_anom"].quantile(heat_pct / 100),
            "drought": meso_data["precip_roll30_sum"].quantile(drought_pct / 100),
        }
    return thresholds


def detect_heatwaves(df: pd.DataFrame, thresholds: dict) -> list[dict]:
    """Find heatwave events: temp_max_anom above threshold for >= N consecutive days."""
    events = []
    for meso_key in df.index.get_level_values("meso_key").unique():
        meso_data = df.loc[meso_key].sort_index()
        thresh = thresholds[meso_key]["heatwave"]
        above = meso_data["temp_max_anom"] > thresh

        # Find contiguous runs
        runs = []
        current_start = None
        for date_idx, is_hot in above.items():
            if is_hot and current_start is None:
                current_start = date_idx
            elif not is_hot and current_start is not None:
                runs.append((current_start, date_idx))
                current_start = None
        if current_start is not None:
            runs.append((current_start, above.index[-1]))

        for start, end in runs:
            duration = (end - start).days
            if duration >= HEATWAVE_MIN_DAYS:
                window = meso_data.loc[start:end]
                events.append({
                    "meso_key": meso_key,
                    "start_date": start,
                    "end_date": end - pd.Timedelta(days=1),
                    "duration_days": duration,
                    "event_type": "heatwave",
                    "severity": window["temp_max_anom"].mean(),
                    "peak_anomaly": window["temp_max_anom"].max(),
                })
    return events


def detect_droughts(df: pd.DataFrame, thresholds: dict) -> list[dict]:
    """Find drought events: 30-day rolling precip below threshold."""
    events = []
    for meso_key in df.index.get_level_values("meso_key").unique():
        meso_data = df.loc[meso_key].sort_index()
        col = f"precip_roll{DROUGHT_WINDOW_DAYS}_sum"
        if col not in meso_data.columns:
            continue
        thresh = thresholds[meso_key]["drought"]
        below = meso_data[col] < thresh

        runs = []
        current_start = None
        for date_idx, is_dry in below.items():
            if is_dry and current_start is None:
                current_start = date_idx
            elif not is_dry and current_start is not None:
                runs.append((current_start, date_idx))
                current_start = None
        if current_start is not None:
            runs.append((current_start, below.index[-1]))

        for start, end in runs:
            duration = (end - start).days
            window = meso_data.loc[start:end]
            events.append({
                "meso_key": meso_key,
                "start_date": start,
                "end_date": end - pd.Timedelta(days=1),
                "duration_days": duration,
                "event_type": "drought",
                "severity": -window[col].mean(),
                "peak_anomaly": -window[col].min(),
            })
    return events


def find_compound(heatwaves: list[dict], droughts: list[dict]) -> list[dict]:
    """Find compound events: overlapping heatwave and drought in same mesoregion."""
    compounds = []
    for hw in heatwaves:
        for dr in droughts:
            if hw["meso_key"] != dr["meso_key"]:
                continue
            hw_range = pd.date_range(hw["start_date"], hw["end_date"])
            dr_range = pd.date_range(dr["start_date"], dr["end_date"])
            overlap = max(0, (min(hw["end_date"], dr["end_date"]) - max(hw["start_date"], dr["start_date"])).days + 1)
            if overlap > 0:
                compounds.append({
                    "meso_key": hw["meso_key"],
                    "start_date": max(hw["start_date"], dr["start_date"]),
                    "end_date": min(hw["end_date"], dr["end_date"]),
                    "duration_days": overlap,
                    "event_type": "compound",
                    "severity": (hw["severity"] + dr["severity"]) / 2,
                    "peak_anomaly": max(hw["peak_anomaly"], dr["peak_anomaly"]),
                })
    return compounds


def detect_all() -> pd.DataFrame:
    """Run full detection pipeline, save events, and print summary."""
    print("Loading weather data ...")
    df = load_weather()

    print("Computing thresholds ...")
    thresholds = compute_thresholds(df)

    print("Detecting heatwaves ...")
    heatwaves = detect_heatwaves(df, thresholds)

    print("Detecting droughts ...")
    droughts = detect_droughts(df, thresholds)

    print("Finding compound events ...")
    compounds = find_compound(heatwaves, droughts)

    all_events = pd.DataFrame(heatwaves + droughts + compounds)
    if all_events.empty:
        print("No events detected.")
        return all_events

    all_events = all_events.sort_values(["meso_key", "start_date"]).reset_index(drop=True)

    # Attach meso metadata
    all_events["state_name"] = all_events["meso_key"].map(
        lambda k: MESOREGIONS[k]["state_name"] if k in MESOREGIONS else ""
    )
    all_events["meso_name"] = all_events["meso_key"].map(
        lambda k: MESOREGIONS[k]["meso_name"] if k in MESOREGIONS else ""
    )
    all_events["production_tonnes_2018"] = all_events["meso_key"].map(
        lambda k: MESOREGIONS[k]["production_tonnes_2018"] if k in MESOREGIONS else 0
    )

    out_path = DATA_PROCESSED_DIR / "shock_events.parquet"
    all_events.to_parquet(out_path, index=False)
    print(f"\nSaved {len(all_events)} events to {out_path}")

    print(f"\n=== Shock Event Summary ===")
    for etype in ["heatwave", "drought", "compound"]:
        subset = all_events[all_events["event_type"] == etype]
        print(f"\n  {etype.upper()}: {len(subset)} events")
        if not subset.empty:
            print(f"    Avg duration: {subset['duration_days'].mean():.1f} days")
            print(f"    Avg severity: {subset['severity'].mean():.2f}")
            print(f"    Top mesos: {subset['meso_key'].value_counts().head(5).to_dict()}")

    return all_events


def load_events() -> pd.DataFrame:
    path = DATA_PROCESSED_DIR / "shock_events.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return detect_all()