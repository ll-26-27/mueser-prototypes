---
title: A 1786 route, resolved — place names to a map
description: 24 historical German place names from a synthetic travel ledger → GOV, Wikidata and the World Historical Gazetteer → a recorded decision per name, 21 automatic and 3 for review → DuckDB, GeoJSON, SQLite → a single-file map with a candidate inspector and a Datasette site.
author: claude
created: 2026-11-04
---

# A 1786 route, resolved: place names to a map

Open **`outputs/index.html`**. Click any point: the panel lists every mention
behind it (document, row, date) and every candidate the three gazetteers
returned, with its score, source, coordinates, type, time span and
population, and the one-line reason the resolver chose or did not choose.
The unresolved names are listed on the right with their candidates.

## What happened

`inputs/places.csv` has 24 rows: the places of an invented 1786 journey from
Breslau to Königsberg and back to Kolberg, written as an eighteenth-century
clerk would ("Breßlau", "Frankfurth an der Oder", "Colberg"), with a modern
name column, a date and a note. Three names are there to be difficult:
**Brandenburg** (town or margraviate), **Halle** (Saale or Westphalia) and
**Neustadt** (dozens).

| outcome | names | how |
|---|---|---|
| auto | 21 | 9 because the gazetteers agreed on one location within 5 km (Breslau, Liegnitz, Magdeburg, Memel, Bautzen, Dresden, Bunzlau, Danzig, Frankfurt (Oder)); 12 because one same-name place was at least ten times more populous than the next and the reason says so (Berlin, Brandenburg → Brandenburg an der Havel, Königsberg → Kaliningrad, Leipzig, Posen, Thorn, Görlitz, Elbing, Meißen, Kolberg, Tilsit, Landsberg an der Warthe) |
| unresolved | 3 | Halle (36 candidates), Neustadt (37), Stettin (21): several places score 1.0 and no population tie-break reaches 10×. They are in `operations/work/review.csv` |

Each "auto by population" decision is marked in the panel with "Check if the
source could mean a smaller place". For a journey ledger the big city is the
likely reading; for a parish register it would not be, and the threshold
(`--accept-min`, `--margin`, `--populous-tiebreak`) is a parameter of the
run, recorded in `run.json`.

**Stettin** is instructive: GOV returns the city (BREADTJO81MC-style textual
id) and several Stettin farms and districts, all exact name matches, and the
city's GOV record carries no population in the search result, so the
tie-break has nothing to work with. One click in `review.csv` fixes it, and
the fix is recorded as `reviewed`.

**Königsberg → Kaliningrad.** Wikidata's label is the modern one; the
historical name is an alias. The record keeps `surface_form` "Königsberg in
Preußen" and `normalized` "Königsberg"; the URI is what resolved.

## The pipeline

1. **`python -m mueser.maps.load table`** (deterministic code). Reads the
   CSV; each row becomes a Record with `surface_form` = the name as written,
   `normalized` = the modern-name column, `date_start` = the date, and
   `source.page_id` = the row number, so a point can always be traced to a
   row.
2. **`python -m mueser.maps.resolve run`** (deterministic lookup + recorded
   rule). Asks GOV, Wikidata and WHG for each distinct name; decides; writes
   `records_resolved.jsonl`, `review.csv`, `decisions.json`, `run.json`.
3. **`python -m mueser.maps.load records`** and the candidates table
   (deterministic). Into `operations/work/research.duckdb`.
4. **`python -m mueser.maps.export geojson|sqlite`** (deterministic).
   `outputs/records.geojson` + `unresolved.json`; `outputs/research.db` for
   Datasette.
5. **`python -m mueser.maps.build_map build`** (deterministic). Embeds the
   GeoJSON, the unresolved list and `decisions.json` into the template and
   writes `outputs/index.html`.

```sh
U=01-use-cases/maps/01-places-to-map
uv run python -m mueser.maps.load table $U/inputs/places.csv --db $U/operations/work/research.duckdb \
  --doc-id reiseroute-1786 --name-col as_written --normalized-col modern_name --date-col date \
  --notes-cols entry_type,note --also-jsonl $U/operations/work/01-records.jsonl
uv run python -m mueser.maps.resolve run --records $U/operations/work/01-records.jsonl --out $U/operations/work --sources gov,wikidata,whg
uv run python -m mueser.maps.load records $U/operations/work/records_resolved.jsonl --db $U/operations/work/research.duckdb
uv run python -m mueser.maps.export geojson --db $U/operations/work/research.duckdb --out $U/outputs/records.geojson
uv run python -m mueser.maps.export sqlite  --db $U/operations/work/research.duckdb --out $U/outputs/research.db
uv run python -m mueser.maps.build_map build --geojson $U/outputs/records.geojson --decisions $U/operations/work/decisions.json \
  --out $U/outputs/index.html --title "A 1786 route, resolved"
uv run datasette $U/outputs/research.db -m $U/datasette/metadata.yml   # then open the `places` view
```

Add `geonames` to `--sources` once `GEONAMES_USERNAME` is in `.env`.

## Reviewing

Open `operations/work/review.csv` in a spreadsheet. Rows are grouped by name;
each row is one candidate with its source, score, coordinates, type,
population and time span. Put the chosen candidate's `uri` in `your_choice`
(or `none`), save, and rerun step 2: the choice is applied as `reviewed` and
the original table is kept as `review_regenerated.csv`.

## What the gazetteers are

- **GOV** (gov.genealogy.net): the historical gazetteer of the German-speaking
  world. Its JSON API returns names with validity spans as Julian day numbers
  (converted to years here), administrative membership over time, GOV's own
  type codes (51 = Stadt) and population series. The search is a
  contains-search ("Breslau" also returns "Peterswaldau, Bez. Breslau"), which
  the scoring handles.
- **Wikidata**: historical names survive as aliases; coordinates are modern.
  Used through the entity API; cached entities are trimmed to the properties
  read (P625 coordinates, P17 country, P31 type, P571/P576 dates, P1082
  population), and the cache entry says so.
- **World Historical Gazetteer**: an aggregator with name variants and time
  spans; its index search answered without a token.

## Rights

OpenFreeMap tiles (OpenMapTiles / OpenStreetMap contributors, ODbL). GOV data
© Verein für Computergenealogie, CC BY-SA. Wikidata CC0. WHG per its
contributing datasets. The input table is invented.
