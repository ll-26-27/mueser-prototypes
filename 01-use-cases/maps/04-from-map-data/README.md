---
title: From map data — Lower Silesia as GOV holds it
description: No text behind it. A bounding-box query to GOV returns 1,715 historical places with coordinates, kinds and every name with the years it was valid → DuckDB with the spatial extension → questions asked in SQL → the same map with a time slider across 1945, a Datasette site, and a GeoPackage for QGIS.
author: claude
created: 2026-11-05
---

# From map data: Lower Silesia as GOV holds it

Open **`outputs/index.html`** and drag the year range across 1945: the
German names go out and the Polish names come in. Nothing in this folder
was read from a page. It is the use case for research that starts from a
dataset, a gazetteer extract, a spreadsheet with coordinates, a shapefile.

## What happened

`operations/01-fetch-gov-region.py` asked GOV for everything inside a
rectangle around Breslau (lat 50.80–51.50, lon 16.30–17.60) and kept all of
it: 1,715 objects, every one with coordinates, 3,721 names (2,284 German,
1,436 Polish, 1 Latin), each name with the years GOV records it as valid.

`operations/02-load-and-query.py` turned every *name* into a record
(`surface_form` the name, `date_start` the validity as an EDTF interval
such as `1945/..`, `lat`/`lon` the place, `resolution_status` `reviewed`
because the coordinates came with the data), loaded them into DuckDB with
the spatial extension, and asked:

| question | answer |
|---|---|
| What kinds of object are in the rectangle? | 1,054 Ortsteile, 253 Protestant and 98 Catholic parishes, 114 churches, 38 Amtsbezirke, 35 Gutsbezirke, 31 Kreise, 23 towns, 21 Standesämter … |
| How many names end or begin in 1945? | 552 German names end in 1945; 955 Polish names begin then |
| Which places had more than two names? | Szczytniki has 13 recorded spellings; Breslau five (Wrezlaue, Wreczelaw, Wratislavia 1295–1305, Breslau, Wrocław); Kuraszków was Alt Karoschke until 1936, Karoschke for a year, Lindenwaldau 1937–1945 |
| What is nearest Breslau's centre? | by great-circle distance in SQL (`ST_Distance_Sphere`) |
| Which towns would a 1786 traveller have passed? | 23 `Stadt` objects with their German and Polish names |
| Where does the 1786 route (maps/01) cross this rectangle? | one stop (Breslau), joined to the nearest GOV object |

The full tables, with the SQL that produced each, are in
`outputs/queries.md`.

## Outputs

- `outputs/index.html`: the map. Each circle is a place; the panel lists
  its names with their years. The year slider filters names by validity,
  so a range of 1900–1940 shows German names and 1946–2000 Polish ones.
- `outputs/research.db`: SQLite for Datasette
  (`uv run datasette outputs/research.db -m ../01-places-to-map/datasette/metadata.yml`).
- `outputs/gov-region.gpkg`: a GeoPackage, one row per place with its
  names joined, for QGIS.
- `outputs/records.geojson`: the records as points.
- `inputs/gov-region.geojson` and `inputs/gov-region-names.csv`: the data
  as fetched, so the step from data to records is inspectable.

## Using your own map data instead

Any of these go through the same loader and viewer:

```sh
# a CSV or XLSX with coordinates (no gazetteer needed)
uv run python -m mueser.maps.load table my-places.csv --db work/research.duckdb --doc-id my-table \
  --name-col name --lat-col lat --lon-col lon --date-col year --also-jsonl work/records.jsonl
# a GeoJSON / shapefile / GeoPackage (geometry centroids become the points)
uv run python -m mueser.maps.load table my-layer.geojson --db work/research.duckdb --doc-id my-layer --name-col NAME
# a CSV of names WITHOUT coordinates: resolve them first (maps/01)
```

Then `export geojson`, `export sqlite`, `build_map build` as in
`01-places-to-map/README.md`. Historical boundary datasets (the MPIDR
Population History GIS collection, HGIS Germany) load the same way; their
licences differ and are not included here.

## Rights

GOV data © Verein für Computergenealogie e.V., CC BY-SA; fetched 5 November
2026 and cached. Tiles: OpenFreeMap / OpenStreetMap contributors.
