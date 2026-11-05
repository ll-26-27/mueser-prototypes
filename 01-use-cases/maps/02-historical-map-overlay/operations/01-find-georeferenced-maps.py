"""Step 1 (deterministic lookup): ask the Allmaps API which georeferenced historical maps cover each resolved
place on the route, and write a table a person can choose from.

    uv run python 01-use-cases/maps/02-historical-map-overlay/operations/01-find-georeferenced-maps.py

Reads ../../01-places-to-map/outputs/records.geojson; queries https://api.allmaps.org/maps?intersects=<lon>,<lat>
(keyless, checked 2026-11-04); writes outputs/georeferenced-maps.csv with one row per (place, map): the map's
annotation URL (what the viewer needs), its IIIF image, pixel size, number of ground control points, and the
holding institution's IIIF service when the URL reveals it. Every API answer is cached under cache/allmaps/.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mueser.maps.gazetteer.base import HttpCached  # noqa: E402

GEOJSON = HERE.parents[1] / "01-places-to-map" / "outputs" / "records.geojson"
OUT = HERE.parent / "outputs" / "georeferenced-maps.csv"
API = "https://api.allmaps.org/maps"


class Allmaps(HttpCached):
    name = "allmaps"
    min_interval = 0.5

    def maps_at(self, lon: float, lat: float, limit: int = 200) -> list[dict]:
        return self._get(API, params={"intersects": f"{lon},{lat}", "limit": limit})


def main() -> None:
    fc = json.loads(GEOJSON.read_text(encoding="utf-8"))
    places = {}
    for f in fc["features"]:
        p = f["properties"]
        key = p.get("normalized") or p["surface_form"]
        places.setdefault(key, f["geometry"]["coordinates"])
    api = Allmaps()
    rows = []
    for name, (lon, lat) in sorted(places.items()):
        try:
            maps = api.maps_at(lon, lat)
        except Exception as e:  # noqa: BLE001
            print(f"{name}: error {e}")
            continue
        for m in maps:
            res = m.get("resource", {}) or {}
            img = res.get("id", "")
            host = urlparse(img).netloc
            w, h = res.get("width"), res.get("height")
            gcp_list = m.get("gcps", []) or []
            gcps = len(gcp_list)
            # How much of the earth the sheet covers, from the spread of its ground control points. A world map
            # spans 300° of longitude; a city plan a fraction of a degree. This is the column to sort by.
            lons = [g["geo"][0] for g in gcp_list if g.get("geo")]
            lats = [g["geo"][1] for g in gcp_list if g.get("geo")]
            span_lon = round(max(lons) - min(lons), 3) if lons else None
            span_lat = round(max(lats) - min(lats), 3) if lats else None
            scale = ("city" if span_lon is not None and span_lon < 0.5 and span_lat < 0.5 else
                     "regional" if span_lon is not None and span_lon < 8 and span_lat < 6 else
                     "continental or world" if span_lon is not None else "unknown")
            # Does the sheet's control-point box actually contain the place? Allmaps' intersects test uses the
            # warped mask; a badly georeferenced sheet (control points on the wrong continent) can still match.
            contains = bool(lons) and (min(lons) - 0.5 <= lon <= max(lons) + 0.5) and (min(lats) - 0.5 <= lat <= max(lats) + 0.5)
            label = ""
            for part in (res.get("partOf") or []):
                for p2 in (part.get("partOf") or []):
                    lab = p2.get("label") or {}
                    label = label or " ".join(v[0] for v in lab.values() if v)
                lab = part.get("label") or {}
                label = label or " ".join(v[0] for v in lab.values() if v)
            provider = " ".join(v[0] for pr in (res.get("provider") or []) for v in (pr.get("label") or {}).values() if v)
            rows.append({"place": name, "lon": lon, "lat": lat, "annotation_url": m.get("id", ""), "iiif_image": img, "host": host,
                         "label": label.strip(), "provider": provider, "width": w, "height": h, "gcps": gcps, "span_lon_deg": span_lon,
                         "span_lat_deg": span_lat, "scale": scale, "gcp_box_contains_place": contains,
                         "created": m.get("created", "") or m.get("modified", "")})
        print(f"{name}: {len(maps)} georeferenced maps")
        time.sleep(0.2)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["place", "lon", "lat", "annotation_url", "iiif_image", "host", "label", "provider", "width", "height", "gcps", "span_lon_deg", "span_lat_deg", "scale", "gcp_box_contains_place", "created"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["place"], r["span_lon_deg"] if r["span_lon_deg"] is not None else 999)))
    hosts = {}
    for r in rows:
        hosts[r["host"]] = hosts.get(r["host"], 0) + 1
    print(f"{len(rows)} (place, map) rows -> {OUT}")
    by_scale = {}
    for r in rows:
        by_scale[r["scale"]] = by_scale.get(r["scale"], 0) + 1
    print("by scale:", by_scale)
    print("regional and city sheets whose control points contain the place:")
    seen = set()
    for r in sorted(rows, key=lambda r: (r["span_lon_deg"] if r["span_lon_deg"] is not None else 999)):
        if r["scale"] not in ("city", "regional") or not r["gcp_box_contains_place"] or r["annotation_url"] in seen:
            continue
        seen.add(r["annotation_url"])
        print(f"  {r['place']:26} {r['span_lon_deg']:>7}° × {r['span_lat_deg']:>6}°  {r['label'][:60]!r} ({r['provider'][:30]})  {r['annotation_url']}")
    print("image hosts:", dict(sorted(hosts.items(), key=lambda kv: -kv[1])[:12]))


if __name__ == "__main__":
    main()
