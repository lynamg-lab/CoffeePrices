"""Event study: measure coffee price response around weather shock events.

For each shock event, computes the Cumulative Abnormal Return (CAR)
from 30 days before to 90 days after the event, relative to a pre-event trend.
"""

import pandas as pd
import numpy as np
from scipy import stats

from src.config import DATA_PROCESSED_DIR
from src.data.merge_data import load_combined


def load_events() -> pd.DataFrame:
    path = DATA_PROCESSED_DIR / "shock_events.parquet"
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


def compute_car(
    prices: pd.Series,
    event_start: pd.Timestamp,
    pre_window: int = 30,
    post_window: int = 90,
) -> pd.Series | None:
    """Compute Cumulative Abnormal Return around an event date.

    Abnormal return = actual return - expected return (pre-event trend).
    CAR = cumulative sum of abnormal returns from event_start to event_start+post_window.
    """
    pre_end = event_start - pd.Timedelta(days=1)
    pre_start = event_start - pd.Timedelta(days=pre_window)

    pre_prices = prices[pre_start:pre_end]
    post_prices = prices[event_start: event_start + pd.Timedelta(days=post_window)]

    if len(pre_prices) < 5 or len(post_prices) < 5:
        return None

    # Fit linear trend on pre-event window
    x_pre = np.arange(len(pre_prices))
    slope, intercept = np.polyfit(x_pre, pre_prices.values, 1)

    # Expected prices in post window
    x_post = np.arange(len(pre_prices), len(pre_prices) + len(post_prices))
    expected = slope * x_post + intercept

    # Abnormal returns and CAR
    abnormal = post_prices.values - expected
    car = np.cumsum(abnormal / expected)
    return pd.Series(car, index=post_prices.index)


def run_event_study(
    pre_window: int = 30,
    post_window: int = 90,
) -> pd.DataFrame:
    """Run the full event study and print results."""
    print("Loading data ...")
    combined = load_combined()
    events = load_events()

    if combined is None or events.empty:
        print("No data available.")
        return pd.DataFrame()

    prices = combined["Close"]

    print(f"Running event study: {len(events)} events ...")
    results = []
    for _, event in events.iterrows():
        event_date = pd.Timestamp(event["start_date"])
        car_series = compute_car(prices, event_date, pre_window, post_window)
        if car_series is None:
            continue

        # CAR at key horizons
        for horizon, label in [(10, "10d"), (30, "30d"), (60, "60d"), (90, "90d")]:
            price_at_horizon = prices.asof(event_date + pd.Timedelta(days=horizon))
            if price_at_horizon is None or pd.isna(price_at_horizon):
                continue
            base_price = prices.asof(event_date - pd.Timedelta(days=1))
            if base_price is None or pd.isna(base_price) or base_price == 0:
                continue
            car_pct = (price_at_horizon - base_price) / base_price * 100

            results.append({
                "meso_key": event["meso_key"],
                "meso_name": event.get("meso_name", ""),
                "state_name": event.get("state_name", ""),
                "event_type": event["event_type"],
                "event_date": event_date,
                "horizon": label,
                "horizon_days": horizon,
                "car_pct": car_pct,
                "severity": event.get("severity", 0),
                "production_tonnes": event.get("production_tonnes_2018", 0),
            })

    car_df = pd.DataFrame(results)
    if car_df.empty:
        print("No valid CAR results.")
        return car_df

    out_path = DATA_PROCESSED_DIR / "event_study_results.parquet"
    car_df.to_parquet(out_path, index=False)
    print(f"Saved {len(car_df)} CAR records to {out_path}")

    # Print summary
    print(f"\n=== Event Study Summary ===\n")
    for etype in ["heatwave", "drought", "compound"]:
        subset = car_df[car_df["event_type"] == etype]
        if subset.empty:
            continue
        print(f"  {etype.upper()}:")
        for horizon in ["10d", "30d", "60d", "90d"]:
            h = subset[subset["horizon"] == horizon]["car_pct"]
            if h.empty:
                continue
            mean_car = h.mean()
            t_stat, p_val = stats.ttest_1samp(h, 0)
            sig = "***" if p_val < 0.01 else "**" if p_val < 0.05 else "*" if p_val < 0.1 else ""
            print(f"    {horizon:>4}: mean CAR = {mean_car:+.2f}%  "
                  f"(t={t_stat:.2f}, p={p_val:.4f}){sig}")

    # By production weight
    print(f"\n  CAR by production quartile (90-day):")
    q90 = car_df[car_df["horizon"] == "90d"].copy()
    if not q90.empty:
        q90["weight_quartile"] = pd.qcut(q90["production_tonnes"], 4, labels=["Q1(small)", "Q2", "Q3", "Q4(large)"])
        for q, grp in q90.groupby("weight_quartile", observed=True):
            print(f"    {q}: mean CAR = {grp['car_pct'].mean():+.2f}% ({len(grp)} events)")

    return car_df