# German sources, transcribed and mapped

**Research prototypes for Ben · Bok Center Learning Lab · November 2026**

Two things a historian of the German-speaking world needs from a computer,
built end to end so the mechanics are visible: **read old German print and
handwriting** (Fraktur, Kurrent) with several engines and measure each one
against known text; and **put the places a source names on a map**, with
every identification traceable to the gazetteer record and the line of the
page it came from.

The shape is the one from the desktop-app workshop: `inputs/` →
`operations/` → `outputs/`, with the folder as the record of the work. What
is different here is the standard. Every number has a run folder behind it,
every model call is cached with its raw reply, every gazetteer choice has a
written reason, and anything a person still has to decide sits in a review
table rather than being guessed.

## Start here

1. Clone and install (Python 3.12, [uv](https://docs.astral.sh/uv/), Tesseract):

   ```sh
   git clone https://github.com/ll-26-27/mueser-prototypes.git && cd mueser-prototypes
   brew install tesseract                      # macOS; apt install tesseract-ocr on Linux
   uv sync --extra text --extra maps --extra dev --extra htr   # drop --extra htr to skip Kraken/PyTorch
   uv run python -m mueser.text.models fetch tesseract
   uv run python -m mueser.text.models fetch fonts
   uv run python -m mueser.text.models fetch kraken
   uv run pytest -q
   ```

2. Open the three explorers by double-clicking them:
   `01-use-cases/transcription/01-fraktur-print-bakeoff/outputs/index.html`,
   `01-use-cases/transcription/02-kurrent-handwriting/outputs/index.html`,
   `01-use-cases/maps/01-places-to-map/outputs/index.html`.
3. Read [`01-use-cases/README.md`](01-use-cases/README.md), then the README
   of whichever example is closest to your material.
4. Keys go in `.env` (copy `.env.example`); see
   [`resources/accounts.md`](resources/accounts.md). Without keys, Tesseract,
   Kraken, GOV, Wikidata and the World Historical Gazetteer all run; with an
   OpenRouter key the vision models (Qwen3-VL, Gemini, Claude) join the
   bake-off.

## What's here

| Folder | Contents |
|---|---|
| [`01-use-cases/`](01-use-cases/README.md) | Five worked examples: two transcription bake-offs, places to a map, a historical-map overlay, and the bridge from page to map. |
| [`02-your-project/`](02-your-project/README.md) | Ben's workspace, with the commands for a folder of images, a IIIF manifest, a spreadsheet of places, or transcriptions to places. |
| [`src/mueser/`](src/mueser/) | The package the operations call: `text` (ingest, backends, formats, evaluate, bake-off, extract, report), `maps` (load, gazetteers, reconcile, db, export, map), `shared` (record model, cache, runs, OpenRouter client). |
| [`shared/schema/`](shared/README.md) | The one record shape both halves use. |
| [`context/`](context/README.md) | The tool landscape as checked on 4 November 2026, and what is still unknown about the sources. |
| [`resources/`](resources/README.md) | Accounts and keys; the Learning Lab glossary and handouts. |
| [`HANDOFF.md`](HANDOFF.md) | The scoping note this was built from, verbatim. |
| `cache/` | Every gazetteer and model response, keyed by request; reruns are free and the evidence stays. |

## What the first runs found

- **Print.** On three real Fraktur pages (1796, 1812, 1853) Kraken's
  `german_print` model reads with a normalised character error rate of
  0.015 to 0.034; the best Tesseract model, `frak2021`, 0.026 to 0.093. On
  synthetic pages the order reverses, which is why synthetic scores are an
  upper bound.
- **Handwriting.** The open Kraken handwriting model reads a clean 1864
  secretary's hand at CER 0.21 and a photographed 1901 album at 0.82. That
  is the baseline Transkribus and the vision models have to beat; neither
  has run yet.
- **Places.** 21 of 24 ledger names resolved automatically against GOV,
  Wikidata and WHG, each with a reason; three ambiguous ones (Halle,
  Neustadt, Stettin) wait in a review table. From OCR text, 36 of 56 names;
  what stays open is rivers, regions, buildings and city quarters.
- **Historical maps.** The Allmaps index returned 4,200 georeferenced
  sheets for the route and none at a usable scale with sound control points,
  so the overlay ships off, with the table that shows why.

## Conventions

Python 3.11+, `uv`, pydantic models, `typer` commands run from the repo
root as `uv run python -m mueser.<half>.<step>`. Outputs go to timestamped
run folders and are never overwritten. Synthetic material is labelled
synthetic wherever it appears. See [`CLAUDE.md`](CLAUDE.md) for the rules a
coding assistant follows in this repository.
