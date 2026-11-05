"""Step 2 (deterministic code): map data → records → DuckDB with the spatial extension → questions asked in SQL →
GeoJSON, SQLite and GeoPackage out.

    uv run python 01-use-cases/maps/04-from-map-data/operations/02-load-and-query.py

Each NAME becomes one record (surface_form = the name as GOV has it; date_start/date_end = the years the name was
valid; lat/lon = the place; resolution_status = reviewed, because the coordinates come with the data), so the
same viewer's time slider shows the 1945 renaming. The queries below are the kind a historian asks of a dataset:
what is here, what changed, what is near what. Results go to outputs/queries.md with the SQL that produced them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mueser.maps import db  # noqa: E402
from mueser.maps.export import records_geojson  # noqa: E402
from mueser.shared.record import Record, Source, write_jsonl  # noqa: E402

INPUTS = HERE.parent / "inputs"
WORK = HERE / "work"
OUT = HERE.parent / "outputs"
ROUTE = HERE.parents[1] / "01-places-to-map" / "outputs" / "records.geojson"


def records_from_geojson(path: Path) -> list[Record]:
    fc = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for f in fc["features"]:
        p = f["properties"]; lon, lat = f["geometry"]["coordinates"]
        current = next((n["value"] for n in p["names"] if n["lang"] == "pol" and not n.get("to")), None) or \
                  next((n["value"] for n in p["names"] if not n.get("to")), None)
        for i, n in enumerate(p["names"]):
            src = Source(doc_id="gov-region", page_id=p["gov_id"], line_index=i, extraction_method="gov/searchByBoundingBox")
            # Validity as an EDTF interval: "1945/.." = from 1945 on; "../1945" = until 1945; None = no dates known.
            frm, to = n.get("from"), n.get("to")
            interval = f"{frm or '..'}/{to or '..'}" if (frm or to) else None
            out.append(Record.new(type="place", surface_form=n["value"], source=src, normalized=current, date_start=interval,
                                  lat=lat, lon=lon, place_uri=p["uri"], resolution_status="reviewed", resolution_source="gov", confidence=1.0,
                                  notes=f"{n['lang']}; {'; '.join(p['types'])}"))
    return out


QUERIES = [
    ("What kinds of object are in the rectangle?",
     "SELECT split_part(notes, '; ', 2) AS kind, count(DISTINCT source_page_id) AS places FROM records GROUP BY 1 ORDER BY 2 DESC LIMIT 12"),
    ("How many places carry a German name that ended in 1945, and a Polish name that began then?",
     "SELECT sum(CASE WHEN notes LIKE 'deu;%' AND year_end = 1945 THEN 1 ELSE 0 END) AS german_names_ended_1945, "
     "sum(CASE WHEN notes LIKE 'pol;%' AND year_start = 1945 THEN 1 ELSE 0 END) AS polish_names_from_1945, count(DISTINCT source_page_id) AS places FROM records"),
    ("Which places had more than two names over time?",
     "SELECT source_page_id AS gov_id, normalized AS today, count(*) AS names, string_agg(surface_form || CASE WHEN year_start IS NULL AND year_end IS NULL THEN '' ELSE ' (' || coalesce(year_start::VARCHAR, '?') || '–' || coalesce(year_end::VARCHAR, '') || ')' END, ' · ' ORDER BY year_start NULLS FIRST) AS history "
     "FROM records GROUP BY 1, 2 HAVING count(*) > 2 ORDER BY names DESC, gov_id LIMIT 12"),
    ("The ten places nearest Breslau's centre (17.0325, 51.11), by great-circle distance",
     "SELECT DISTINCT source_page_id AS gov_id, normalized AS today, round(ST_Distance_Sphere(ST_Point(lon, lat), ST_Point(17.0325, 51.11)) / 1000, 1) AS km "
     "FROM records WHERE source_page_id NOT LIKE 'BREADT%' ORDER BY km LIMIT 10"),
    ("Towns (Stadt) in the rectangle, with the name a 1786 traveller would have used",
     "SELECT source_page_id AS gov_id, string_agg(DISTINCT surface_form, ' / ') AS names, any_value(normalized) AS today FROM records WHERE notes LIKE '%Stadt%' AND notes NOT LIKE '%Stadtteil%' GROUP BY 1 ORDER BY 1 LIMIT 20"),
]


def main() -> None:
    recs = records_from_geojson(INPUTS / "gov-region.geojson")
    WORK.mkdir(parents=True, exist_ok=True)
    write_jsonl(recs, WORK / "02-records.jsonl")
    dbp = WORK / "research.duckdb"
    if dbp.exists():
        dbp.unlink()
    con = db.connect(dbp)
    n = db.upsert_records(con, recs)
    print(f"{n} name-records from {len({r.source.page_id for r in recs})} places -> {dbp}")
    lines = ["# Questions asked of the map data\n", f"Database: `{dbp.relative_to(ROOT)}` (DuckDB with the spatial extension). Each row is one *name* of one place; `source_page_id` is the GOV id.\n"]
    for title, sql in QUERIES:
        try:
            cur = con.execute(sql)
            cols = [d[0] for d in cur.description]; rows = cur.fetchall()
            lines.append(f"\n## {title}\n\n```sql\n{sql}\n```\n\n| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
            for r in rows:
                lines.append("| " + " | ".join(str(v) if v is not None else "" for v in r) + " |\n")
            print(f"{title}: {len(rows)} rows")
        except Exception as e:  # noqa: BLE001
            lines.append(f"\n## {title}\n\nfailed: {e}\n")
            print(f"{title}: FAILED {e}")
    # A spatial join with another dataset: which 1786 route stops fall inside this rectangle, and their nearest GOV object.
    if ROUTE.exists():
        route = json.loads(ROUTE.read_text(encoding="utf-8"))
        fc = json.loads((INPUTS / "gov-region.geojson").read_text(encoding="utf-8"))
        lon0, lat0, lon1, lat1 = fc["bbox"]
        inside = [f for f in route["features"] if lon0 <= f["geometry"]["coordinates"][0] <= lon1 and lat0 <= f["geometry"]["coordinates"][1] <= lat1]
        lines.append("\n## Which stops of the 1786 route (maps/01) fall inside the rectangle, and what GOV has at that point\n\n| stop | nearest GOV object | km |\n|---|---|---|\n")
        for f in inside:
            lon, lat = f["geometry"]["coordinates"]
            r = con.execute("SELECT source_page_id, any_value(normalized), round(min(ST_Distance_Sphere(ST_Point(lon, lat), ST_Point(?, ?))) / 1000, 2) AS km FROM records GROUP BY 1 ORDER BY km LIMIT 1", [lon, lat]).fetchone()
            lines.append(f"| {f['properties'].get('normalized') or f['properties']['surface_form']} | {r[0]} ({r[1]}) | {r[2]} |\n")
        print(f"route stops inside: {len(inside)}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "queries.md").write_text("".join(lines), encoding="utf-8")
    fcj, unresolved = records_geojson(con)
    (OUT / "records.geojson").write_text(json.dumps(fcj, ensure_ascii=False), encoding="utf-8")
    (OUT / "unresolved.json").write_text("[]", encoding="utf-8")
    db.to_sqlite(con, OUT / "research.db")
    # GeoPackage for QGIS: one layer of places (one row per place, names joined), via GeoPandas.
    try:
        import geopandas as gpd
        from shapely.geometry import Point

        fc = json.loads((INPUTS / "gov-region.geojson").read_text(encoding="utf-8"))
        gdf = gpd.GeoDataFrame([{"gov_id": f["properties"]["gov_id"], "uri": f["properties"]["uri"], "types": "; ".join(f["properties"]["types"]),
                                 "names": " / ".join(f"{n['value']} [{n['lang']}{(' ' + str(n['from'])) if n.get('from') else ''}{('–' + str(n['to'])) if n.get('to') else ''}]" for n in f["properties"]["names"]),
                                 "geometry": Point(f["geometry"]["coordinates"])} for f in fc["features"]], crs="EPSG:4326")
        gdf.to_file(OUT / "gov-region.gpkg", layer="places", driver="GPKG")
        print(f"GeoPackage -> {OUT / 'gov-region.gpkg'} ({len(gdf)} places)")
    except Exception as e:  # noqa: BLE001
        print(f"GeoPackage not written: {e}")
    print(f"queries -> {OUT / 'queries.md'}; geojson -> {OUT / 'records.geojson'}")


if __name__ == "__main__":
    main()
