"""Embed the exported GeoJSON, the unresolved list and the reconciliation decisions into the single-file web map.

    uv run python -m mueser.maps.build_map --geojson out/records.geojson --decisions out/decisions.json --out outputs/index.html

The template is web/map-template.html; the three ``/*__DATA__*/`` placeholders are replaced with JSON. The page opens
by double-clicking: data is inline; only the basemap tiles, MapLibre and (optionally) the Allmaps plugin load
from the network.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from mueser.shared import env
from mueser.shared.review import enhance_html

app = typer.Typer(help="Build the single-file MapLibre viewer.")
TEMPLATE = Path(__file__).parent / "web" / "map-template.html"


@app.callback()
def _root():
    """Sub-commands below."""


@app.command()
def build(geojson: Path = typer.Option(..., exists=True), out: Path = typer.Option(...),
          decisions: Optional[Path] = typer.Option(None), unresolved: Optional[Path] = None,
          title: str = "Places", subtitle: str = "", allmaps_annotation: Optional[str] = None,
          template: Path = TEMPLATE):
    html = template.read_text(encoding="utf-8")
    fc = json.loads(geojson.read_text(encoding="utf-8"))
    unres_path = unresolved or geojson.with_name("unresolved.json")
    unres = json.loads(unres_path.read_text(encoding="utf-8")) if unres_path.exists() else []
    dec = json.loads(decisions.read_text(encoding="utf-8")) if decisions and decisions.exists() else {}
    # No default overlay: every Allmaps sheet found for this route on 2026-11-04 either covered a continent or had
    # control points on the wrong part of the earth (see 01-use-cases/maps/02-historical-map-overlay). Set
    # ALLMAPS_ANNOTATION_URL in .env or pass --allmaps-annotation once a sound annotation exists.
    ann = allmaps_annotation or env.get("ALLMAPS_ANNOTATION_URL") or ""
    config = {"title": title, "subtitle": subtitle, "allmapsAnnotation": ann}
    html = (html.replace("/*__GEOJSON__*/null", json.dumps(fc, ensure_ascii=False))
                .replace("/*__UNRESOLVED__*/null", json.dumps(unres, ensure_ascii=False))
                .replace("/*__DECISIONS__*/null", json.dumps(dec, ensure_ascii=False))
                .replace("/*__CONFIG__*/null", json.dumps(config, ensure_ascii=False))
                .replace("__TITLE__", title))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(enhance_html(html, out, "map"), encoding="utf-8")
    typer.echo(f"{len(fc['features'])} points, {len(unres)} unresolved -> {out}")


if __name__ == "__main__":
    app()
