"""Run quality checks on the full data pipeline and produce a text report + charts.

Usage:  python tools/quality_check_report.py
Output: Console report + PNG charts in reports/figures/quality/
"""

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import DATA_PROCESSED_DIR, MESOREGIONS


# ---- Helpers ----

RESULTS = {"PASS": 0, "WARN": 0, "FAIL": 0}


def check(label: str, condition: bool, fail_type: str = "FAIL"):
    status = fail_type if not condition else "PASS"
    RESULTS[status] += 1
    print(f"  [{status}] {label}")


def warn(label: str, condition: bool):
    check(label, condition, "WARN")


# ---- 1. Climate Plausibility ----

def check_climate_plausibility(weather: pd.DataFrame):
    print("\n--- 1. Climate Plausibility ---")
    check("temp_max: all values in 0-45C range",
          (weather["temp_max"] >= 0).all() and (weather["temp_max"] <= 45).all())
    check("temp_min: all values in -5-30C range",
          (weather["temp_min"] >= -5).all() and (weather["temp_min"] <= 30).all())
    check("precipitation: no negative values",
          (weather["precipitation"] >= 0).all())
    warn("precipitation: no values > 300mm/day",
         (weather["precipitation"] <= 300).all())
    check("evapotranspiration: no negative values",
          (weather["evapotranspiration"] >= 0).all())


# ---- 2. Geographic Consistency ----

def check_geographic(weather: pd.DataFrame):
    print("\n--- 2. Geographic Consistency ---")
    means = weather.groupby("meso_key")["temp_max"].mean()

    check("Triangulo Mineiro (31_05) > Sul de Minas (31_10)",
          means.get("31_05", 0) > means.get("31_10", 0))
    check("Sul ES (32_04) > Central ES (32_03)",
          means.get("32_04", 0) > means.get("32_03", 0))
    check("Centro Sul BA (29_06) > Norte Pioneiro PR (41_04)",
          means.get("29_06", 0) > means.get("41_04", 0))

    print("\n  Mean temp_max by mesoregion (sorted hottest first):")
    for meso_key in means.sort_values(ascending=False).index:
        m = MESOREGIONS[meso_key]
        print(f"    {meso_key} {m['meso_name']:>35} {m['state_name']:>15}: "
              f"{means[meso_key]:.1f}C")


# ---- 3. Temporal Consistency ----

def check_temporal(weather: pd.DataFrame, combined: pd.DataFrame):
    print("\n--- 3. Temporal Consistency ---")
    df = weather.reset_index().set_index("date")

    max_dod = df.groupby("meso_key")["temp_max"].diff().abs().max()
    warn("No daily temp_max jump > 15C in any meso", max_dod.max() <= 15)

    roll_cols = [c for c in combined.columns if "roll30" in c]
    if roll_cols:
        nan_count = combined[roll_cols[0]].isna().sum()
        warn(f"Rolling 30-day NaN count: {nan_count} (first ~20 trading days expected)",
             nan_count <= 25)

    check("No duplicate date rows in combined panel",
          combined.index.is_unique)


# ---- 4. Anomaly Distributions ----

def check_anomalies(weather: pd.DataFrame):
    print("\n--- 4. Anomaly Distributions ---")
    for var, label, tol in [("temp_max", "temp_max", 0.5),
                             ("temp_min", "temp_min", 0.5),
                             ("precipitation", "precipitation", 0.5),
                             ("evapotranspiration", "evapotranspiration", 0.5)]:
        anom_col = f"{var}_anom"
        if anom_col not in weather.columns:
            continue
        means = weather.groupby("meso_key")[anom_col].mean()
        max_abs = means.abs().max()
        check(f"|{label} anomaly mean| < {tol}C/mm for all mesos (max={max_abs:.2f})",
              max_abs < tol)

    anom_cols = [c for c in weather.columns if c.endswith("_anom")]
    all_anoms = pd.concat([weather[c] for c in anom_cols])
    mu = all_anoms.mean()
    sd = all_anoms.std()
    print(f"  Overall anomaly distribution: mean={mu:.2f}, std={sd:.2f}")
    check("Overall anomaly mean near zero (|mean| < 0.1)", abs(mu) < 0.1)


# ---- 5. Coffee + Controls Range ----

def check_coffee_controls(combined: pd.DataFrame):
    print("\n--- 5. Coffee + Controls Range ---")
    if "Close" in combined.columns:
        c_min = combined["Close"].min()
        c_max = combined["Close"].max()
        check(f"KC=F close: {c_min:.1f}-{c_max:.1f} ct/lb (expected 80-500)",
              80 < c_min < c_max < 500)
        check("Close always > 0", (combined["Close"] > 0).all())
        warn("Volume always > 0 (some days may have zero)",
              (combined["Volume"] > 0).all())

    if "usdbrl" in combined.columns:
        u_min = combined["usdbrl"].min()
        u_max = combined["usdbrl"].max()
        check(f"USD/BRL: {u_min:.2f}-{u_max:.2f} (expected 4-6)",
              4 < u_min < u_max < 7)

    if "oil" in combined.columns:
        o_min = combined["oil"].min()
        o_max = combined["oil"].max()
        check(f"Oil: {o_min:.1f}-{o_max:.1f} $/bbl (expected -40 to 150)",
              -40 < o_min < o_max < 150)

    if "oni" in combined.columns:
        oni_min = combined["oni"].min()
        oni_max = combined["oni"].max()
        check(f"ONI: {oni_min:.2f}-{oni_max:.2f} (expected -3 to +3)",
              -4 < oni_min and oni_max < 4)


# ---- 6. Merge Integrity ----

def check_merge(combined: pd.DataFrame, weather: pd.DataFrame):
    print("\n--- 6. Merge Integrity ---")
    weather_dates = set(weather.reset_index()["date"].dt.date.unique())
    combo_dates = set(combined.index.date)
    overlap = len(combo_dates & weather_dates) / len(combo_dates) * 100
    check(f"Coffee/weather date overlap: {overlap:.1f}%", overlap > 90)

    if "usdbrl" in combined.columns:
        non_na = combined["usdbrl"].notna().sum()
        check(f"usdbrl: {non_na}/{len(combined)} non-null", non_na > len(combined) * 0.9)


# ---- Charts ----

def save_charts(weather: pd.DataFrame, combined: pd.DataFrame):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  WARNING: matplotlib not installed. Skipping chart export.")
        return

    out_dir = Path("reports") / "figures" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(weather["temp_max"], bins=50, color="#8b7355", alpha=0.7, edgecolor="none")
    ax.set_title("Distribution of Daily Max Temperature (all mesos)")
    ax.set_xlabel("Temp max (C)")
    fig.tight_layout()
    fig.savefig(out_dir / "01_temp_max_histogram.png", dpi=150)
    plt.close(fig)

    means = weather.groupby("meso_key")["temp_max"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.barh(range(len(means)), means.values, color="#8b7355", height=0.7)
    ax.set_yticks(range(len(means)))
    labels = [f"{k} {MESOREGIONS[k]['meso_name'][:20]}" for k in means.index]
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("Mean temp_max (C)")
    ax.set_title("Mean Max Temperature by Mesoregion")
    fig.tight_layout()
    fig.savefig(out_dir / "02_mean_temp_by_meso.png", dpi=150)
    plt.close(fig)

    sul = weather[weather.index.get_level_values("meso_key") == "31_10"].copy()
    sul = sul.reset_index().set_index("date")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    ax1.plot(sul.index, sul["temp_max"], color="#c08080", linewidth=0.5)
    ax1.set_ylabel("Temp max (C)")
    ax1.set_title("Sul/Sudoeste de Minas - Raw Temperature")
    ax2.plot(sul.index, sul["temp_max_anom"], color="#8b7355", linewidth=0.5)
    ax2.axhline(0, color="grey", linewidth=0.5)
    ax2.set_ylabel("Anomaly (C)")
    ax2.set_title("Sul/Sudoeste de Minas - Temperature Anomaly")
    fig.tight_layout()
    fig.savefig(out_dir / "03_sul_minas_timeseries.png", dpi=150)
    plt.close(fig)

    # 4. Separate anomaly histograms per variable
    anom_vars = {
        "temp_max": "Temperature Max Anomaly (C)",
        "temp_min": "Temperature Min Anomaly (C)",
        "temp_mean": "Temperature Mean Anomaly (C)",
        "precipitation": "Precipitation Anomaly (mm)",
        "evapotranspiration": "Evapotranspiration Anomaly (mm)",
    }
    for var, label in anom_vars.items():
        col = f"{var}_anom"
        if col not in weather.columns:
            continue
        data = weather[col].dropna()
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.hist(data, bins=80, color="#8b7355", alpha=0.7, edgecolor="none")
        ax.axvline(0, color="red", linewidth=1, linestyle="--")
        ax.set_title(f"Distribution of {label}")
        ax.set_xlabel(label)
        fig.tight_layout()
        fig.savefig(out_dir / f"04_anomaly_{var}_hist.png", dpi=150)
        plt.close(fig)

    if "Close" in combined.columns:
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(combined.index, combined["Close"], color="#4a3728", linewidth=1)
        ax.set_title("ICE Arabica Coffee Futures (KC=F)")
        ax.set_ylabel("ct/lb")
        fig.tight_layout()
        fig.savefig(out_dir / "05_coffee_price.png", dpi=150)
        plt.close(fig)

    if "usdbrl" in combined.columns:
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(combined.index, combined["usdbrl"], color="#8b7355", linewidth=1)
        ax.set_ylabel("USD/BRL", color="#8b7355")
        ax.set_title("USD/BRL Exchange Rate")
        fig.tight_layout()
        fig.savefig(out_dir / "06_usdbrl.png", dpi=150)
        plt.close(fig)

    print(f"  Charts saved to {out_dir}/")


def main():
    print("=" * 60)
    print("Data Pipeline Quality Check Report")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    weather_path = DATA_PROCESSED_DIR / "weather_processed.parquet"
    combined_path = DATA_PROCESSED_DIR / "combined_daily.parquet"

    if not weather_path.exists():
        print(f"\nERROR: {weather_path} not found. Run process_weather.py first.")
        sys.exit(1)
    if not combined_path.exists():
        print(f"\nERROR: {combined_path} not found. Run merge_data.py first.")
        sys.exit(1)

    weather = pd.read_parquet(weather_path)
    combined = pd.read_parquet(combined_path)

    print(f"\nData loaded:")
    print(f"  Weather: {len(weather)} records")
    print(f"  Combined: {len(combined)} days, {len(combined.columns)} columns")

    check_climate_plausibility(weather)
    check_geographic(weather)
    check_temporal(weather, combined)
    check_anomalies(weather)
    check_coffee_controls(combined)
    check_merge(combined, weather)

    print(f"\n--- Summary ---")
    total = sum(RESULTS.values())
    print(f"  PASS: {RESULTS['PASS']}/{total}")
    print(f"  WARN: {RESULTS['WARN']}/{total}")
    print(f"  FAIL: {RESULTS['FAIL']}/{total}")
    verdict = "DATA IS USABLE" if RESULTS["FAIL"] == 0 else "REVIEW FAILURES"
    print(f"  Verdict: {verdict}")

    save_charts(weather, combined)
    print("\nDone.")


if __name__ == "__main__":
    main()