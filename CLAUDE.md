# For the coding assistant

*Ben: this file is instructions for Claude Code and other coding assistants
working in the repository. Nothing here is needed to use it.*

A research prototype for one faculty member (Ben): transcribing old German
sources in Fraktur print and Kurrent handwriting, and putting the places
those sources name on a map. It has to be **defensible and auditable**:
every number, line and point must be traceable to the input, the method and
the model that produced it.

## Rules

- **Provenance on everything.** A transcription line carries its backend,
  model and prompt hash; a record carries its page and line; a map point
  carries the gazetteer candidate it was resolved to and the reason. Never
  strip a provenance field to make a table shorter.
- **Keep the raw response.** Every API call is cached on disk with the raw
  reply (`cache/`), trimmed only where a resolver says so in the entry.
  Do not delete the cache to "clean up".
- **Never overwrite.** Outputs go in run folders with a `run.json`. Reuse a
  run id only to redo that run after a fix, and say so. Ground truth in
  `inputs/gt/` is never written by a backend.
- **Never silently pick.** Gazetteer resolution auto-accepts only under a
  recorded rule; everything else goes to `review.csv`. `resolution_status`
  is `auto`, `reviewed` or `unresolved`.
- **Diplomatic transcription.** Keep ſ, old spelling, abbreviations and
  line breaks. A normalised layer sits beside the diplomatic one, never
  replaces it. Gaps are `[...]`, doubts `[?word]`. Never fill from memory.
- **Report CER raw and normalised**, and say what the normalisation is.
- **Consensus is not truth.** The medoid and the check-in list are for a
  person to settle; `compare apply` writes corrected text only from
  recorded decisions.
- **Missing credentials skip, they do not crash.** A model reply without
  JSON is recorded as an error or a `[...]` line, never retried into silence.
- **Synthetic data is labelled synthetic.** Scores on synthetic pages are
  upper bounds, not findings about real sources.

## Voice

Write what ran, on what, by which model, what it produced, what was
checked. Prefer specific figures to general warnings. Explain a mechanism
where it explains a decision. No reassurance about AI use, no "responsible
use" boxes, no accusations denied in advance. Prose for Ben goes in the
READMEs; rules for assistants stay here.

## Layout and commands

- `01-use-cases/{transcription,maps}/<case>/`: `inputs/`, numbered
  `operations/`, `outputs/` (`index.html`, `consensus/`, `runs/`),
  `README.md`, `summary.md`, `index.md`, `CLAUDE.md`.
- `src/mueser/text`: ingest, backends (tesseract, kraken, openrouter,
  hybrid, escriptorium; mistral and transkribus optional), formats,
  evaluate, bakeoff, report, compare, layout, extract, synth, models.
- `src/mueser/maps`: load, gazetteer (gov, wikidata, whg, geonames),
  reconcile, resolve, db, export, build_map, `web/map-template.html`.
- `src/mueser/shared`: record model, cache, runs, env, OpenRouter client.
- `context/handoff.md`: the scoping note, with where the build departed.
- `models/` is local; `cache/` is committed except the Allmaps index;
  `.env` is ignored.

```sh
uv sync --extra text --extra maps --extra dev --extra htr
uv run pytest -q
uv run python -m mueser.text.bakeoff run --help
uv run python -m mueser.text.compare run --help
uv run python -m mueser.maps.resolve run --help
```

Run everything from the repository root.
