# Operations

The exact invocations that produced what is in `outputs/`, in order. Run from anywhere; each script changes to the repository root.

| script | step | writes |
|---|---|---|
| `00-collect.sh` | Wikidata by the rules in `inputs/rules.json` | `outputs/timeline/runs/collect-<id>/{nodes,edges,rules,summary}.json`, `run.json` |
| `01-sources.sh` | SEP entry metadata, Wikipedia extracts | `outputs/timeline/sources/{sep,wikipedia}.json`, `run.json` |
| `02-connect.sh` | model proposals, thinker to event | `outputs/timeline/proposals/connect-<id>/proposals.json`, `run.json` |
| `03-db.sh` | the database and the page's JSON | `outputs/timeline/timeline.sqlite`, `timeline.json`, `run.json` |
| `04-build.sh` | the page | `outputs/index.html`, `outputs/timeline/builds/<data_id>/run.json` |
| `05-serve.sh [name]` | the local server | appends to `outputs/timeline/log.jsonl` |

`python -m mueser.timeline ingest` appends exported browser logs from `outputs/timeline/inbox/`; `python -m mueser.timeline query --case … "SELECT …"` runs SQL against the database.
