"""Generate an interactive world map showing:
  1. Natural Earth land mask (transparent overlay)
  2. Region bounding boxes
  3. Individual grid points colored by max temperature for the latest date

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
from src.data.fetch_weather import _generate_grid, _is_land, _fetch_point, _load_land_mask

REGION_COLORS = {
    "brazil": "#7cb342",
    "vietnam": "#c0ca33",
    "colombia": "#f4511e",
    "indonesia": "#fb8c00",
    "ethiopia": "#43a047",
}

fig = go.Figure()

# ---- Land mask overlay ----
land = _load_land_mask()


def _flatten(geom):
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, (MultiPolygon, GeometryCollection)):
        polys = []
        for g in geom.geoms:
            polys.extend(_flatten(g))
        return polys
    return []


for poly in _flatten(land):
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

# ---- Grid points coloured by temp_max (latest date) ----
grid_lons: list[float] = []
grid_lats: list[float] = []
grid_temps: list[float] = []
grid_hover: list[str] = []

for key, r in REGIONS.items():
    parquet_path = Path(DATA_RAW_DIR) / f"weather_{key}.parquet"
    if not parquet_path.exists():
        continue

    region_df = pd.read_parquet(parquet_path)
    if region_df.empty:
        continue

    latest_date = region_df.index[-1]
    date_str = latest_date.strftime("%Y-%m-%d")

    grid = _generate_grid(r["lat_min"], r["lat_max"], r["lon_min"], r["lon_max"], 1.0)
    grid = [(lat, lon) for lat, lon in grid if _is_land(lat, lon)]

    for lat, lon in grid:
        pt_df = _fetch_point(lat, lon, date_str, date_str)
        if pt_df is None or pt_df.empty:
            continue
        row = pt_df.iloc[0]
        temp = row.get("temp_max")
        if temp is None or np.isnan(temp):
            continue

        grid_lons.append(lon)
        grid_lats.append(lat)
        grid_temps.append(temp)
        grid_hover.append(
            f"<b>{r['country']}</b><br>"
            f"Lat: {lat:.2f}, Lon: {lon:.2f}<br>"
            f"Date: {date_str}<br>"
            f"Temp max: {temp:.1f}°C"
        )

if grid_temps:
    fig.add_trace(
        go.Scattergeo(
            lon=grid_lons,
            lat=grid_lats,
            mode="markers",
            marker=dict(
                size=10,
                color=grid_temps,
                colorscale="RdYlBu_r",
                showscale=True,
                colorbar=dict(
                    title="Max temp (°C)",
                    x=1.02,
                    len=0.6,
                ),
                line=dict(width=0.5, color="rgba(74,55,40,0.3)"),
                symbol="circle",
            ),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=grid_hover,
            name="Grid points (temp_max)",
        )
    )

fig.update_layout(
    title="Coffee Producing Regions — Gridded Max Temperature (latest date)",
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
    margin=dict(l=10, r=10, t=50, b=10),
    paper_bgcolor="#faf6f0",
    font=dict(color="#4a3728", family="Segoe UI, sans-serif"),
)

output = Path(__file__).resolve().parent / "region_map.html"
fig.write_html(str(output))
print(f"Map saved: {output}")

webbrowser.open(str(output))