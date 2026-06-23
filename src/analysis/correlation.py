"""Cross-correlation and Granger causality between weather anomalies and coffee prices."""

import pandas as pd
import numpy as np

from src.config import DATA_PROCESSED_DIR, MESOREGIONS
from src.data.merge_data import load_combined


def compute_ccf(
    x: pd.Series,
    y: pd.Series,
    max_lag: int = 180,
) -> pd.DataFrame:
    """Compute cross-correlation between x and y at lags 0..max_lag.

    Positive lag = x leads y (x_t influences y_{t+lag}).
    """
    x = x.dropna()
    y = y.dropna()
    common = x.index.intersection(y.index)
    x, y = x[common], y[common]

    results = []
    for lag in range(max_lag + 1):
        if lag == 0:
            corr = x.corr(y)
        else:
            y_shifted = y.shift(-lag)
            min_len = min(len(x), len(y_shifted.dropna()))
            corr = x.iloc[:min_len].corr(y_shifted.iloc[:min_len])
        results.append({"lag": lag, "correlation": corr if not pd.isna(corr) else 0})
    return pd.DataFrame(results)


def run_correlation(max_lag: int = 180) -> dict[str, pd.DataFrame]:
    """Run cross-correlation for key mesoregions and print Granger test results."""
    print("Loading combined data ...")
    combined = load_combined()
    if combined is None:
        return {}

    # Compute daily returns
    returns = combined["Close"].pct_change().dropna()

    meso_keys = sorted(MESOREGIONS.keys())
    results: dict[str, pd.DataFrame] = {}

    print(f"\n=== Cross-Correlation: Weather Anomalies vs Coffee Returns ===\n")
    print(f"{'Mesoregion':>35} | {'Peak lag':>8} | {'Peak corr':>9} | {'90d corr':>8}")
    print("-" * 70)

    for meso_key in meso_keys:
        temp_col = f"{meso_key}_temp_max_anom"
        precip_col = f"{meso_key}_precipitation_anom"

        if temp_col not in combined.columns:
            continue

        temp_corr = compute_ccf(combined[temp_col], returns, max_lag)
        precip_corr = compute_ccf(combined[precip_col] if precip_col in combined.columns else combined[temp_col], returns, max_lag)

        peak_idx = temp_corr["correlation"].abs().idxmax()
        peak_lag = temp_corr.loc[peak_idx, "lag"]
        peak_corr = temp_corr.loc[peak_idx, "correlation"]
        corr_90 = temp_corr.loc[temp_corr["lag"] == 90, "correlation"].values[0]

        name = MESOREGIONS[meso_key]["meso_name"][:30]
        print(f"  {name:>35} | {peak_lag:>4}d | {peak_corr:>+7.3f} | {corr_90:>+7.3f}")

        results[meso_key] = temp_corr

    # Granger causality on top mesos
    print(f"\n=== Granger Causality Test (lag=5 days) ===\n")
    print(f"{'Mesoregion':>35} | {'F-stat':>8} | {'p-value':>8} | {'Significant?':>12}")
    print("-" * 70)

    top_mesos = ["31_10", "31_05", "31_12", "35_02", "32_04", "29_06"]
    try:
        from statsmodels.tsa.stattools import grangercausalitytests
        for meso_key in top_mesos:
            temp_col = f"{meso_key}_temp_max_anom"
            if temp_col not in combined.columns:
                continue

            test_data = pd.concat([combined[temp_col], returns], axis=1).dropna()
            test_data.columns = ["weather", "returns"]

            try:
                gc_result = grangercausalitytests(test_data, maxlag=5, verbose=False)
                f_stat = gc_result[5][0]["ssr_ftest"][0]
                p_val = gc_result[5][0]["ssr_ftest"][1]
                sig = "***" if p_val < 0.01 else "**" if p_val < 0.05 else "*" if p_val < 0.1 else "n.s."
                name = MESOREGIONS[meso_key]["meso_name"][:30]
                print(f"  {name:>35} | {f_stat:>7.2f} | {p_val:>7.4f} | {sig:>12}")
            except Exception as e:
                print(f"  {meso_key:>35} | ERROR: {e}")
    except ImportError:
        print("  (statsmodels not installed. Install with: pip install statsmodels)")

    return results