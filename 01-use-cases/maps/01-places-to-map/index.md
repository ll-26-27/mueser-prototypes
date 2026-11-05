# Places to map: file guide

- `README.md`, `summary.md`, `CLAUDE.md`.
- `inputs/places.csv`: 24 rows, synthetic.
- `operations/work/`: `01-records.jsonl` (loaded), `records_resolved.jsonl`
  and `.csv`, `review.csv` (every candidate, with a column for a person's
  choice), `decisions.json` (the same, for the map), `run.json`,
  `research.duckdb` (ignored by git; rebuilt by the commands in the README).
- `outputs/index.html`: the map. `outputs/records.geojson`,
  `outputs/unresolved.json`, `outputs/research.db` (SQLite for Datasette).
- `datasette/metadata.yml`: Datasette configuration with the cluster map.
