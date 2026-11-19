# CLAUDE.md — Timeline: thinkers and events

Read the repository `CLAUDE.md` first. `README.md` here says what ran and
what the page does; `index.md` lists the files. In this folder:

- **The node set is a rule, not a choice.** `inputs/rules.json` says who
  and what is in: every person with a Stanford or Internet Encyclopedia of
  Philosophy entry, one hop of influence above a sitelink threshold, their
  works, the event and period classes with their thresholds, the concepts
  and movements. Change the rule, rerun `collect`, record it; never add or
  remove a node by hand.
- **Every edge names its source.** `wikidata:P737` for a statement,
  `model:<model>` for a proposal, `person:<name>` for one added in the
  page. A proposal carries the sentence of the extract it rests on and
  whether that sentence was found verbatim; it is `proposed` until a
  decision in the log says `accepted` or `rejected`. Nothing promotes it
  silently.
- **Perspectives are data.** Whose connections a layer shows (the record,
  the model, the readers) is the `source` prefix of each edge. A new
  perspective, such as the connections one commentator draws in a book,
  is a new source prefix with its own run folder and citations, never a
  rewrite of the recorded edges.
- **Texts are attributed, not claimed.** The overview on a node is the
  Wikipedia lead extract, shown with article, revision and licence; the
  Stanford citation is built from the entry's own metadata. Neither is
  edited. No summary is written by a model.
- **Every reply is cached raw** (`cache/wikidata/`, `cache/sep/`,
  `cache/wikipedia/`, `cache/openrouter/`). A rerun with the same rules
  makes no request. Do not delete the cache to clean up.
- **Never overwrite a run.** `collect` and `connect` write run folders;
  `db` and `build` write the current database and page from named runs
  and record which (`data_id`). The log is append-only.
- **Dates keep their precision.** A year, decade or century on Wikidata
  stays that; the page shows the label, not an invented day.
- **Missing credentials skip.** Without `OPENROUTER_API_KEY`, `connect`
  reports the pass skipped; the page builds without proposals.
- **Test events are not Ben's.** Anything written to `outputs/timeline/log.jsonl`
  while exercising the page is removed afterwards and the README says so.
- **The local servers share `src/mueser/shared/local_http.py`.** Paths
  with a hidden component, encoded or through a symlink, are refused;
  keep that when changing `serve.py`.

Commands, from the repository root (`operations/` has the exact ones):

```sh
uv run python -m mueser.timeline collect  --case 01-use-cases/timeline/01-thinkers-and-events
uv run python -m mueser.timeline sources  --case 01-use-cases/timeline/01-thinkers-and-events
uv run python -m mueser.timeline connect  --case 01-use-cases/timeline/01-thinkers-and-events
uv run python -m mueser.timeline db       --case 01-use-cases/timeline/01-thinkers-and-events
uv run python -m mueser.timeline build    --case 01-use-cases/timeline/01-thinkers-and-events
uv run python -m mueser.timeline serve    --case 01-use-cases/timeline/01-thinkers-and-events --who ben
uv run pytest -q tests/test_timeline.py tests/test_local_servers.py
node --test tests/timeline_queue.test.cjs
```
