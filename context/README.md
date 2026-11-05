# Context

Background for the two halves of this repository: what the tools are, what
they were checked against, and what is still unknown about Ben's sources.
The use cases cite this folder rather than repeating it.

## The transcription landscape (checked 4 November 2026)

| Tool | What it is | How it is used here |
|---|---|---|
| **Tesseract 5** with `frak2021`, `deu_latf`, `script/Fraktur`, `deu_frak` | The standard open OCR engine; `frak2021` is UB Mannheim's model trained on GT4HistOCR, the reference corpus of historical German print | Fraktur print baseline. Returns line boxes and confidences. No cost, runs on a laptop. |
| **Kraken** (the engine inside eScriptorium) | Open OCR/HTR with layout segmentation; models on Zenodo (`german_print`, `german_handwriting`, `german_handwriting_kurrent_v3`) | Second baseline; also the segmenter for the hybrid mode where it draws the lines and a vision model reads them. Cannot hallucinate text it was not trained to see. |
| **Transkribus** (READ-COOP) | Hosted HTR with a GUI for correction and training; the largest public German Kurrent models | The reference point. Free plan: 50 pages/month in the app; API only on Scholar (€99/year). Backend is a documented stub until then. |
| **Vision-language models** through OpenRouter: Qwen3-VL, Gemini 2.5 Flash, Claude Haiku 5.5, GPT-5 mini | General models that read an image and write text | Asked for diplomatic JSON line arrays at temperature 0. Risk: they normalise silently and fill gaps from memory, which is why CER is reported raw and normalised and why the prompt forbids "fixing". |
| **Mistral OCR** (`mistral-ocr-latest`) | A dedicated document-OCR endpoint, $4 per 1,000 pages | Called directly (not a chat model). Returns Markdown. |
| **CHURRO** (Stanford OVAL, 2025) | A 3B open vision model trained on historical documents | Needs a GPU host (FASRC). Stub. |
| **OCR4all, OCR-D, Calamari** | Workflow systems for historical print | Noted; not wired. OCR-D's `dinglehopper` is the usual CER tool; this repo computes CER itself so the normalisation is visible. |

**Ground truth.** GT4HistOCR (Zenodo 10.5281/zenodo.1344132, CC BY 4.0) is
the public corpus of historical German print lines; it is one 4 GB tar, so
this repo uses Wikisource proofread pages and Commons transcriptions as
fixtures instead, with the revision ids recorded. Ben's own 20 to 50
hand-corrected pages per material type, exported as PAGE-XML from Transkribus
or eScriptorium into `inputs/gt/`, are what the bake-off should finally be
scored on.

## The maps landscape

| Layer | Tool | Note |
|---|---|---|
| Historical gazetteer, German-speaking world | **GOV** (gov.genealogy.net) | JSON API, no key. Names with time spans (Julian day numbers), administrative membership over time, type codes, population series. First in lookup order. |
| General knowledge graph | **Wikidata** | Historical names live as aliases ("Breslau" on Wrocław). Used through the entity API; the SPARQL endpoint was rate-limited to one request a minute during an outage on 4 November 2026. |
| Historical gazetteer aggregator | **World Historical Gazetteer** | Index search worked without a token with an identifying User-Agent; most endpoints now want a free token. |
| Modern gazetteer with alternate names | **GeoNames** | Free username, web services must be enabled on the account page. |
| Storage | **DuckDB** (+ SQLite export) | One file, no server. |
| Browse | **Datasette** + `datasette-cluster-map` | Searchable website with a map from the SQLite export. |
| Web map | **MapLibre GL JS** on OpenFreeMap tiles | Keyless. Single file with the data inline. |
| Historical map overlay | **Allmaps** | Georeferenced IIIF scans as a layer; the default overlay is a sheet of the *Historischer Atlas von Berlin* (ZLB). Find more with `https://api.allmaps.org/maps?intersects=<lon>,<lat>`. |
| Desktop GIS | **QGIS** | Opens the GeoJSON export. |
| Noted, not wired | Recogito / Peripleo (Pelagios), nodegoat | Annotation and no-code alternatives. |

## What is not known about the sources

From the scoping note (see `HANDOFF.md` §9): centuries, page counts, print
versus handwriting split; diplomatic edition versus searchable text; whether
the sources are already digitised (IIIF?) and by which library; what "map
data" means (points from texts, historical maps, existing datasets); who
corrects output and in which interface; licensing limits on sending images
to commercial APIs. The configuration hooks for each are in place
(`ingest iiif`, `--mode print|hand`, the record schema's `iiif_canvas`
field, the `.env` keys).
