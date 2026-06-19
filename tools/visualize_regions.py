"""Generate an interactive world map showing the 5 coffee-producing region bounding boxes.

Usage:  python tools/visualize_regions.py
Output: tools/region_map.html (opens automatically in browser)
"""

import sys
import webbrowser
from pathlib import Path

import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import REGIONS

colors = {
    "brazil": "#7cb342",
    "vietnam": "#c0ca33",
    "colombia": "#f4511e",
    "indonesia": "#fb8c00",
    "ethiopia": "#43a047",
}

fig = go.Figure()

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
            line=dict(width=2.5, color=colors.get(key, "#888")),
            name=label,
            hovertemplate="%{text}<extra></extra>",
            text=[label],
        )
    )

fig.update_layout(
    title="Coffee Producing Regions — Bounding Boxes",
    geo=dict(
        showland=True,
        landcolor="#f0ebe3",
        coastlinecolor="#8b7355",
        coastlinewidth=0.5,
        showocean=True,
        oceancolor="#e8f0f8",
        showcountries=True,
        countrycolor="#d5c8b5",
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
