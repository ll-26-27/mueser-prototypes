# German sources, transcribed and mapped

Prototypes built for Ben by the Bok Center Learning Lab, November 2026.

Two things this repository does, end to end, with every step open to
inspection:

1. **Reads old German print and handwriting** (Fraktur, Kurrent) with nine
   different readers, from free local engines to the current vision models,
   measures each one against pages whose text is known, and merges them
   into one reading with the doubtful spans marked for you to settle.
2. **Puts the places a source names on a map**, looking each name up in
   the historical gazetteers, recording why each point is where it is, and
   leaving the names it could not settle in a table for you. It also works
   from map data alone, with no text behind it.

## Open these first

Open **`index.html`** in a browser. It is the map of everything here: each
use case as a row of steps, what kind of step each is (code, a lookup, a
model's judgment), and links to the pages below.

| page | what you see |
|---|---|
| [Fraktur print explorer](01-use-cases/transcription/01-fraktur-print-bakeoff/outputs/index.html) | each page beside every reader's text, with the differences from the known text marked, and the cost and time of each |
| [Fraktur consensus](01-use-cases/transcription/01-fraktur-print-bakeoff/outputs/consensus/index.html) | how far the readers agree, which are reliable, and the spans a person should check |
| [Kurrent explorer](01-use-cases/transcription/02-kurrent-handwriting/outputs/index.html) · [consensus](01-use-cases/transcription/02-kurrent-handwriting/outputs/consensus/index.html) | the same for handwriting |
| [Layout overlay](01-use-cases/transcription/03-layout-and-hybrid/outputs/layout.html) | what a vision model sees on a page (headings, stamps, corrections, a later hand) beside an OCR engine's line segmentation |
| [Places map](01-use-cases/maps/01-places-to-map/outputs/index.html) | 24 names from a 1786 route; click a point for every candidate the gazetteers offered and the reason one was chosen |
| [Page-to-map](01-use-cases/maps/03-from-page-to-map/outputs/index.html) | places read off transcribed pages, each point linked to its page and line |
| [Map data](01-use-cases/maps/04-from-map-data/outputs/index.html) | 1,715 places around Breslau from a gazetteer extract; drag the years across 1945 |

Each use case folder has a `README.md` that says what ran and what it
found; [`01-use-cases/README.md`](01-use-cases/README.md) lists them all,
and the two group READMEs ([transcription](01-use-cases/transcription/README.md),
[maps](01-use-cases/maps/README.md)) draw the flow of each.

## What the runs found

| | result |
|---|---|
| **Print** | On real Fraktur pages (1812, 1853) the Gemini models read at one wrong character in sixty to a hundred; the free Kraken engine at one in thirty; the best Tesseract model at one in eleven to fourteen. On an Antiqua page Kraken is best. Four vision models on eight pages cost $0.23. |
| **Handwriting** | On a clean 1864 secretary hand Gemini reads at one wrong character in seventeen where Kraken has one in five; on a fast 1896 private hand one in six where everything else is one in two or worse. A photographed 1901 album defeats every reader. |
| **Consensus** | Without any known text, a reader's agreement with the other readers ranks the readers the same way the known text does, so the method carries over to pages nobody has transcribed. |
| **Layout** | A vision model finds the masthead, the ownership stamp, a pencil page number in a later hand, an interlinear correction, and the Latin-script names inside a Kurrent letter, and counts the lines correctly. |
| **Places** | 21 of 24 names from the 1786 route resolved automatically with a written reason; Halle, Neustadt and Stettin wait for a person. From OCR text, 36 of 56 names. |
| **Historical maps** | Nothing yet sound for Prussia on Allmaps; the folder shows how to georeference a sheet and switch the overlay on. |

## Running it on your own material

```sh
git clone https://github.com/ll-26-27/mueser-prototypes.git && cd mueser-prototypes
brew install tesseract                                       # macOS; apt install tesseract-ocr on Linux
uv sync --extra text --extra maps --extra dev --extra htr     # Python 3.12 and uv; drop --extra htr to skip Kraken
uv run python -m mueser.text.models fetch tesseract
uv run python -m mueser.text.models fetch fonts
uv run python -m mueser.text.models fetch kraken
```

Put an OpenRouter key in `.env` (copy `.env.example`;
[`resources/accounts.md`](resources/accounts.md) explains each service).
Without it, the free engines and the gazetteers still run.

[`02-your-project/README.md`](02-your-project/README.md) has the commands
for a folder of page images, a IIIF manifest from a library, a spreadsheet
of places, or transcriptions to places. The pattern is always the same:
`inputs/` is what you start with, `operations/` what is done to it,
`outputs/` what comes out, and every output folder keeps a `run.json`
saying what ran.

## What's where

| folder | contents |
|---|---|
| [`01-use-cases/`](01-use-cases/README.md) | the seven worked examples |
| [`02-your-project/`](02-your-project/README.md) | your workspace |
| [`context/`](context/README.md) | the tools, what they were checked against, the open questions about your sources, and the original scoping note |
| [`resources/`](resources/README.md) | accounts and keys; a glossary; the Learning Lab handouts |
| `src/mueser/` | the code the use cases run |
| `cache/` | every gazetteer and model reply, kept so reruns are free and the evidence stays |
