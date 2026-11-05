# Working in this repository

This is a research prototype for one faculty member (Ben) with two needs:
transcribing old German sources in Fraktur print and Kurrent handwriting, and
putting the places those sources name on a map. It is built by the Bok
Center Learning Lab to show the prototype and to teach how it works, and it
has to be **defensible and auditable**: every number, line and point must be
traceable to the input, the method and the model that produced it.

## Rules that keep it auditable

- **Provenance on everything.** A transcription line carries its backend,
  model and prompt hash; a record carries its page and line; a map point
  carries the gazetteer candidate it was resolved to and why. Never strip a
  provenance field to make a table shorter.
- **Keep the raw response.** Every API call is cached on disk with the raw
  reply (`cache/`). Reruns are free, and a result can be re-examined without
  re-calling the service. Do not delete the cache to "clean up".
- **Never overwrite.** Outputs go in timestamped run folders with a
  `run.json` (parameters, cost, timings, git commit). Ground truth in
  `inputs/gt/` is never written by a backend.
- **Never silently pick.** Gazetteer resolution auto-accepts only under a
  recorded rule (threshold, margin, agreement, or a population tie-break that
  names both populations); everything else goes to `review.csv` for a
  person. `resolution_status` is always `auto`, `reviewed` or `unresolved`.
- **Diplomatic transcription.** Keep ſ, old spelling, abbreviations and line
  breaks. A normalised layer may sit beside the diplomatic one, never replace
  it. Mark gaps `[...]` and doubts `[?word]`. Never fill from memory.
- **Report CER both raw and normalised**, and say what the normalisation is.
- **Missing credentials skip, they do not crash.** A run lists which backends
  ran and which were skipped, with the reason.
- **Synthetic data is labelled synthetic.** The 1786 travel journal and
  letters are invented; say so wherever they appear. Scores on synthetic pages
  are upper bounds, not findings about real sources.

## Editorial voice

- Write directly: what ran, on what, by which model, what it produced, what
  was checked. A method note is a record, not an apology.
- Replace generic warnings with specific information: "CER 0.012 on five
  synthetic pages, 0.18 on the 1853 newspaper page", "21 of 24 names
  auto-resolved, 3 in review".
- Explain mechanics where they explain a decision: why Tesseract returns
  boxes and a vision model does not, why `Neustadt` cannot be resolved from
  the name alone, what a Julian day is doing in a gazetteer record.
- No reassurance about AI use, no "responsible use" boxes, no accusations
  denied in advance.

## Layout

- `01-use-cases/transcription/` and `01-use-cases/maps/`: worked examples,
  each with `inputs/`, `operations/` (numbered steps), `outputs/`
  (`index.html` is the explorer), `README.md`, `summary.md`, `index.md`.
- `src/mueser/`: the package the operations call (`text`, `maps`, `shared`).
- `shared/schema/record.schema.json`: the one data shape both halves use.
- `02-your-project/`: Ben's workspace. `context/`: background notes.
- `models/` and `cache/` are local; `.env` holds keys and is ignored by git.

## Commands

```sh
uv sync --extra text --extra maps --extra dev        # add --extra htr for kraken
uv run pytest -q
uv run python -m mueser.text.bakeoff run --help
uv run python -m mueser.maps.resolve run --help
```

Run everything from the repository root.
