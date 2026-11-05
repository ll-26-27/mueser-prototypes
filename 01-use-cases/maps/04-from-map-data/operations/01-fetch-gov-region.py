"""Step 1 (deterministic lookup): pull every place GOV knows inside a rectangle, as map data.

    uv run python 01-use-cases/maps/04-from-map-data/operations/01-fetch-gov-region.py [--bbox lat0 lat1 lon0 lon1]

GOV's bounding-box search (https://gov.genealogy.net/api/searchByBoundingBox) returns objects with coordinates,
type codes, administrative membership and every name with the years it was valid. Writes
inputs/gov-region.geojson (one feature per place, all names kept) and inputs/gov-region-names.csv (one row per
name, with its validity years). The default rectangle is Lower Silesia around Breslau; it was chosen because the
1945 renaming makes the time dimension of the data visible on a map. The response is cached under
cache/gazetteer_gov/. No text source is involved: this is the use case for data that arrives as a map.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mueser.maps.gazetteer.base import HttpCached  # noqa: E402
from mueser.maps.gazetteer.gov import TYPE_LABELS, jd_to_year  # noqa: E402

INPUTS = HERE.parent / "inputs"
API = "https://gov.genealogy.net/api/searchByBoundingBox"
DEFAULT_BBOX = (50.80, 51.50, 16.30, 17.60)   # lat0, lat1, lon0, lon1: Breslau and its surroundings
EXTRA_TYPES = {"55": "Stadtteil/Ortsteil", "26": "Pfarrei (ev.)", "18": "Pfarrei (kath.)", "54": "Gutsbezirk", "129": "Kirche (kath.)", "21": "Kirche",
               "40": "Amtsbezirk", "13": "Kreis", "51": "Stadt", "39": "Gemeinde", "245": "Standesamt", "87": "Bahnhof", "30": "Kloster", "111": "Friedhof", "69": "Schule"}


class GOV(HttpCached):
    name = "gov"
    min_interval = 1.5

    def bbox(self, lat0, lat1, lon0, lon1):
        return self._get(API, params={"latitude0": lat0, "latitude1": lat1, "longitude0": lon0, "longitude1": lon1})


def name_years(n: dict) -> tuple[int | None, int | None]:
    ts = n.get("timespan") or {}
    b = jd_to_year((ts.get("begin") or {}).get("jd")) or n.get("beginYear")
    e = jd_to_year((ts.get("end") or {}).get("jd")) or n.get("endYear")
    return b, e


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbox", nargs=4, type=float, metavar=("LAT0", "LAT1", "LON0", "LON1"), default=DEFAULT_BBOX)
    a = ap.parse_args()
    lat0, lat1, lon0, lon1 = a.bbox
    t0 = time.time()
    items = GOV().bbox(lat0, lat1, lon0, lon1)
    feats, rows = [], []
    for it in items:
        pos = it.get("position") or {}
        if pos.get("lat") is None:
            continue
        codes = [t.get("value", "") for t in it.get("type") or []]
        labels = [TYPE_LABELS.get(c) or EXTRA_TYPES.get(c) or f"type {c}" for c in codes]
        names = []
        for n in it.get("name") or []:
            b, e = name_years(n)
            names.append({"lang": n.get("lang"), "value": n.get("value"), "from": b, "to": e})
            rows.append({"gov_id": it["id"], "lang": n.get("lang"), "name": n.get("value"), "valid_from": b or "", "valid_to": e or "",
                         "type": "; ".join(labels), "lat": pos["lat"], "lon": pos["lon"]})
        feats.append({"type": "Feature", "id": it["id"], "geometry": {"type": "Point", "coordinates": [pos["lon"], pos["lat"]]},
                      "properties": {"gov_id": it["id"], "uri": f"https://gov.genealogy.net/item/show/{it['id']}", "types": labels, "type_codes": codes,
                                     "names": names, "part_of": [p.get("ref") for p in it.get("partOf") or []], "last_modified": it.get("lastModification")}})
    INPUTS.mkdir(parents=True, exist_ok=True)
    (INPUTS / "gov-region.geojson").write_text(json.dumps({"type": "FeatureCollection", "bbox": [lon0, lat0, lon1, lat1], "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                                            "source": API, "features": feats}, ensure_ascii=False), encoding="utf-8")
    with (INPUTS / "gov-region-names.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["gov_id", "lang", "name", "valid_from", "valid_to", "type", "lat", "lon"])
        w.writeheader(); w.writerows(rows)
    by_lang = {}
    for r in rows:
        by_lang[r["lang"]] = by_lang.get(r["lang"], 0) + 1
    print(f"{len(items)} objects in bbox lat {lat0}–{lat1}, lon {lon0}–{lon1}; {len(feats)} with coordinates; {len(rows)} names {by_lang}; {time.time() - t0:.1f}s")
    print(f"-> {INPUTS / 'gov-region.geojson'}, {INPUTS / 'gov-region-names.csv'}")


if __name__ == "__main__":
    main()
