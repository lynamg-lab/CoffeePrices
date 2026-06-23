"""Process raw mesoregion weather: climatology, anomalies, rolling statistics."""

import pandas as pd

from src.config import DATA_PROCESSED_DIR


def load_weather() -> pd.DataFrame:
    return pd.read_parquet(DATA_PROCESSED_DIR / "weather_mesoregion_daily.parquet")


def compute_climatology(
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Compute monthly mean and std for each mesoregion from available data.

    Returns a DataFrame with MultiIndex (meso_key, month) and columns
    for each variable's mean and std, e.g. temp_max_mean, temp_max_std.
    """
    if df is None:
        df = load_weather()

    df = df.reset_index()
    df["month"] = df["date"].dt.month

    climatology = df.groupby(["meso_key", "month"]).agg(["mean", "std"])
    climatology.columns = [f"{var}_{stat}" for var, stat in climatology.columns]
    climatology = climatology.reset_index()

    out_path = DATA_PROCESSED_DIR / "climatology.parquet"
    climatology.to_parquet(out_path)
    print(f"Saved climatology ({len(climatology)} meso-month records) to {out_path}")
    return climatology


def compute_anomalies(
    df: pd.DataFrame | None = None,
    climatology: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Compute daily weather anomalies (deviation from monthly mean).

    Returns the input DataFrame with additional _anom columns for each variable.
    """
    if df is None:
        df = load_weather()
    if climatology is None:
        climatology = load_climatology()

    df = df.reset_index()
    df["month"] = df["date"].dt.month

    merged = df.merge(
        climatology,
        on=["meso_key", "month"],
        how="left",
    )

    for var in ["temp_max", "temp_min", "temp_mean", "precipitation", "evapotranspiration"]:
        mean_col = f"{var}_mean"
        anom_col = f"{var}_anom"
        merged[anom_col] = merged[var] - merged[mean_col]

    merged = merged.set_index(["meso_key", "date"]).sort_index()
    cols_to_drop = [c for c in merged.columns if c.endswith(("_mean", "_std")) and c != "month"]
    merged = merged.drop(columns=cols_to_drop, errors="ignore")

    out_path = DATA_PROCESSED_DIR / "weather_anomalies.parquet"
    merged.to_parquet(out_path)
    print(f"Saved anomalies ({len(merged)} records) to {out_path}")
    return merged


def compute_rolling_stats(
    df: pd.DataFrame | None = None,
    window: int = 30,
) -> pd.DataFrame:
    """Compute rolling statistics: 30-day precip sum, temp max/min.

    Returns the input DataFrame with additional _roll{N}_{stat} columns.
    """
    if df is None:
        df = load_weather()

    groups = df.groupby("meso_key")
    roll = groups[["temp_max", "temp_min", "temp_mean", "precipitation"]].rolling(window)

    result = df.copy()
    result[f"precip_roll{window}_sum"] = groups["precipitation"].transform(
        lambda x: x.rolling(window, min_periods=window).sum()
    )
    result[f"temp_max_roll{window}_mean"] = groups["temp_max"].transform(
        lambda x: x.rolling(window, min_periods=window).mean()
    )
    result[f"temp_min_roll{window}_mean"] = groups["temp_min"].transform(
        lambda x: x.rolling(window, min_periods=window).mean()
    )

    out_path = DATA_PROCESSED_DIR / "weather_rolling.parquet"
    result.to_parquet(out_path)
    print(f"Saved rolling stats ({len(result)} records) to {out_path}")
    return result


def load_climatology() -> pd.DataFrame:
    path = DATA_PROCESSED_DIR / "climatology.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return compute_climatology()


def process_all() -> pd.DataFrame:
    """Run full pipeline: climatology → anomalies → rolling stats."""
    print("Computing climatology ...")
    clim = compute_climatology()

    print("Computing anomalies ...")
    anom = compute_anomalies(climatology=clim)

    print("Computing rolling stats ...")
    rolled = compute_rolling_stats()

    # Merge all into one big processed dataset
    merged = anom.merge(
        rolled.drop(columns=[c for c in rolled.columns if c in anom.columns], errors="ignore"),
        left_index=True,
        right_index=True,
    )

    out_path = DATA_PROCESSED_DIR / "weather_processed.parquet"
    merged.to_parquet(out_path)
    print(f"Saved full processed weather ({len(merged)} records, {len(merged.columns)} cols) to {out_path}")
    return merged