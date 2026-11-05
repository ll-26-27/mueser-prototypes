"""Load records into the database from the shared JSONL/CSV or from any CSV/XLSX/GeoJSON with a column map.

    uv run python -m mueser.maps.load records  --path records.jsonl --db research.duckdb
    uv run python -m mueser.maps.load table    --path places.csv --db research.duckdb --doc-id my-table \
        --name-col place --date-col year --type place

The table loader turns each row into a Record (surface_form = the name column, source.page_id = the row number),
so arbitrary spreadsheets flow through the same resolver and map as transcription output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from mueser.shared.record import Record, Source, read_csv, read_jsonl, write_jsonl
from . import db

app = typer.Typer(help="Load records or tables into DuckDB.")


def read_records(path: Path) -> list[Record]:
    if path.suffix == ".jsonl":
        return read_jsonl(path)
    if path.suffix == ".csv":
        return read_csv(path)
    raise typer.BadParameter("records must be .jsonl or .csv in the shared schema")


@app.command()
def records(path: Path, db_path: Path = typer.Option(..., "--db")):
    recs = read_records(path)
    con = db.connect(db_path)
    n = db.upsert_records(con, recs)
    typer.echo(f"{n} records -> {db_path}")


def table_to_records(path: Path, *, doc_id: str, name_col: str, type_: str = "place", date_col: Optional[str] = None,
                     date_end_col: Optional[str] = None, normalized_col: Optional[str] = None, notes_cols: list[str] | None = None,
                     lat_col: Optional[str] = None, lon_col: Optional[str] = None) -> list[Record]:
    import pandas as pd

    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    elif path.suffix.lower() == ".geojson" or path.suffix.lower() == ".json":
        import geopandas as gpd

        gdf = gpd.read_file(path)
        gdf["__lat"] = gdf.geometry.centroid.y
        gdf["__lon"] = gdf.geometry.centroid.x
        df = pd.DataFrame(gdf.drop(columns="geometry"))
        lat_col, lon_col = "__lat", "__lon"
    else:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    out = []
    for i, row in df.iterrows():
        name = str(row[name_col]).strip()
        if not name:
            continue
        notes = "; ".join(f"{c}={row[c]}" for c in (notes_cols or []) if str(row.get(c, "")).strip())
        src = Source(doc_id=doc_id, page_id=f"row{int(i) + 2}", extraction_method="csv")
        kw = {}
        if date_col and str(row.get(date_col, "")).strip():
            kw["date_start"] = str(row[date_col]).strip()
        if date_end_col and str(row.get(date_end_col, "")).strip():
            kw["date_end"] = str(row[date_end_col]).strip()
        if normalized_col and str(row.get(normalized_col, "")).strip():
            kw["normalized"] = str(row[normalized_col]).strip()
        if lat_col and lon_col and str(row.get(lat_col, "")).strip():
            kw.update(lat=float(row[lat_col]), lon=float(row[lon_col]), resolution_status="reviewed", resolution_source="manual")
        out.append(Record.new(type=type_, surface_form=name, source=src, notes=notes or None, **kw))  # type: ignore[arg-type]
    return out


@app.command()
def table(path: Path, db_path: Path = typer.Option(..., "--db"), doc_id: str = typer.Option(...), name_col: str = typer.Option(...),
          type_: str = typer.Option("place", "--type"), date_col: Optional[str] = None, date_end_col: Optional[str] = None,
          normalized_col: Optional[str] = None, notes_cols: str = typer.Option("", help="comma list of columns to keep in notes"),
          lat_col: Optional[str] = None, lon_col: Optional[str] = None, also_jsonl: Optional[Path] = None):
    recs = table_to_records(path, doc_id=doc_id, name_col=name_col, type_=type_, date_col=date_col, date_end_col=date_end_col,
                            normalized_col=normalized_col, notes_cols=[c for c in notes_cols.split(",") if c], lat_col=lat_col, lon_col=lon_col)
    if also_jsonl:
        write_jsonl(recs, also_jsonl)
    con = db.connect(db_path)
    n = db.upsert_records(con, recs)
    typer.echo(f"{n} records from {path.name} -> {db_path}")


if __name__ == "__main__":
    app()
