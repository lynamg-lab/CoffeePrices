"""Merge coffee futures, weather, and controls into a single daily analysis panel."""

from datetime import datetime, timezone

import pandas as pd

from src.config import DATA_PROCESSED_DIR, DEFAULT_START_DATE
from src.data.fetch_coffee import fetch_coffee
from src.data.fetch_controls import fetch_all_controls, load_cached_controls


def load_weather_processed() -> pd.DataFrame:
    path = DATA_PROCESSED_DIR / "weather_processed.parquet"
    if path.exists():
        return pd.read_parquet(path)
    raise FileNotFoundError("Run process_weather.process_all() first")


def pivot_weather(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot weather from long (meso_key, date) to wide (date, meso_key_var).

    Example: columns become 31_10_temp_max, 31_10_precipitation, etc.
    """
    df = df.reset_index()
    id_vars = ["date", "meso_key"]
    value_vars = [c for c in df.columns if c not in id_vars and c != "month"]
    pivoted = df.pivot_table(index="date", columns="meso_key", values=value_vars)
    pivoted.columns = [f"{k}_{v}" for v, k in pivoted.columns]
    pivoted.index = pd.to_datetime(pivoted.index)
    return pivoted.sort_index()


def merge_all(
    start: str = DEFAULT_START_DATE,
    end: str | None = None,
    refresh_controls: bool = False,
) -> pd.DataFrame:
    """Merge coffee futures + processed weather + controls into one daily panel.

    Returns a DataFrame indexed by date with columns:
    - Close, Volume (coffee)
    - {meso_key}_{var} ({41 mesos × ~10 weather columns})
    - usdbrl, oil, oni (controls)
    """
    if end is None:
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Coffee futures
    print("Loading coffee futures ...")
    coffee = fetch_coffee(start=start, end=end)
    coffee = coffee[["Close", "Volume"]]

    # Weather
    print("Loading processed weather ...")
    weather = load_weather_processed()
    weather_wide = pivot_weather(weather)
    # Filter date range
    weather_wide = weather_wide.loc[weather_wide.index >= pd.Timestamp(start)]
    weather_wide = weather_wide.loc[weather_wide.index <= pd.Timestamp(end)]

    # Controls
    if refresh_controls:
        controls = fetch_all_controls(start, end)
    else:
        controls = load_cached_controls()
        missing = [k for k, v in controls.items() if v is None]
        if missing:
            print(f"Fetching missing controls: {missing}")
            controls.update(fetch_all_controls(start, end))
    usdbrl = controls.get("usdbrl")
    oil = controls.get("oil")
    enso = controls.get("enso")

    # Merge: start with coffee, add weather, then controls
    result = coffee.copy()

    # Weather (forward-fill for non-trading days)
    weather_aligned = weather_wide.reindex(result.index, method="ffill")
    result = result.join(weather_aligned)

    # Controls
    if usdbrl is not None:
        usdbrl_aligned = usdbrl.reindex(result.index, method="ffill")
        result = result.join(usdbrl_aligned)
    if oil is not None:
        oil_aligned = oil.reindex(result.index, method="ffill")
        result = result.join(oil_aligned)
    if enso is not None:
        enso_aligned = enso.reindex(result.index, method="ffill")
        result = result.join(enso_aligned)
        # Forward-fill ENSO from monthly to daily
        result["oni"] = result["oni"].ffill()

    result.index = pd.to_datetime(result.index)
    result.index.name = "date"

    out_path = DATA_PROCESSED_DIR / "combined_daily.parquet"
    result.to_parquet(out_path)
    print(f"Saved combined daily panel: {result.shape[0]} days × {result.shape[1]} columns to {out_path}")
    print(f"  Coffee columns: Close, Volume")
    print(f"  Weather columns: {len([c for c in result.columns if '_temp' in c or '_precip' in c or '_evap' in c or '_anom' in c or '_roll' in c])}")
    print(f"  Control columns: {[c for c in result.columns if c in ['usdbrl', 'oil', 'oni']]}")

    return result


def load_combined() -> pd.DataFrame | None:
    path = DATA_PROCESSED_DIR / "combined_daily.parquet"
    if path.exists():
        df = pd.read_parquet(path)
        df.index = pd.to_datetime(df.index)
        return df
    return None