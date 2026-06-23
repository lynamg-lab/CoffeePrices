import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.config import (
    DATA_RAW_DIR,
    PRODUCTION_COLORSCALE,
    MESOREGIONS,
    PLOTLY_TEMPLATE,
    COLOR_CLOSE_LINE,
    COLOR_GRID,
)


def _apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(template=PLOTLY_TEMPLATE)
    return fig


def load_production_geojson() -> gpd.GeoDataFrame:
    path = DATA_RAW_DIR / "coffee_producing_municipalities.geojson"
    gdf = gpd.read_file(path)
    gdf["meso_key"] = (
        gdf["state_geocode"].astype(str).str.zfill(2)
        + "_"
        + gdf["meso_id"].astype(str).str.zfill(2)
    )
    return gdf


def municipality_choropleth() -> go.Figure:
    gdf = load_production_geojson()
    total = gdf["production_of_arabica_coffee_tonnes_2018"].sum()
    gdf_pct = gdf.copy()
    gdf_pct["production_pct"] = (
        gdf["production_of_arabica_coffee_tonnes_2018"] / total * 100
    )

    fig = px.choropleth_mapbox(
        gdf_pct,
        geojson=gdf_pct.geometry,
        locations=gdf_pct.index,
        color="production_pct",
        color_continuous_scale=PRODUCTION_COLORSCALE,
        mapbox_style="carto-positron",
        center={"lat": -16.5, "lon": -47.0},
        zoom=4.5,
        opacity=0.8,
        hover_data={
            "municipality_name": True,
            "state_name": True,
            "meso_name": True,
            "production_of_arabica_coffee_tonnes_2018": True,
            "production_pct": ":.2f",
        },
        labels={
            "production_pct": "Share of national (%)",
            "municipality_name": "Municipality",
            "meso_name": "Mesoregion",
            "production_of_arabica_coffee_tonnes_2018": "Production (tonnes)",
        },
    )
    fig.update_layout(
        title="Arabica Coffee Production by Municipality (2018)",
        height=700,
        margin={"r": 10, "t": 40, "l": 10, "b": 10},
    )
    return _apply_theme(fig)


def mesoregion_bar_chart(top_n: int = 20) -> go.Figure:
    mesos = sorted(
        MESOREGIONS.values(),
        key=lambda m: m["production_tonnes_2018"],
        reverse=True,
    )[:top_n]
    names = [m["meso_name"] + " (" + m["state_name"].title() + ")" for m in mesos]
    tonnes = [m["production_tonnes_2018"] / 1000 for m in mesos]
    colors = [
        "#4a3728" if t >= 200 else "#8b7355" if t >= 50 else "#c8b89a"
        for t in tonnes
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=tonnes,
            y=names,
            orientation="h",
            marker_color=colors,
            text=[f"{t:.1f}k" for t in tonnes],
            textposition="outside",
        )
    )
    fig.update_layout(
        title=f"Top {top_n} Coffee-Producing Mesoregions (2018)",
        height=600,
        xaxis_title="Production (thousand tonnes)",
        yaxis=dict(autorange="reversed"),
        margin={"r": 60, "t": 40, "l": 10, "b": 10},
    )
    return _apply_theme(fig)


def production_by_state_pie() -> go.Figure:
    state_totals: dict[str, float] = {}
    for m in MESOREGIONS.values():
        state = m["state_name"].title()
        state_totals[state] = state_totals.get(state, 0) + m["production_tonnes_2018"]

    labels = list(state_totals.keys())
    values = list(state_totals.values())
    colors = ["#4a3728", "#6b5740", "#8b7355", "#a89070", "#c8b89a"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(colors=colors),
                textinfo="label+percent",
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        title="Arabica Production by State (2018)",
        height=500,
        showlegend=False,
    )
    return _apply_theme(fig)