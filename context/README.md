# Context

Background for the two halves of this repository: what the tools are, what
they were checked against, what is still unknown about Ben's sources, and
the scoping note the build started from ([`handoff.md`](handoff.md), with
a list of where the build departed from it).

## The transcription landscape (checked 4 November 2026)

| Tool | What it is | How it is used here |
|---|---|---|
| **Tesseract 5** with `frak2021`, `deu_latf`, `script/Fraktur`, `deu_frak` | The standard open OCR engine; `frak2021` is UB Mannheim's model trained on GT4HistOCR, the reference corpus of historical German print | Fraktur print baseline. Returns line boxes and confidences. No cost, runs on a laptop. |
| **Kraken** (the engine inside eScriptorium) | Open OCR/HTR with layout segmentation; models on Zenodo (`german_print`, `german_handwriting`, `german_handwriting_kurrent_v3`) | Second baseline; also the segmenter for the hybrid mode where it draws the lines and a vision model reads them. Cannot hallucinate text it was not trained to see. |
| **eScriptorium** | The open HTR platform around Kraken: a web GUI for segmentation, correction, training and PAGE-XML export; self-hosted (Docker) or lab-hosted | The place for Ben to correct pages and train on his own lines. The backend drives an instance through its REST API (`escriptorium.py`); skipped until `ESCRIPTORIUM_URL` is set. |
| **Vision-language models** through OpenRouter: Gemini 3.8 Flash and 3.1 Pro, Qwen3-VL 235B, Claude Haiku and Sonnet 5.5 | General models that read an image and write text | Three uses: whole-page reading (JSON line arrays, temperature 0); **hybrid** reading of Kraken's line crops, which keeps coordinates; and a **layout pass** that maps regions, lines, marginalia and later hands without transcribing. Risk: silent normalisation and filling from memory, hence CER raw and normalised, the prompt's ban on "fixing", and the consensus step that shows where readers disagree. |
| **Transkribus** (READ-COOP), **Mistral OCR** | Hosted alternatives | Wired as optional backends; not used. Transkribus's API needs a paid plan; Mistral OCR is a Markdown-returning endpoint at $4 per 1,000 pages. |
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
| Historical map overlay | **Allmaps** | Georeferenced IIIF scans as a layer. No sound sheet was found for the Prussian route (see maps/02), so the overlay ships off; find candidates with `https://api.allmaps.org/maps?intersects=<lon>,<lat>` and check their control points. |
| Desktop GIS | **QGIS** | Opens the GeoJSON export. |
| Noted, not wired | Recogito / Peripleo (Pelagios), nodegoat | Annotation and no-code alternatives. |

## What is not known about the sources

From the scoping note (see `context/handoff.md` §9): centuries, page counts, print
versus handwriting split; diplomatic edition versus searchable text; whether
the sources are already digitised (IIIF?) and by which library; what "map
data" means (points from texts, historical maps, existing datasets); who
corrects output and in which interface; licensing limits on sending images
to commercial APIs. The configuration hooks for each are in place
(`ingest iiif`, `--mode print|hand`, the record schema's `iiif_canvas`
field, the `.env` keys).
