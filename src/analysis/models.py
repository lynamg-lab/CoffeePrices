"""Regression models: coffee price ~ weather anomalies + controls.

Runs OLS with Newey-West standard errors for multiple model specifications.
"""

import pandas as pd
import numpy as np

from src.config import DATA_PROCESSED_DIR, MESOREGIONS
from src.data.merge_data import load_combined


def _run_ols(y: pd.Series, x: pd.DataFrame, name: str = ""):
    """Run OLS with Newey-West standard errors and print results."""
    try:
        import statsmodels.api as sm
    except ImportError:
        print("  (statsmodels not installed)")
        return

    y, x = y.align(x, join="inner", axis=0)
    combo = pd.concat([y, x], axis=1).dropna()
    y = combo.iloc[:, 0]
    x = combo.iloc[:, 1:]
    x = sm.add_constant(x)

    model = sm.OLS(y, x.astype(float))
    results = model.fit(cov_type="HAC", cov_kwds={"maxlags": 10})

    print(f"\n--- {name} ---")
    print(f"  R-squared: {results.rsquared:.4f}")
    print(f"  Adj R-squared: {results.rsquared_adj:.4f}")
    print(f"  N: {int(results.nobs)}")
    print(f"  F-stat: {results.fvalue:.2f} (p={results.f_pvalue:.4f})")
    print(f"\n  {'Variable':>30} | {'Coeff':>8} | {'Std.Err':>8} | {'t-stat':>7} | {'p-value':>8} | {'Signif':>6}")
    print("  " + "-" * 75)
    for var, coeff in results.params.items():
        se = results.bse[var]
        t = results.tvalues[var]
        p = results.pvalues[var]
        sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else "n.s."
        print(f"  {var:>30} | {coeff:>+8.4f} | {se:>8.4f} | {t:>+7.2f} | {p:>8.4f} | {sig:>6}")


def run_models() -> None:
    """Run several model specifications on the combined dataset."""
    print("Loading data ...")
    combined = load_combined()
    if combined is None:
        print("No combined data found.")
        return

    # Daily coffee returns
    returns = combined["Close"].pct_change().dropna()

    # Top producing mesos for weather variables
    top_mesos = ["31_10", "31_05", "31_12", "35_02", "32_04", "29_06"]

    # ---- Model 1: Sul de Minas only ----
    x1 = pd.DataFrame()
    x1["anom_temp_31_10"] = combined[f"31_10_temp_max_anom"]
    x1["anom_precip_31_10"] = combined[f"31_10_precipitation_anom"]
    _run_ols(returns, x1, "Model 1: Sul de Minas only")

    # ---- Model 2: Top 3 MG mesos ----
    x2 = pd.DataFrame()
    for mk in ["31_10", "31_05", "31_12"]:
        x2[f"anom_temp_{mk}"] = combined[f"{mk}_temp_max_anom"]
        x2[f"anom_precip_{mk}"] = combined[f"{mk}_precipitation_anom"]
    _run_ols(returns, x2, "Model 2: Top 3 MG mesos")

    # ---- Model 3: All top mesos ----
    x3 = pd.DataFrame()
    for mk in top_mesos:
        x3[f"anom_temp_{mk}"] = combined[f"{mk}_temp_max_anom"]
        x3[f"anom_precip_{mk}"] = combined[f"{mk}_precipitation_anom"]
    _run_ols(returns, x3, "Model 3: All 6 top mesos")

    # ---- Model 4: Weather + controls ----
    x4 = pd.DataFrame()
    for mk in ["31_10", "31_05", "31_12"]:
        x4[f"anom_temp_{mk}"] = combined[f"{mk}_temp_max_anom"]
    x4["usdbrl_ret"] = combined["usdbrl"].pct_change()
    x4["oil_ret"] = combined["oil"].pct_change()
    x4["oni"] = combined["oni"]
    _run_ols(returns, x4, "Model 4: MG weather + controls")

    # ---- Model 5: Sul de Minas with lags ----
    x5 = pd.DataFrame()
    x5["anom_temp_31_10_t0"] = combined["31_10_temp_max_anom"]
    x5["anom_temp_31_10_t30"] = combined["31_10_temp_max_anom"].shift(30)
    x5["anom_temp_31_10_t60"] = combined["31_10_temp_max_anom"].shift(60)
    x5["usdbrl_ret"] = combined["usdbrl"].pct_change()
    x5["oil_ret"] = combined["oil"].pct_change()
    _run_ols(returns, x5, "Model 5: Sul de Minas with lags 0/30/60d + controls")

    print("\nDone.")