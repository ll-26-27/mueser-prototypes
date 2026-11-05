"""DuckDB with the spatial extension as the working store; SQLite export for Datasette and QGIS.

One table ``records`` in the shared schema (flat columns), plus ``candidates`` from reconciliation so the
database itself carries the audit trail. ``to_sqlite`` writes the same tables to a SQLite file that Datasette
(with datasette-cluster-map) serves as a searchable website with a map.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import duckdb

from mueser.shared.record import FLAT_COLUMNS, Record

DDL = """
CREATE TABLE IF NOT EXISTS records (
  id VARCHAR PRIMARY KEY, type VARCHAR, surface_form VARCHAR, normalized VARCHAR,
  source_doc_id VARCHAR, source_page_id VARCHAR, source_line_index INTEGER, source_bbox VARCHAR, source_iiif_canvas VARCHAR,
  source_transcription_backend VARCHAR, source_extraction_method VARCHAR,
  date_start VARCHAR, date_end VARCHAR, year_start INTEGER, year_end INTEGER,
  place_uri VARCHAR, lat DOUBLE, lon DOUBLE, resolution_status VARCHAR, resolution_source VARCHAR, confidence DOUBLE, notes VARCHAR
);
CREATE TABLE IF NOT EXISTS candidates (
  name VARCHAR, status VARCHAR, reason VARCHAR, chosen_uri VARCHAR, candidate_rank INTEGER, source VARCHAR, uri VARCHAR, label VARCHAR,
  score DOUBLE, lat DOUBLE, lon DOUBLE, feature_type VARCHAR, admin VARCHAR, population BIGINT, valid_from VARCHAR, valid_to VARCHAR, alt_names VARCHAR
);
"""


def connect(path: Path) -> duckdb.DuckDBPyConnection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    try:
        con.execute("INSTALL spatial; LOAD spatial;")
    except Exception as e:  # noqa: BLE001
        print(f"note: DuckDB spatial extension not loaded ({e}); lat/lon columns still work")
    for stmt in DDL.strip().split(";"):
        if stmt.strip():
            con.execute(stmt)
    return con


def upsert_records(con: duckdb.DuckDBPyConnection, records: list[Record]) -> int:
    rows = [[r.to_flat().get(c) for c in FLAT_COLUMNS] for r in records]
    if not rows:
        return 0
    con.executemany(f"INSERT OR REPLACE INTO records ({', '.join(FLAT_COLUMNS)}) VALUES ({', '.join('?' * len(FLAT_COLUMNS))})", rows)
    return len(rows)


def replace_candidates(con: duckdb.DuckDBPyConnection, review_csv: Path) -> int:
    con.execute("DROP TABLE IF EXISTS candidates")
    con.execute([s for s in DDL.split(";") if "candidates" in s][0])
    con.execute(f"INSERT INTO candidates SELECT name, status, reason, chosen_uri, candidate_rank, source, uri, label, score, lat, lon, feature_type, admin, population, valid_from, valid_to, alt_names FROM read_csv_auto('{review_csv}', header=true, all_varchar=false)")
    return con.execute("SELECT count(*) FROM candidates").fetchone()[0]


def to_sqlite(con: duckdb.DuckDBPyConnection, sqlite_path: Path) -> None:
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()
    lite = sqlite3.connect(str(sqlite_path))
    for table in ("records", "candidates"):
        cols = [c[0] for c in con.execute(f"DESCRIBE {table}").fetchall()]
        rows = con.execute(f"SELECT * FROM {table}").fetchall()
        lite.execute(f"CREATE TABLE {table} ({', '.join(cols)})")
        lite.executemany(f"INSERT INTO {table} VALUES ({', '.join('?' * len(cols))})", rows)
    # Datasette's cluster-map plugin looks for columns named latitude/longitude; give it a view.
    lite.execute("CREATE VIEW places AS SELECT id, type, surface_form, normalized, source_doc_id, source_page_id, source_line_index, date_start, date_end, year_start, year_end, place_uri, lat AS latitude, lon AS longitude, resolution_status, resolution_source, confidence, notes FROM records")
    lite.commit()
    lite.close()
