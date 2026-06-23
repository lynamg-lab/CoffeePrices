"""Build IBGE municipality-to-mesoregion lookup and filter producing municipalities.

Provides:
- `build_meso_lookup()` — fetches from IBGE API, caches as JSON
- `load_meso_lookup()` — loads cached lookup
- `filter_producing_municipalities()` — saves a GeoJSON of only producing municipios
- `load_producing_municipalities()` — loads the filtered GeoJSON as a dict
"""

import json
import os
import urllib.request
import gzip

from src.config import (
    IBGE_STATE_CODES,
    MESO_LOOKUP_JSON,
    MUNICIPALITY_GEOJSON,
    PRODUCING_GEOJSON,
)

_IBGE_MUNICIPIOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{}/municipios"


def _fetch_json(url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(gzip.decompress(resp.read()))


def build_meso_lookup() -> dict[str, tuple[str, str]]:
    """Fetch all municipios from IBGE for coffee states, return {geocode: (meso_id, meso_name)}."""
    lookup: dict[str, tuple[str, str]] = {}
    for state_name, state_code in IBGE_STATE_CODES.items():
        url = _IBGE_MUNICIPIOS_URL.format(state_code)
        municipios = _fetch_json(url)
        for m in municipios:
            geocode = str(m["id"])
            meso = m["microrregiao"]["mesorregiao"]
            lookup[geocode] = (str(meso["id"]), meso["nome"])
    os.makedirs(os.path.dirname(MESO_LOOKUP_JSON), exist_ok=True)
    with open(MESO_LOOKUP_JSON, "w", encoding="utf-8") as f:
        json.dump(lookup, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(lookup)} municipality -> mesoregion mappings to {MESO_LOOKUP_JSON}")
    return lookup


def load_meso_lookup() -> dict[str, tuple[str, str]]:
    """Load cached meso lookup, or build if missing."""
    if os.path.exists(MESO_LOOKUP_JSON):
        with open(MESO_LOOKUP_JSON, encoding="utf-8") as f:
            raw = json.load(f)
        return {k: (v[0], v[1]) for k, v in raw.items()}
    return build_meso_lookup()


def filter_producing_municipalities() -> list[dict]:
    """Filter the full GeoJSON to municipalities with non-zero 2018 arabica production,
    attach mesoregion info, and save as a lighter GeoJSON."""
    meso_lookup = load_meso_lookup()

    with open(MUNICIPALITY_GEOJSON, encoding="utf-8") as f:
        full = json.load(f)

    filtered: list[dict] = []
    for feature in full["features"]:
        props = feature["properties"]
        production = props.get("production_of_arabica_coffee_tonnes_2018", 0) or 0
        if production <= 0:
            continue

        geocode = props["municipality_geocode"]
        if geocode in meso_lookup:
            meso_id, meso_name = meso_lookup[geocode]
        else:
            meso_id, meso_name = "", ""

        props["meso_id"] = meso_id
        props["meso_name"] = meso_name
        filtered.append(feature)

    geojson = {"type": "FeatureCollection", "features": filtered}
    os.makedirs(os.path.dirname(PRODUCING_GEOJSON), exist_ok=True)
    with open(PRODUCING_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)
    print(f"Saved {len(filtered)} producing municipalities to {PRODUCING_GEOJSON}")
    return filtered


def load_producing_municipalities() -> list[dict]:
    """Load filtered producing municipalities GeoJSON, or build if missing."""
    if os.path.exists(PRODUCING_GEOJSON):
        with open(PRODUCING_GEOJSON, encoding="utf-8") as f:
            return json.load(f)["features"]
    return filter_producing_municipalities()