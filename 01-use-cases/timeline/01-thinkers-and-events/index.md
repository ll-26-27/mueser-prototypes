# Files

| path | what it is |
|---|---|
| `README.md` | what ran, on what, what it produced, what was checked; how to use the page |
| `summary.md` | purpose, workflow, findings, limits, a paragraph each |
| `CLAUDE.md` | rules for a coding assistant in this folder |
| `inputs/rules.json` | the written rule for the node set and the edge properties; copied into every collect run |
| `inputs/README.md` | what the rule controls |
| `operations/00-collect.sh` … `05-serve.sh` | the exact invocations, in order; `operations/README.md` explains each |
| `outputs/index.html` | the page: one self-contained file with the data embedded; opens from disk, saves through `serve` |
| `outputs/timeline/runs/collect-<id>/` | `nodes.json`, `edges.json`, `rules.json`, `summary.json`, `run.json`: one collect run |
| `outputs/timeline/sources/sep.json` | per node with an SEP entry: title, authors, first published, substantive revision, as the entry page states them |
| `outputs/timeline/sources/wikipedia.json` | per node: the lead extract, article, revision id, timestamp, licence |
| `outputs/timeline/proposals/connect-<id>/proposals.json` | per person: the model's proposed connections, each with type, reason, quoted evidence, whether the quote was found verbatim; `run.json` with model, prompt hash, cost |
| `outputs/timeline/timeline.sqlite` | the database: `nodes`, `node_ids`, `links`, `texts`, `sep_entries`, `citations`, `edges`, `sources`, `meta` |
| `outputs/timeline/timeline.json` | the same, shaped for the page |
| `outputs/timeline/log.jsonl` | every decision, added connection, note and excerpt, append-only |
| `outputs/timeline/inbox/` | exported browser logs waiting for `ingest` |
| `outputs/timeline/builds/<data_id>/run.json` | which data each page build came from |
| `src/mueser/timeline/` | `collect.py`, `wikidata.py`, `sources.py`, `connect.py`, `db.py`, `build.py`, `log.py`, `serve.py`, `__main__.py`, `web/timeline.{html,css,js}` |
| `src/mueser/text/backends/prompts/timeline_connect.md` | the connect prompt |
| `cache/wikidata/`, `cache/sep/`, `cache/wikipedia/`, `cache/openrouter/` | every reply, raw, keyed by request |
| `tests/test_timeline.py`, `tests/test_local_servers.py`, `tests/timeline_queue.test.cjs` | the tests |
