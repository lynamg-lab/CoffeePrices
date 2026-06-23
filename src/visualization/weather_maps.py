import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.config import DATA_PROCESSED_DIR, MESOREGIONS, PLOTLY_TEMPLATE


def _apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(template=PLOTLY_TEMPLATE)
    return fig


def load_anomalies() -> pd.DataFrame:
    return pd.read_parquet(DATA_PROCESSED_DIR / "weather_anomalies.parquet")


def anomaly_heatmap(variable: str = "temp_max_anom") -> go.Figure:
    df = load_anomalies().reset_index()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    pivot = df.pivot_table(
        index="meso_key", columns="month", values=variable, aggfunc="mean"
    )
    meso_labels = []
    for k in pivot.index:
        m = MESOREGIONS.get(k, {})
        short = m.get("meso_name", k)[:25]
        meso_labels.append(f"{short} ({k})")
    z = pivot.values.copy()
    z_mean = np.nanmean(z)
    z -= z_mean

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=pivot.columns.tolist(),
            y=meso_labels,
            colorscale="RdBu_r",
            zmid=0,
            colorbar_title="Anomaly (dev from mean)",
            hovertemplate="Meso: %{y}<br>Month: %{x}<br>Anomaly: %{z:.2f}°C<extra></extra>",
        )
    )
    fig.update_layout(
        title=f"Weather Anomaly Heatmap — {variable}",
        height=700,
        xaxis=dict(tickangle=-45, nticks=20),
        margin={"r": 20, "t": 40, "l": 10, "b": 80},
    )
    return _apply_theme(fig)


def shock_timeline() -> go.Figure:
    events = pd.read_parquet(DATA_PROCESSED_DIR / "shock_events.parquet")
    type_colors = {"heatwave": "#d4a373", "drought": "#e07a5f", "compound": "#3d405b"}
    type_symbols = {"heatwave": "circle", "drought": "square", "compound": "diamond"}

    fig = go.Figure()
    for etype, color in type_colors.items():
        subset = events[events["event_type"] == etype]
        if subset.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=pd.to_datetime(subset["start_date"]),
                y=subset["meso_name"],
                mode="markers",
                name=etype.title(),
                marker=dict(
                    color=color,
                    symbol=type_symbols[etype],
                    size=8,
                    line=dict(width=0.5, color="white"),
                ),
                hovertemplate="%{x|%Y-%m-%d}<br>%{y}<br>%{customdata[0]} days<br>Severity: %{customdata[1]:.2f}<extra></extra>",
                customdata=subset[["duration_days", "severity"]].values,
            )
        )
    fig.update_layout(
        title="Weather Shock Events by Mesoregion",
        height=600,
        hovermode="closest",
        margin={"r": 20, "t": 40, "l": 10, "b": 10},
    )
    fig.update_xaxes(title_text="Date")
    return _apply_theme(fig)


def seasonal_climate_profile(meso_key: str = "31_10") -> go.Figure:
    df = load_anomalies().reset_index()
    meso_data = df[df["meso_key"] == meso_key].copy()
    if meso_data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data for this mesoregion", showarrow=False)
        return _apply_theme(fig)

    meso_data["month_num"] = pd.to_datetime(meso_data["date"]).dt.month
    monthly = meso_data.groupby("month_num").agg(
        temp_mean=("temp_max", "mean"),
        temp_std=("temp_max", "std"),
        precip_mean=("precipitation", "mean"),
        precip_std=("precipitation", "std"),
    ).reset_index()
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.08,
                        subplot_titles=("Temperature", "Precipitation"))

    fig.add_trace(
        go.Scatter(
            x=month_labels,
            y=monthly["temp_mean"],
            error_y=dict(type="data", array=monthly["temp_std"], visible=True),
            mode="lines+markers",
            name="Max Temp",
            line=dict(color="#d4a373", width=2),
            marker=dict(size=6),
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Bar(
            x=month_labels,
            y=monthly["precip_mean"],
            name="Precipitation",
            marker_color="#8fbc8f",
            error_y=dict(type="data", array=monthly["precip_std"], visible=True),
        ),
        row=2, col=1,
    )

    meso_name = MESOREGIONS.get(meso_key, {}).get("meso_name", meso_key)
    fig.update_layout(
        title=f"Seasonal Climate — {meso_name} ({meso_key})",
        height=550,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1)
    fig.update_yaxes(title_text="Precipitation (mm)", row=2, col=1)
    return _apply_theme(fig)