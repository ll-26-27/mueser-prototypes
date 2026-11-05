"""Export the records table as GeoJSON (for the web map and QGIS) and SQLite (for Datasette).

Resolved records become Point features; unresolved ones are listed in a sidecar ``unresolved.json`` so the map can
show them beside the points instead of dropping them.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from mueser.shared.record import FLAT_COLUMNS
from . import db

app = typer.Typer(help="Export GeoJSON / SQLite from the DuckDB store.")


def records_geojson(con) -> tuple[dict, list[dict]]:
    rows = con.execute(f"SELECT {', '.join(FLAT_COLUMNS)} FROM records").fetchall()
    feats, unresolved = [], []
    for row in rows:
        d = dict(zip(FLAT_COLUMNS, row))
        if d["lat"] is None or d["lon"] is None:
            if d["type"] == "place":
                unresolved.append(d)      # persons, orgs and events are never placed; they stay in the database
            continue
        props = {k: v for k, v in d.items() if k not in ("lat", "lon")}
        feats.append({"type": "Feature", "id": d["id"], "geometry": {"type": "Point", "coordinates": [d["lon"], d["lat"]]}, "properties": props})
    return {"type": "FeatureCollection", "features": feats}, unresolved


@app.command()
def geojson(db_path: Path = typer.Option(..., "--db"), out: Path = typer.Option(...)):
    con = db.connect(db_path)
    fc, unresolved = records_geojson(con)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    (out.with_name("unresolved.json")).write_text(json.dumps(unresolved, ensure_ascii=False, indent=1), encoding="utf-8")
    typer.echo(f"{len(fc['features'])} features -> {out}; {len(unresolved)} unresolved -> unresolved.json")


@app.command()
def sqlite(db_path: Path = typer.Option(..., "--db"), out: Path = typer.Option(...)):
    con = db.connect(db_path)
    db.to_sqlite(con, out)
    typer.echo(f"SQLite -> {out}  (serve with: uv run datasette {out} -m datasette/metadata.yml)")


if __name__ == "__main__":
    app()
