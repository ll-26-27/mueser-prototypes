# Places to map: summary

**Purpose.** Show that a table of historical place names can be placed on a
map with every decision recorded and every doubt kept visible.

**Workflow.** CSV → records → three keyless gazetteers → a decision rule
with thresholds → DuckDB → GeoJSON and SQLite → a single-file map and a
Datasette site.

**Findings.** 21 of 24 names resolved automatically, 9 by agreement between
sources and 12 by a population tie-break that the map panel flags for
checking; 3 ambiguous names (Halle, Neustadt, Stettin) wait in `review.csv`.
GOV answers with time spans, which no other source does; Wikidata carries
the historical names as aliases.

**Limits.** Coordinates are modern. Dates on the input are exact; a fuzzy
EDTF date would work the same way. One input table, invented.
