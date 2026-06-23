import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.config import DATA_PROCESSED_DIR, MESOREGIONS, PLOTLY_TEMPLATE
from src.data.merge_data import load_combined


def _apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(template=PLOTLY_TEMPLATE)
    return fig


def _run_ols_capture(y, x, name=""):
    import statsmodels.api as sm
    y, x = y.align(x, join="inner", axis=0)
    combo = pd.concat([y, x], axis=1).dropna()
    y = combo.iloc[:, 0]
    x = combo.iloc[:, 1:]
    x = sm.add_constant(x)
    model = sm.OLS(y, x.astype(float))
    results = model.fit(cov_type="HAC", cov_kwds={"maxlags": 10})
    return {
        "name": name,
        "rsquared": results.rsquared,
        "rsquared_adj": results.rsquared_adj,
        "nobs": int(results.nobs),
        "fvalue": results.fvalue,
        "f_pvalue": results.f_pvalue,
        "params": results.params.to_dict(),
        "bse": results.bse.to_dict(),
        "pvalues": results.pvalues.to_dict(),
        "tvalues": results.tvalues.to_dict(),
    }


def run_all_models() -> list[dict]:
    combined = load_combined()
    if combined is None:
        return []
    returns = combined["Close"].pct_change().dropna()
    top_mesos = ["31_10", "31_05", "31_12", "35_02", "32_04", "29_06"]

    results = []

    x1 = pd.DataFrame()
    x1["anom_temp_31_10"] = combined["31_10_temp_max_anom"]
    x1["anom_precip_31_10"] = combined["31_10_precipitation_anom"]
    results.append(_run_ols_capture(returns, x1, "Model 1: Sul de Minas only"))

    x2 = pd.DataFrame()
    for mk in ["31_10", "31_05", "31_12"]:
        x2[f"anom_temp_{mk}"] = combined[f"{mk}_temp_max_anom"]
        x2[f"anom_precip_{mk}"] = combined[f"{mk}_precipitation_anom"]
    results.append(_run_ols_capture(returns, x2, "Model 2: Top 3 MG mesos"))

    x3 = pd.DataFrame()
    for mk in top_mesos:
        x3[f"anom_temp_{mk}"] = combined[f"{mk}_temp_max_anom"]
        x3[f"anom_precip_{mk}"] = combined[f"{mk}_precipitation_anom"]
    results.append(_run_ols_capture(returns, x3, "Model 3: All 6 top mesos"))

    x4 = pd.DataFrame()
    for mk in ["31_10", "31_05", "31_12"]:
        x4[f"anom_temp_{mk}"] = combined[f"{mk}_temp_max_anom"]
    x4["usdbrl_ret"] = combined["usdbrl"].pct_change()
    x4["oil_ret"] = combined["oil"].pct_change()
    x4["oni"] = combined["oni"]
    results.append(_run_ols_capture(returns, x4, "Model 4: MG weather + controls"))

    x5 = pd.DataFrame()
    x5["anom_temp_31_10_t0"] = combined["31_10_temp_max_anom"]
    x5["anom_temp_31_10_t30"] = combined["31_10_temp_max_anom"].shift(30)
    x5["anom_temp_31_10_t60"] = combined["31_10_temp_max_anom"].shift(60)
    x5["usdbrl_ret"] = combined["usdbrl"].pct_change()
    x5["oil_ret"] = combined["oil"].pct_change()
    results.append(_run_ols_capture(returns, x5, "Model 5: Sul de Minas lags + controls"))

    return results


def coefficient_plot(model_results: dict, top_n: int = 15) -> go.Figure:
    params = model_results["params"]
    bse = model_results["bse"]
    pvals = model_results["pvalues"]
    names = list(params.keys())

    coeffs = []
    errors = []
    labels = []
    colors = []
    for n in names:
        if n == "const":
            continue
        coeffs.append(params[n])
        errors.append(1.96 * bse[n])
        labels.append(n)
        colors.append("#3d405b" if pvals[n] < 0.05 else "#c8b89a")

    if not coeffs:
        fig = go.Figure()
        return _apply_theme(fig)

    idx = np.argsort(np.abs(coeffs))[-top_n:]
    coeffs = [coeffs[i] for i in idx]
    errors = [errors[i] for i in idx]
    labels = [labels[i] for i in idx]
    colors = [colors[i] for i in idx]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=coeffs,
            y=labels,
            orientation="h",
            marker_color=colors,
            error_x=dict(type="data", array=errors, visible=True, color="#8b7355"),
            hovertemplate="%{y}: %{x:.4f} ± %{error_x.array[0]:.4f}<extra></extra>",
        )
    )
    fig.add_vline(x=0, line_dash="dash", line_color="grey", opacity=0.5)
    fig.update_layout(
        title=f"Regression Coefficients — {model_results['name']}",
        height=max(300, len(coeffs) * 25 + 80),
        xaxis_title="Coefficient (95% CI)",
        yaxis=dict(autorange="reversed"),
        margin={"r": 20, "t": 40, "l": 200, "b": 10},
    )
    return _apply_theme(fig)


def rsquared_comparison(model_results: list[dict]) -> go.Figure:
    names = [r["name"].split(": ")[1] if ": " in r["name"] else r["name"] for r in model_results]
    rsq = [r["rsquared"] for r in model_results]
    adj_rsq = [r["rsquared_adj"] for r in model_results]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=names,
            y=rsq,
            name="R²",
            marker_color="#8b7355",
            text=[f"{v:.3f}" for v in rsq],
            textposition="outside",
        )
    )
    fig.add_trace(
        go.Bar(
            x=names,
            y=adj_rsq,
            name="Adj R²",
            marker_color="#c8b89a",
            text=[f"{v:.3f}" for v in adj_rsq],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Model Comparison: R² and Adjusted R²",
        height=450,
        xaxis_title="Model",
        yaxis_title="R²",
        barmode="group",
        hovermode="x unified",
    )
    return _apply_theme(fig)


def actual_vs_predicted(model_results: dict) -> go.Figure:
    combined = load_combined()
    if combined is None:
        fig = go.Figure()
        return _apply_theme(fig)

    import statsmodels.api as sm
    returns = combined["Close"].pct_change().dropna()
    x = pd.DataFrame()
    for var in model_results["params"]:
        if var == "const":
            continue
        if var in combined.columns:
            x[var] = combined[var]
        elif var == "usdbrl_ret":
            x[var] = combined["usdbrl"].pct_change()
        elif var == "oil_ret":
            x[var] = combined["oil"].pct_change()
        elif var == "oni":
            x[var] = combined["oni"]
        elif var.startswith("anom_temp_"):
            mk = var.replace("anom_temp_", "").replace("_t0", "").replace("_t30", "").replace("_t60", "")
            base = var.replace("anom_temp_" + mk, "")
            col = f"{mk}_temp_max_anom"
            if col in combined.columns:
                shift = 0
                if "_t30" in var:
                    shift = 30
                elif "_t60" in var:
                    shift = 60
                x[var] = combined[col].shift(shift) if shift else combined[col]
        elif var.startswith("anom_precip_"):
            mk = var.replace("anom_precip_", "")
            col = f"{mk}_precipitation_anom"
            if col in combined.columns:
                x[var] = combined[col]

    y, x = returns.align(x, join="inner", axis=0)
    combo = pd.concat([y, x], axis=1).dropna()
    y = combo.iloc[:, 0]
    x = combo.iloc[:, 1:]
    x = sm.add_constant(x)
    model = sm.OLS(y, x.astype(float))
    results = model.fit()
    predicted = results.predict(x)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=predicted,
            y=y,
            mode="markers",
            marker=dict(color="#8b7355", size=3, opacity=0.4),
            name="Observations",
        )
    )
    lims = [min(predicted.min(), y.min()), max(predicted.max(), y.max())]
    fig.add_trace(
        go.Scatter(
            x=lims, y=lims,
            mode="lines",
            line=dict(color="#d4a373", width=2, dash="dash"),
            name="Perfect fit",
        )
    )
    fig.update_layout(
        title=f"Actual vs Predicted — {model_results['name']}",
        height=500,
        xaxis_title="Predicted Return",
        yaxis_title="Actual Return",
        hovermode="closest",
    )
    return _apply_theme(fig)