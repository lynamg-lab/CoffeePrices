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
    meso_id_str = gdf["meso_id"].astype(str).str[-2:].str.zfill(2)
    gdf["meso_key"] = (
        gdf["state_geocode"].astype(str).str.zfill(2) + "_" + meso_id_str
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
            "production_pct": "% of national production",
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


def mesoregion_boundaries() -> list:
    """Return a filled Choroplethmapbox trace and an outline Scattermapbox trace.

    Mesoregion boundaries are created by dissolving municipality polygons
    on meso_key, producing a unified boundary per mesoregion.
    """
    gdf = load_production_geojson()
    gdf["geometry"] = gdf["geometry"].buffer(0)
    meso_gdf = gdf.dissolve(by="meso_key", aggfunc="sum").reset_index()

    meso_gdf = meso_gdf[meso_gdf["meso_key"].isin(MESOREGIONS)].copy()

    geojson = gpd.GeoSeries(meso_gdf.geometry).__geo_interface__

    fill_trace = go.Choroplethmapbox(
        geojson=geojson,
        locations=meso_gdf.index,
        z=[1] * len(meso_gdf),
        colorscale=[[0, "rgba(144,238,144,0.15)"], [1, "rgba(144,238,144,0.15)"]],
        showscale=False,
        hoverinfo="skip",
        marker_line_width=0,
    )

    lons = []
    lats = []
    for geom in meso_gdf.geometry:
        if geom.geom_type == "MultiPolygon":
            coords = [list(p.exterior.coords) for p in geom.geoms]
        else:
            coords = [list(geom.exterior.coords)]
        for ring in coords:
            lons.append([c[0] for c in ring] + [None])
            lats.append([c[1] for c in ring] + [None])

    lons_flat = [x for sub in lons for x in sub]
    lats_flat = [x for sub in lats for x in sub]

    outline_trace = go.Scattermapbox(
        lon=lons_flat,
        lat=lats_flat,
        mode="lines",
        line=dict(color="rgba(144,238,144,0.7)", width=2),
        hoverinfo="skip",
        showlegend=False,
        name="Mesoregion boundaries",
    )

    return [fill_trace, outline_trace]


def municipality_count_table() -> go.Figure:
    """Plotly table of mesoregions with unique ERA5 grid cells and production stats."""
    gdf = load_production_geojson()
    gdf = gdf.to_crs(gdf.estimate_utm_crs())
    gdf["centroid"] = gdf.geometry.centroid
    gdf = gdf.to_crs("EPSG:4326")
    gdf["era5_lat"] = (gdf["centroid"].y * 4).round() / 4
    gdf["era5_lon"] = (gdf["centroid"].x * 4).round() / 4
    gdf["era5_cell"] = gdf["era5_lat"].astype(str) + "_" + gdf["era5_lon"].astype(str)

    stats = (
        gdf.groupby("meso_key")
        .agg(
            era5_cells=("era5_cell", "nunique"),
            production_tonnes=("production_of_arabica_coffee_tonnes_2018", "sum"),
        )
        .reset_index()
    )
    total_production = stats["production_tonnes"].sum()
    stats["pct"] = stats["production_tonnes"] / total_production * 100

    stats["meso_name"] = stats["meso_key"].map(
        {k: v["meso_name"] for k, v in MESOREGIONS.items()}
    )
    stats["state"] = stats["meso_key"].map(
        {k: v["state_name"].title() for k, v in MESOREGIONS.items()}
    )

    stats = stats.dropna(subset=["meso_name"]).sort_values(
        "production_tonnes", ascending=False
    )

    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=[
                        "Mesoregion",
                        "State",
                        "Open-Meteo points",
                        "Production (t)",
                        "% of national",
                    ],
                    fill_color="#4a3728",
                    font=dict(color="#faf6f0", size=13),
                    align="left",
                    height=32,
                ),
                cells=dict(
                    values=[
                        stats["meso_name"],
                        stats["state"],
                        stats["era5_cells"],
                        stats["production_tonnes"].apply(lambda x: f"{x:,.0f}"),
                        stats["pct"].apply(lambda x: f"{x:.1f}%"),
                    ],
                    fill_color=[
                        ["#f0ebe3" if i % 2 == 0 else "#faf6f0" for i in range(len(stats))]
                    ]
                    * 5,
                    font=dict(color="#4a3728", size=12),
                    align="left",
                    height=28,
                ),
            )
        ]
    )
    fig.update_layout(
        title="Mesoregion Weather Aggregation: Unique ERA5 0.25° Grid Cells per Mesoregion",
        height=min(40 + 28 * len(stats), 700),
        margin={"r": 10, "t": 40, "l": 10, "b": 10},
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