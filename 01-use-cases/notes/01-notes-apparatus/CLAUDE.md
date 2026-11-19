# CLAUDE.md — Notes apparatus

Read the repository `CLAUDE.md` first. `HANDOFF.md` is the brief;
`README.md` says what exists. The reading room (`src/mueser/reading/`)
defines the log-and-serve pattern used here; reuse its `log.py` and
`serve.py` shapes. In this folder:

- **The raw file is copied once and never modified.**
  `outputs/store/raw/<sha256>` is immutable; the inbox is never moved or
  deleted from.
- **The item text is whole.** No field is truncated, sampled or summarised
  in place. A summary is a separate proposal that says what it is.
- **Everything a model says is a proposal** until a person accepts it in
  the log or a rule named in `inputs/config/rules.yml` accepts it and is
  recorded on the row. Controlled lists (`projects.yml`, `themes.yml`) grow
  only by accepted proposals.
- **The log is the record.** `outputs/store/log.jsonl` is append-only;
  `apply` derives statuses and tags from it; the database can be rebuilt
  from the raw store plus the log.
- **Private never leaves the machine.** An item marked `private`, by
  folder or by rule, is never sent to a model. `--no-model` sends nothing.
- **Provenance on derived text.** Transcripts, cleanups, summaries and
  tags carry engine or model, prompt hash and cache key.
- **Connections come from candidates.** A model ranks connections only
  among the deterministic candidates it was given; it cannot invent an id.
- **Local first for audio.** Whisper on the machine by default; a hosted
  model only when asked for by flag.
- **Private material stays out of git.** `inputs/inbox/`, `outputs/store/`,
  `outputs/exports/`, `outputs/inbox/` and `*.sqlite` are ignored by the
  root `.gitignore`. Fixtures are synthetic and named `synth-*`.
- **Missing credentials skip, they do not crash.**
- Test events must not stay in the log: exercise the page under a name
  that is not Ben's and remove them before handing over.

Commands, from the repository root
(`--case 01-use-cases/notes/01-notes-apparatus`):

```sh
uv run python -m mueser.notes ingest --case … [--only email|voice|text|pdf|zotero] [--engine openrouter] [--zotero-local]
uv run python -m mueser.notes enrich --case … [--since …] [--no-model] [--model …]
uv run python -m mueser.notes build  --case …
uv run python -m mueser.notes serve  --case … [--who ben] [--port 8766]
uv run python -m mueser.notes apply  --case …
uv run python -m mueser.notes export --case … --project <id> [--since …] --out …/outputs/exports/
uv run python -m mueser.notes log    --case … [ingest]
```
