# Four projects for Ben

Built by the Bok Center Learning Lab, November 2026. Four projects, each a
self-contained group under `01-use-cases/`, all reached from one home page,
all on the same footing: every number traceable to a run, every model
answer a proposal until a person decides, every decision an event in a log.

1. **Reading room** (`transcription/`, built). Old German print and
   handwriting (Fraktur, Kurrent) read by nine readers, measured against
   known text, merged into one reading with the doubtful spans marked, and
   put beside the scan with its translation, where you settle the doubts,
   ask questions and copy passages with their citations.
2. **Timeline** (`timeline/`, built, first version). Thinkers, works,
   events, periods and concepts from Wikidata by written rules, every node
   linked to the Stanford Encyclopedia, Britannica, the ODNB and the rest,
   on one band of years, with layers for how thinkers connect, how events
   connect and where the two meet; a model's proposed connections wait for
   your accept or reject.
3. **Style** (`style/`, scoped): handouts normed to a house style, the CV
   extended without changing its page geometry, a book's footnotes checked
   against its bibliography with nothing guessed.
4. **Notes** (`notes/`, scoped): email, voice memos, files, PDF highlights
   and Zotero items into one local database, reviewed by project and theme.

Before these, the **maps** group put the places a source names on a map
through the historical gazetteers; it stays as earlier work.

## Open these first

Open **[index.html](index.html)** in a browser for the four-project gateway.
Each project has an overview, its current status and a workflow diagram.
[How it works](how-it-works.html) shows the desktop app, local folder and
model calls; [Methods & experiments](experiments.html) keeps the detailed
pipelines and evidence from the earlier homepage.

| page | what you see |
|---|---|
| [Reading room](01-use-cases/transcription/04-reading-room/outputs/index.html) | a page beside its scan: the settled text with the readers' doubts marked, the translation in register, every selection lit on the image; your decisions and questions kept in a log |
| [Timeline](01-use-cases/timeline/01-thinkers-and-events/outputs/index.html) | a thinker, work, event or concept with the periods and events of its time above, what came before it on the left, what it touched on the right, its references and citations in the middle; the model's proposed connections to accept or reject |
| [Fraktur print explorer](01-use-cases/transcription/01-fraktur-print-bakeoff/outputs/index.html) | each page beside every reader's text, with the differences from the known text marked, and the cost and time of each |
| [Fraktur consensus](01-use-cases/transcription/01-fraktur-print-bakeoff/outputs/consensus/index.html) | how far the readers agree, which are reliable, and the spans a person should check |
| [Kurrent explorer](01-use-cases/transcription/02-kurrent-handwriting/outputs/index.html) · [consensus](01-use-cases/transcription/02-kurrent-handwriting/outputs/consensus/index.html) | the same for handwriting |
| [Layout overlay](01-use-cases/transcription/03-layout-and-hybrid/outputs/layout.html) | what a vision model sees on a page (headings, stamps, corrections, a later hand) beside an OCR engine's line segmentation |
| [Places map](01-use-cases/maps/01-places-to-map/outputs/index.html) | 24 names from a 1786 route; click a point for every candidate the gazetteers offered and the reason one was chosen |
| [Page-to-map](01-use-cases/maps/03-from-page-to-map/outputs/index.html) | places read off transcribed pages, each point linked to its page and line |
| [Map data](01-use-cases/maps/04-from-map-data/outputs/index.html) | 1,715 places around Breslau from a gazetteer extract; drag the years across 1945 |

Each use case folder has a `README.md` that says what ran and what it
found; [`01-use-cases/README.md`](01-use-cases/README.md) lists them all,
and the group READMEs ([transcription](01-use-cases/transcription/README.md),
[timeline](01-use-cases/timeline/README.md), [style](01-use-cases/style/README.md),
[notes](01-use-cases/notes/README.md), [maps](01-use-cases/maps/README.md))
say what each group is for.

## What the runs found

| | result |
|---|---|
| **Print** | On real Fraktur pages (1812, 1853) the Gemini models read at one wrong character in sixty to a hundred; the free Kraken engine at one in thirty; the best Tesseract model at one in eleven to fourteen. On an Antiqua page Kraken is best. Four vision models on eight pages cost $0.23. |
| **Handwriting** | On a clean 1864 secretary hand Gemini reads at one wrong character in seventeen where Kraken has one in five; on a fast 1896 private hand one in six where everything else is one in two or worse. A photographed 1901 album defeats every reader. |
| **Consensus** | Without any known text, a reader's agreement with the other readers ranks the readers the same way the known text does, so the method carries over to pages nobody has transcribed. |
| **Timeline** | See [its README](01-use-cases/timeline/01-thinkers-and-events/README.md) for the counts: how many people, works, events and concepts the rules admitted, how many connections the record holds, how many the model proposed and how many of those quote their extract verbatim. |
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
| [`01-use-cases/`](01-use-cases/README.md) | the four projects and the earlier maps work, as worked examples and briefs |
| [`02-your-project/`](02-your-project/README.md) | your workspace |
| [`context/`](context/README.md) | the tools, what they were checked against, the open questions about your sources, and the original scoping note |
| [`context/roadmap.md`](context/roadmap.md) | the four projects agreed in November 2026, where each lives, its status, and what each needs from you |
| [`resources/`](resources/README.md) | accounts and keys; a glossary; the Learning Lab handouts |
| `src/mueser/` | the code the use cases run |
| `cache/` | every gazetteer and model reply, kept so reruns are free and the evidence stays |

The gateway pages are generated with `python3 scripts/build_gateway.py`;
shared styling is in `assets/gateway.css`. Diagrams use the bundled Mermaid
10.9.3 distribution (MIT license in `assets/vendor/mermaid-LICENSE`) so they
render when opened from disk without a network connection. The report UI
refresh command preserves the gateway.
