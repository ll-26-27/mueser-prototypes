# Maps

Three worked examples that take the same idea three steps further: a table
of historical place names becomes a map; a historical map becomes a layer on
it; and the places come from the transcription half instead of a table.

| Use case | Input | What runs | Output |
|---|---|---|---|
| [`01-places-to-map/`](01-places-to-map/) | a 24-row CSV of place names from a synthetic 1786 travel ledger, in the spelling of the time | load → three gazetteers (GOV, Wikidata, World Historical Gazetteer) → recorded decision per name → DuckDB → GeoJSON + SQLite | [map](01-places-to-map/outputs/index.html) with a candidate inspector; a Datasette site |
| [`02-historical-map-overlay/`](02-historical-map-overlay/) | the resolved points | ask the Allmaps index which georeferenced historical maps cover each point; check their control points | a [table](02-historical-map-overlay/outputs/georeferenced-maps.csv) of sheets, and the overlay toggle in every map page |
| [`03-from-page-to-map/`](03-from-page-to-map/) | Kraken's OCR of the five synthetic Fraktur pages, errors and all | mention list (model judgment, recorded) → verbatim check → records → the same resolver → map | [map](03-from-page-to-map/outputs/index.html) where every point links back to a page and line |

All three share one record shape (`shared/schema/record.schema.json`), one
store (`src/mueser/maps/db.py`), one resolver (`src/mueser/maps/reconcile.py`)
and one viewer template (`src/mueser/maps/web/map-template.html`). Ben's own
spreadsheet goes through `01` unchanged: `python -m mueser.maps.load table
<file> --name-col <column> …`.

## How resolution works, in one paragraph

A name is sent to each gazetteer. Each returns candidates with a score
(exact name match 1.0; alias match; a penalty for non-settlements and for
places outside the project's region), coordinates, type, time span and
population when known. `reconcile.decide()` accepts automatically only when a
candidate is far ahead, or when all high-scoring candidates agree on one
location, or when one same-name place is at least ten times more populous
than the next (and says so). Everything else is `unresolved` and sits in
`review.csv` with every candidate; a person writes the chosen URI in
`your_choice` and reruns, and the record becomes `reviewed`. Every HTTP
response is cached under `cache/`, so a rerun is free and the evidence for
every decision is on disk.
