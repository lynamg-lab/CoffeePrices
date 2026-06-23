import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from src.config import DATA_PROCESSED_DIR, MESOREGIONS, PLOTLY_TEMPLATE
from src.data.merge_data import load_combined


def _apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(template=PLOTLY_TEMPLATE)
    return fig


def _load_combined_and_car():
    combined = load_combined()
    car = pd.read_parquet(DATA_PROCESSED_DIR / "event_study_results.parquet")
    return combined, car


def car_by_event_type() -> go.Figure:
    _, car = _load_combined_and_car()
    horizons = ["10d", "30d", "60d", "90d"]
    colors = {"heatwave": "#d4a373", "drought": "#e07a5f", "compound": "#3d405b"}

    fig = go.Figure()
    for etype, color in colors.items():
        subset = car[car["event_type"] == etype]
        means = [subset[subset["horizon"] == h]["car_pct"].mean() for h in horizons]
        sems = [
            subset[subset["horizon"] == h]["car_pct"].sem()
            for h in horizons
        ]
        fig.add_trace(
            go.Scatter(
                x=horizons,
                y=means,
                error_y=dict(type="data", array=sems, visible=True),
                mode="lines+markers",
                name=etype.title(),
                line=dict(color=color, width=2.5),
                marker=dict(size=8),
            )
        )

    fig.add_hline(y=0, line_dash="dash", line_color="grey", opacity=0.5)
    fig.update_layout(
        title="Cumulative Abnormal Return by Event Type",
        height=500,
        xaxis_title="Horizon",
        yaxis_title="CAR (%)",
        hovermode="x unified",
    )
    return _apply_theme(fig)


def car_by_production_quartile() -> go.Figure:
    _, car = _load_combined_and_car()
    q90 = car[car["horizon"] == "90d"].copy()
    if q90.empty:
        fig = go.Figure()
        return _apply_theme(fig)

    q90["quartile"] = pd.qcut(
        q90["production_tonnes"], 4,
        labels=["Q1 (Smallest)", "Q2", "Q3", "Q4 (Largest)"]
    )
    summary = q90.groupby("quartile", observed=True).agg(
        mean_car=("car_pct", "mean"),
        sem_car=("car_pct", "sem"),
        count=("car_pct", "count"),
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=summary["quartile"],
            y=summary["mean_car"],
            error_y=dict(type="data", array=summary["sem_car"], visible=True),
            marker_color=["#c8b89a", "#a89070", "#8b7355", "#4a3728"],
            text=[f"{v:.1f}%" for v in summary["mean_car"]],
            textposition="outside",
            hovertemplate="%{x}<br>Mean CAR: %{y:.2f}%<br>N events: %{customdata}<extra></extra>",
            customdata=summary["count"],
        )
    )
    fig.update_layout(
        title="90-Day CAR by Production Quartile",
        height=450,
        xaxis_title="Production Weight Quartile",
        yaxis_title="Mean CAR (%)",
    )
    return _apply_theme(fig)


def lag_correlation_heatmap(max_lag: int = 90) -> go.Figure:
    combined, _ = _load_combined_and_car()
    returns = combined["Close"].pct_change().dropna()
    top_mesos = ["31_10", "31_05", "31_12", "35_02", "32_04", "29_06"]
    lags = list(range(0, max_lag + 1, 10))
    z = np.full((len(top_mesos), len(lags)), np.nan)

    for i, mk in enumerate(top_mesos):
        col = f"{mk}_temp_max_anom"
        if col not in combined.columns:
            continue
        x = combined[col].dropna()
        y = returns
        common = x.index.intersection(y.index)
        x, y = x[common], y[common]
        for j, lag in enumerate(lags):
            if lag == 0:
                z[i, j] = x.corr(y)
            else:
                y_shifted = y.shift(-lag)
                valid = y_shifted.notna()
                min_len = min(len(x[valid]), len(y_shifted[valid]))
                if min_len > 10:
                    z[i, j] = x[valid].iloc[:min_len].corr(y_shifted[valid].iloc[:min_len])
                else:
                    z[i, j] = 0

    labels = [MESOREGIONS.get(mk, {}).get("meso_name", mk)[:22] for mk in top_mesos]
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=[f"{l}d" for l in lags],
            y=labels,
            colorscale="RdBu_r",
            zmid=0,
            colorbar_title="Correlation",
            hovertemplate="Meso: %{y}<br>Lag: %{x}<br>Corr: %{z:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Cross-Correlation: Temp Anomaly vs Coffee Returns",
        height=400,
        width=700,
        xaxis_title="Lag (days)",
    )
    return _apply_theme(fig)


def granger_summary_table() -> go.Figure:
    combined, _ = _load_combined_and_car()
    returns = combined["Close"].pct_change().dropna()
    top_mesos = ["31_10", "31_05", "31_12", "35_02", "32_04", "29_06"]

    from statsmodels.tsa.stattools import grangercausalitytests

    rows = []
    for mk in top_mesos:
        col = f"{mk}_temp_max_anom"
        if col not in combined.columns:
            continue
        test_data = pd.concat([combined[col], returns], axis=1).dropna()
        test_data.columns = ["weather", "returns"]
        try:
            gc = grangercausalitytests(test_data, maxlag=5, verbose=False)
            f_stat = gc[5][0]["ssr_ftest"][0]
            p_val = gc[5][0]["ssr_ftest"][1]
            sig = (
                "***"
                if p_val < 0.01
                else "**" if p_val < 0.05
                else "*" if p_val < 0.1
                else "n.s."
            )
        except Exception:
            f_stat, p_val, sig = 0, 1, "n.s."
        name = MESOREGIONS.get(mk, {}).get("meso_name", mk)
        rows.append(dict(Mesoregion=name, F_stat=f"{f_stat:.2f}",
                         p_value=f"{p_val:.4f}", Significant=sig))

    df_table = pd.DataFrame(rows)
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=list(df_table.columns),
                    fill_color="#4a3728",
                    font=dict(color="white", size=12),
                    align="left",
                ),
                cells=dict(
                    values=[df_table[c] for c in df_table.columns],
                    fill_color=[["#faf6f0", "#f0ebe3"] * len(df_table)],
                    align="left",
                    font_size=11,
                ),
            )
        ]
    )
    fig.update_layout(
        title="Granger Causality: Weather Anomalies → Coffee Returns (lag=5)",
        height=300,
    )
    return _apply_theme(fig)