# CLAUDE.md — Reading room

Read the repository `CLAUDE.md` first. `HANDOFF.md` is the brief this was
built from; `README.md` says what exists. In this folder:

- `outputs/reading/log.jsonl` is append-only. No command rewrites it and
  no one edits it by hand. A mistake is corrected by a later event; a
  status change is an event that references the issue.
- A build under `outputs/reading/builds/<build_id>/` is immutable.
  `apply` writes a new build; every event records the build it was made
  against. Rerun `settle` with the same id only to redo it after a fix, and
  say so in the README.
- The `diplomatic` text of a line is never edited by any command.
  Decisions produce the `settled` text beside it.
- Translation is a layer beside the transcription, never a replacement.
  When a source line changes, the page marks the translation stale; rerun
  `translate` rather than reusing it.
- Thresholds (`--max-dist`, `--min-divergence`) go in `run.json` with the
  result. Unanchored lines are counted in the README, not hidden.
- The pages and readings in `inputs/` are copies; `inputs/readings/
  provenance.json` says where each came from. Fix provenance in cases
  01–03, not here. `inputs/metadata.json` is hand-written; a document gets
  an entry there before it gets a citation, and a synthetic document
  carries `synthetic: true`.
- Test events must not stay in the log. Exercise the page under a name
  that is not Ben's, and remove the events and any build made from them
  before handing over.

Commands, from the repository root (`--case 01-use-cases/transcription/04-reading-room`):

```sh
uv run python -m mueser.reading settle    --case … [--build-id …] [--max-dist 0.55]
uv run python -m mueser.reading translate --case … [--models a,b] [--min-divergence 0.35]
uv run python -m mueser.reading build     --case … [--translation <run_id>|none]
uv run python -m mueser.reading serve     --case … [--port 8765] [--who name]
uv run python -m mueser.reading apply     --case …      # log -> new build
uv run python -m mueser.reading ingest    --case …      # inbox/*.jsonl -> log
uv run python -m mueser.reading log       --case …
uv run python -m mueser.reading collect   --case … --consensus … --runs … --pages …
uv run python -m mueser.reading init-doc  --pages … --out …/inputs/metadata.json
```
