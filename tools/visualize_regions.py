"""Generate an interactive world map showing region bounding boxes overlaid on the
Natural Earth land mask, plus weather data from parquet files for the latest
available date.

Usage:  python tools/visualize_regions.py
Output: tools/region_map.html (opens automatically in browser)
"""

import sys
import webbrowser
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import DATA_RAW_DIR, REGIONS
from src.data.fetch_weather import _load_land_mask

REGION_COLORS = {
    "brazil": "#7cb342",
    "vietnam": "#c0ca33",
    "colombia": "#f4511e",
    "indonesia": "#fb8c00",
    "ethiopia": "#43a047",
}

fig = go.Figure()

# ---- Land mask overlay (transparent) ----
land = _load_land_mask()


def _flatten_geometry(geom):
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, (MultiPolygon, GeometryCollection)):
        polys = []
        for g in geom.geoms:
            polys.extend(_flatten_geometry(g))
        return polys
    return []


for poly in _flatten_geometry(land):
    coords = list(poly.exterior.coords)
    lons, lats = zip(*coords)
    fig.add_trace(
        go.Scattergeo(
            lon=lons,
            lat=lats,
            mode="lines",
            fill="toself",
            fillcolor="rgba(107,143,107,0.12)",
            line=dict(width=0),
            name="Land mask",
            showlegend=False,
            hoverinfo="skip",
        )
    )

# ---- Region bounding boxes ----
for key, r in REGIONS.items():
    lon = [r["lon_min"], r["lon_max"], r["lon_max"], r["lon_min"], r["lon_min"]]
    lat = [r["lat_min"], r["lat_min"], r["lat_max"], r["lat_max"], r["lat_min"]]
    share = r["production_share"]
    label = f"{r['country']}<br>{r['region_name']}<br>{share:.0%} of global production"

    fig.add_trace(
        go.Scattergeo(
            lon=lon,
            lat=lat,
            mode="lines",
            line=dict(width=2.5, color=REGION_COLORS.get(key, "#888")),
            name=label,
            hovertemplate="%{text}<extra></extra>",
            text=[label],
        )
    )

# ---- Weather data markers (latest common date) ----
weather_labels = []
center_lons = []
center_lats = []
temp_means = []
hover_texts = []

for key in REGIONS:
    path = Path(DATA_RAW_DIR) / f"weather_{key}.parquet"
    if not path.exists():
        continue

    df = pd.read_parquet(path)
    if df.empty:
        continue

    latest = df.iloc[-1]
    center = REGIONS[key]
    c_lat = (center["lat_min"] + center["lat_max"]) / 2
    c_lon = (center["lon_min"] + center["lon_max"]) / 2

    hover = (
        f"<b>{center['country']}</b><br>"
        f"Date: {latest.name:%Y-%m-%d}<br>"
        f"Temp max: {latest.get('temp_max', np.nan):.1f}°C<br>"
        f"Temp mean: {latest.get('temp_mean', np.nan):.1f}°C<br>"
        f"Temp min: {latest.get('temp_min', np.nan):.1f}°C<br>"
        f"Precipitation: {latest.get('precipitation', np.nan):.1f} mm<br>"
        f"Evapotranspiration: {latest.get('evapotranspiration', np.nan):.2f} mm"
    )

    center_lons.append(c_lon)
    center_lats.append(c_lat)
    temp_means.append(latest.get("temp_mean", np.nan))
    weather_labels.append(center["country"])
    hover_texts.append(hover)

if temp_means:
    fig.add_trace(
        go.Scattergeo(
            lon=center_lons,
            lat=center_lats,
            mode="markers+text",
            marker=dict(
                size=28,
                color=temp_means,
                colorscale="RdYlBu_r",
                showscale=True,
                colorbar=dict(
                    title="Temp mean (°C)",
                    x=1.02,
                    len=0.5,
                ),
                line=dict(width=2, color="#4a3728"),
                symbol="circle",
            ),
            text=weather_labels,
            textposition="bottom center",
            textfont=dict(size=11, color="#4a3728", family="Segoe UI, sans-serif"),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_texts,
            name="Weather (latest)",
        )
    )

fig.update_layout(
    title=(
        "Coffee Producing Regions — Land Mask & Latest Weather Data<br>"
        "<sup>Bubbles coloured by mean temperature. Hover for all variables.</sup>"
    ),
    geo=dict(
        showland=False,
        showocean=True,
        oceancolor="#e8f0f8",
        showcountries=True,
        countrycolor="#d5c8b5",
        countrywidth=0.3,
        projection_type="natural earth",
        showframe=False,
    ),
    margin=dict(l=10, r=10, t=60, b=10),
    paper_bgcolor="#faf6f0",
    font=dict(color="#4a3728", family="Segoe UI, sans-serif"),
)

output = Path(__file__).resolve().parent / "region_map.html"
fig.write_html(str(output))
print(f"Map saved: {output}")

webbrowser.open(str(output))