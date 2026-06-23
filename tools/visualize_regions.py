"""Generate an interactive map of Brazil's coffee-producing municipalities.

Color-coded by 2018 arabica production tonnage, with mesoregion labels.
Output: tools/region_map.html (opens automatically in browser)
"""

import sys
import webbrowser
from pathlib import Path

import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import MESOREGIONS, PRODUCING_GEOJSON

fig = go.Figure()

# Load producing municipalities
import json
with open(PRODUCING_GEOJSON, encoding="utf-8") as f:
    features = json.load(f)["features"]

# Plot each municipality as a polygon, colored by production
for feature in features:
    props = feature["properties"]
    production = props.get("production_of_arabica_coffee_tonnes_2018", 0) or 0
    meso_name = props.get("meso_name", "")
    mun_name = props.get("municipality_name", "")
    state = props.get("state_name", "")

    for polygon in feature["geometry"]["coordinates"]:
        for ring in polygon:
            lons, lats = zip(*ring)
            fig.add_trace(
                go.Scattergeo(
                    lon=lons,
                    lat=lats,
                    mode="lines",
                    fill="toself",
                    fillcolor=f"rgba(74,55,40,{min(production / 50000, 0.8)})",
                    line=dict(width=0.3, color="rgba(74,55,40,0.2)"),
                    name=mun_name,
                    showlegend=False,
                    hovertemplate=(
                        f"<b>{mun_name}</b>, {state}<br>"
                        f"Mesoregion: {meso_name}<br>"
                        f"Production (2018): {production:,.0f} tonnes"
                    ),
                )
            )

# Add mesoregion centroid markers
for meso_key, meso in MESOREGIONS.items():
    if meso["production_tonnes_2018"] < 100:
        continue
    fig.add_trace(
        go.Scattergeo(
            lon=[meso["centroid_lon"]],
            lat=[meso["centroid_lat"]],
            mode="markers+text",
            marker=dict(
                size=8,
                color="#8b7355",
                symbol="diamond",
                line=dict(width=1, color="#4a3728"),
            ),
            text=[meso["meso_name"]],
            textposition="top center",
            textfont=dict(size=10, color="#4a3728"),
            showlegend=False,
            hovertext=(
                f"{meso['meso_name']}<br>"
                f"{meso['state_name']}<br>"
                f"Production: {meso['production_tonnes_2018']:,.0f} tonnes"
            ),
        )
    )

fig.update_layout(
    title="Brazil Coffee-Producing Municipalities — Shading by 2018 Production",
    geo=dict(
        scope="south america",
        showland=True,
        landcolor="#f0ebe3",
        showocean=True,
        oceancolor="#e8f0f8",
        showcountries=True,
        countrycolor="#d5c8b5",
        countrywidth=0.5,
        lonaxis_range=[-55, -35],
        lataxis_range=[-28, -8],
        projection_type="mercator",
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