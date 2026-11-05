# HANDOFF — Faculty research prototypes: German text transcription + maps/data

*The scoping note this repository was built from, kept verbatim below (4 November 2026). Paths and tools were adjusted during the build; see `README.md` for what exists.*

---

**Owner:** Cat (Bok Center Learning Lab)
**Status:** Scoping done. Accounts are being set up. Build the scaffold and the first working slices now; stub everything that needs a credential that isn't there yet.
**Audience:** a coding agent (CLI) setting up and building this repo.

---

## 1. Context

One faculty member, two research needs:

1. **Text:** transcribe old German sources for research:
   - **printed** material (mostly **Fraktur**, possibly Antiqua), and
   - **handwritten** material (**Kurrent / Sütterlin**, possibly earlier hands).
2. **Maps/data:** "work with databases and map data" for research. This is still vague. Build flexible infrastructure that supports three likely modes:
   - A. structured records that contain places → database → map
   - B. historical place names (including ones extracted from the transcriptions) → gazetteer lookup → coordinates
   - C. historical maps as data (georeferencing IIIF map scans)

The two halves connect: transcriptions yield names, places and dates → those become records → the records get mapped. Design one shared record schema so output from `text/` flows into `maps/` without glue code.

Not yet known (do **not** block on these; leave config hooks): date range and volume of the sources, print vs. handwriting ratio, whether they want a diplomatic edition or searchable content, whether the sources are already digitized as IIIF, and what "map data" means to them.

---

## 2. Repo layout

Create one repo with this structure:

```
.
├── README.md                  # human overview + quickstart for both halves
├── HANDOFF.md                 # this file
├── pyproject.toml             # uv-managed; optional dependency groups per half
├── .env.example               # every key/URL below, empty
├── shared/
│   ├── schema/
│   │   ├── record.schema.json # the shared record (see §5)
│   │   └── README.md
│   └── py/shared/             # tiny package: Record model (pydantic), IO helpers
├── text/                      # TRANSCRIPTION half
│   ├── README.md
│   ├── data/
│   │   ├── raw/               # page images (gitignored)
│   │   ├── gt/                # hand-corrected ground truth (PAGE-XML + txt)
│   │   └── out/               # backend outputs, one folder per backend/run
│   ├── src/text/
│   │   ├── ingest.py          # local images + IIIF manifest download
│   │   ├── backends/
│   │   │   ├── base.py        # Backend interface
│   │   │   ├── tesseract.py   # Fraktur print baseline
│   │   │   ├── kraken.py      # local HTR/OCR (segmentation + recognition)
│   │   │   ├── openrouter.py  # VLMs: Gemini / Claude / GPT / Qwen3-VL
│   │   │   ├── mistral_ocr.py # Mistral /v1/ocr (direct API)
│   │   │   ├── transkribus.py # stub until account exists
│   │   │   └── churro.py      # local HF/vLLM, GPU-only, stub OK
│   │   ├── formats.py         # PAGE-XML / ALTO read+write, plaintext, TEI export
│   │   ├── evaluate.py        # CER/WER vs gt/ (dinglehopper or jiwer)
│   │   ├── bakeoff.py         # run N backends on same pages → comparison table
│   │   ├── extract.py         # NER: people/places/dates → shared Records
│   │   └── finetune/          # LATER (phase T4): Qwen-VL LoRA data prep + config
│   └── tests/
└── maps/                      # DATABASE + MAP half
    ├── README.md
    ├── data/
    │   ├── raw/               # incoming CSV/XLSX/GeoJSON (gitignored if large)
    │   └── db/                # research.duckdb / research.sqlite (gitignored)
    ├── src/maps/
    │   ├── load.py            # CSV/XLSX/GeoJSON/shared Records → DB
    │   ├── db.py              # DuckDB + spatial ext; SQLite export for Datasette
    │   ├── gazetteer/
    │   │   ├── base.py        # Resolver interface: name (+context) → candidates
    │   │   ├── gov.py         # GOV (Genealogisches Ortsverzeichnis), historical German places
    │   │   ├── wikidata.py    # SPARQL
    │   │   ├── geonames.py    # needs username
    │   │   └── whg.py         # World Historical Gazetteer
    │   ├── reconcile.py       # pick or flag candidates; keep confidence and review status
    │   └── export.py          # GeoJSON out, for web map + QGIS
    ├── web/
    │   ├── index.html         # single-file MapLibre GL viewer (points + filters + time slider)
    │   └── allmaps.md         # how to overlay georeferenced historical maps (Allmaps)
    ├── datasette/
    │   └── metadata.yml       # Datasette config + datasette-cluster-map
    └── tests/
```

Gitignore images, DBs, model weights and `.env`. Commit small sample fixtures under `*/tests/fixtures/`.

---

## 3. `text/` — transcription

### 3.1 Tools, ranked by role

| Role | Tool | Notes |
|---|---|---|
| Hosted HTR/OCR with a GUI (likely what the faculty member ends up using) | **Transkribus** (READ-COOP) | Large German models: "Text Titan", "German Genius", plus Kurrent-specific models (e.g. Transkribus German Kurrent, Early Kurrent Emperor for 16th–early 19th c.). Has an API; exports PAGE-XML. Uses paid credits; free tier for testing. **Account pending.** |
| Open-source HTR platform | **eScriptorium + Kraken** | Kraken = engine (`pip install kraken`), eScriptorium = web UI for correction and training. Cat may self-host eScriptorium with Docker later. Models live on Zenodo (`ocr_models` community). |
| Fraktur print baseline | **Tesseract** + UB Mannheim Fraktur models (GT4HistOCR-trained, e.g. `frak2021`) | Cheap, local, good on 19th–20th c. print. |
| Historical-print workflows | **OCR4all**, **OCR-D**, **Calamari** | Note them in the README as options; no backend needed unless the bake-off shows a gap. |
| VLMs | via **OpenRouter**: Gemini, Claude, GPT, **Qwen3-VL** (`qwen/qwen3-vl-8b-instruct`, `qwen/qwen3-vl-30b-a3b-instruct`, `qwen/qwen3-vl-235b-a22b-instruct`) | One OpenAI-compatible client. Qwen3-VL supports JSON-schema structured output; use it to get line arrays back. **Risk: silent normalization or hallucination.** |
| Dedicated OCR API | **Mistral OCR** (`mistral-ocr-latest`, own `/v1/ocr` endpoint) | Not a chat model, so call Mistral directly, not through OpenRouter. |
| Open historical VLM | **CHURRO** (Stanford, 3B, github.com/stanford-oval/Churro) | Not on OpenRouter. Run locally with HF Transformers or vLLM on a GPU (FASRC). Stub if no GPU. |

### 3.2 Backend interface

```python
class Backend(Protocol):
    name: str
    def transcribe(self, image_path: Path, *, mode: Literal["print","hand"], lang: str = "de") -> PageResult: ...

@dataclass
class PageResult:
    page_id: str
    lines: list[Line]          # Line(text, bbox|None, baseline|None, confidence|None)
    raw: dict                  # untouched backend response, for debugging
    backend: str
    model: str
    cost_usd: float | None
```

- Backends that segment (Kraken, Transkribus, Tesseract) return bboxes. VLM backends return `bbox=None`.
- **Hybrid mode (important):** `kraken.segment()` → crop lines → send each crop to any recognition backend (VLM or Kraken). This keeps coordinates and PAGE-XML while letting VLMs do the reading.
- Every run writes `text/data/out/<backend>/<model>/<run_id>/` with PAGE-XML, `.txt` and `run.json` (params, cost, timings).

### 3.3 VLM prompt rules (for `openrouter.py` and `mistral_ocr.py` post-processing)

- Transcribe **diplomatically**: keep original spelling, ſ (long s), abbreviations as written, superscript-e umlauts as marked, and line breaks. No modernizing, no translating, no "fixing".
- Mark unreadable text as `[...]` and uncertain readings as `[?word]`.
- Ask for structured JSON: `{"lines": [{"text": "..."}]}`. Temperature 0.
- Keep the prompt in `text/src/text/backends/prompts/transcribe_de.md` so it can be edited without touching code.
- Optional second pass ("normalize"): an LLM writes a normalized layer **next to** the diplomatic one, never replacing it.

### 3.4 Evaluation

- `evaluate.py`: character error rate (CER) and word error rate (WER) per page and per backend against `text/data/gt/`. Use **dinglehopper** (OCR-D) if it installs cleanly; fall back to `jiwer`.
- Report CER both raw and after a configurable normalization (ſ→s, collapse whitespace), so a VLM that normalizes isn't unfairly penalized or rewarded.
- `bakeoff.py` → `text/data/out/bakeoff_<date>.csv` + a small HTML table: backend, model, CER, WER, cost per page, seconds per page.
- Ground truth: Cat will hand-correct 20–50 pages per material type (print / hand), probably in Transkribus or eScriptorium, and export PAGE-XML into `gt/`. Until then, use a public sample (e.g. a few GT4HistOCR lines) as a fixture so the pipeline runs end to end.

### 3.5 Extraction (bridge to maps)

`extract.py`: take transcriptions → find person / place / date / organization mentions → emit shared `Record`s (§5) with `source_page`, `line_index` and the verbatim `surface_form`.
- Backend A: historical German NER (dbmdz hmBERT-family models through HF/Flair).
- Backend B: LLM with JSON schema through OpenRouter.
- Always keep the verbatim form plus a normalized form. Never drop the link back to the page and line.

### 3.6 Fine-tuning (phase T4 — only if the bake-off shows a gap)

- Goal: QLoRA fine-tune of a Qwen-VL model (8B or smaller; or start from CHURRO) on **line-level** image→text pairs taken from PAGE-XML ground truth.
- Data prep script: PAGE-XML + page image → line crops + `train.jsonl` (`{"image": "...png", "text": "..."}`), split by **document** (not by line) to avoid leaks.
- Trainer: Unsloth (preferred) or HF TRL / LLaMA-Factory. Run on FASRC GPU, not in this sandbox.
- Compare against a **fine-tuned Kraken** model on the same data; it's the cheaper baseline and can't hallucinate.
- Serve the result with vLLM as a `Backend`. OpenRouter cannot serve custom fine-tunes.

---

## 4. `maps/` — database + maps

### 4.1 Stack

| Layer | Choice | Why |
|---|---|---|
| Storage | **DuckDB + spatial extension** (primary), **SQLite/SpatiaLite** export | Single file, no server, works on a faculty laptop. PostGIS only if it later becomes multi-user. |
| Python | **GeoPandas**, **Shapely**, **pyproj**, pandas | Standard. |
| Browse/share | **Datasette** + `datasette-cluster-map` | Instant searchable website with a map from SQLite. Best "show the faculty member their data" tool. |
| Web map | **MapLibre GL JS** single-file `web/index.html` reading `export/*.geojson` | Free, no token. Leaflet is fine as an alternative. |
| Desktop GIS | **QGIS** | Just make sure exports open cleanly (GeoJSON / GeoPackage). |
| Historical maps | **Allmaps** (IIIF Georeference Annotations; `@allmaps/maplibre` or `@allmaps/leaflet` plugin) | Georeference any IIIF map scan in the browser; overlay it as a layer. Harvard Library maps are IIIF. Allmaps overlays are for display; use GeoTIFF for GIS analysis. |
| Annotation (optional) | **Recogito / Peripleo** (Pelagios) | Note in README only. |
| No-code alternative (optional) | **nodegoat** | Note in README only. |

### 4.2 Gazetteer reconciliation

Resolver interface: `resolve(name: str, context: dict) -> list[Candidate(uri, label, lat, lon, source, score, valid_from, valid_to)]`.

Order of lookup for German historical places:
1. **GOV** (gov.genealogy.net): historical German places with administrative changes over time. Highest priority for this project.
2. **Wikidata** (SPARQL; no key).
3. **World Historical Gazetteer**.
4. **GeoNames** (needs a free username in `.env`).

`reconcile.py`: auto-accept when one candidate is far ahead (configurable threshold) and otherwise write it to a `review` table with all candidates. Never silently pick. Store `resolution_status ∈ {auto, reviewed, unresolved}`. Cache every API response on disk; these services are rate-limited.

### 4.3 Web map (`web/index.html`)

Single file. MapLibre GL, OSM/OpenFreeMap-style free basemap, points from GeoJSON, clustering, a popup that shows `surface_form` + source citation (+ link to the page image if available), a filter by record type, and a **time slider** on `date_start`/`date_end`. Include a toggle for one Allmaps historical-map overlay. Get the annotation URL from config, with a documented placeholder.

---

## 5. Shared record schema (`shared/schema/record.schema.json`)

Minimum fields:

```json
{
  "id": "string (stable hash)",
  "type": "place | person | event | org | other",
  "surface_form": "verbatim text as in source",
  "normalized": "string|null",
  "source": {
    "doc_id": "string",
    "page_id": "string",
    "line_index": "int|null",
    "bbox": "[x,y,w,h]|null",
    "iiif_canvas": "uri|null",
    "transcription_backend": "string|null"
  },
  "date_start": "ISO-8601 or EDTF string|null",
  "date_end": "ISO-8601 or EDTF string|null",
  "place_uri": "GOV/Wikidata/WHG/GeoNames URI|null",
  "lat": "float|null",
  "lon": "float|null",
  "resolution_status": "auto | reviewed | unresolved",
  "confidence": "float|null",
  "notes": "string|null"
}
```

Use EDTF-tolerant date strings (historical dates are often fuzzy: `1743~`, `174X`). Store them as text, and derive sortable start and end years in separate columns.

---

## 6. Credentials (`.env.example`) — accounts are being set up

```
OPENROUTER_API_KEY=
MISTRAL_API_KEY=
TRANSKRIBUS_USER=
TRANSKRIBUS_PASSWORD=
ESCRIPTORIUM_URL=
ESCRIPTORIUM_TOKEN=
GEONAMES_USERNAME=
HF_TOKEN=
```

Every backend or resolver whose credentials are missing must **skip with a clear message**, not crash. `bakeoff.py` should list which backends ran and which were skipped.

---

## 7. Build order + done criteria

**Phase 0 — scaffold**
- [ ] Repo layout above, `uv` project, optional-dependency groups `[text]`, `[maps]`, `[gpu]`, ruff, pytest, `.env.example`, `.gitignore`.
- [ ] `shared` Record model + JSON Schema + round-trip test.
- Done when: `uv run pytest` passes on a fresh clone.

**Phase T1 — text pipeline end to end, no paid services**
- [ ] `ingest.py` (local folder + IIIF manifest → images).
- [ ] Tesseract Fraktur backend + Kraken backend (default public models).
- [ ] PAGE-XML writer/reader; `evaluate.py` with fixture ground truth.
- Done when: `uv run python -m text.bakeoff --pages tests/fixtures --backends tesseract,kraken` produces a CSV with CER.

**Phase T2 — VLM + hosted backends**
- [ ] OpenRouter backend (model is configurable; test with one Qwen3-VL and one frontier model), hybrid Kraken-segment + VLM-recognize mode.
- [ ] Mistral OCR backend.
- [ ] Transkribus + eScriptorium backends: implement against their APIs if the credentials exist; otherwise leave well-documented stubs.
- Done when: the bake-off compares ≥4 backends on the same pages, with cost per page.

**Phase M1 — maps pipeline**
- [ ] `load.py` (CSV/GeoJSON/Records → DuckDB), `export.py` (GeoJSON, SQLite).
- [ ] Gazetteer resolvers (GOV + Wikidata first) with disk cache + review table.
- [ ] Datasette config with cluster map; `web/index.html` MapLibre viewer with time slider.
- Done when: a sample CSV of ~20 historical German place names → resolved → visible in Datasette and in the web map.

**Phase B1 — bridge**
- [ ] `text/extract.py` → Records → `maps/load.py` → map. A demo notebook or script that runs transcribed page → places on a map.

**Phase T4 — fine-tune (only if justified by bake-off)** — see §3.6.

---

## 8. Conventions

- Python 3.11+, `uv`, type hints, pydantic for data models, `typer` CLIs (`python -m text.bakeoff`, `python -m maps.load`).
- Make every expensive call cacheable and idempotent: cache keyed by (backend, model, prompt hash, image hash).
- Never overwrite ground truth; outputs go in timestamped run folders.
- Keep provenance on everything: which backend/model/prompt produced each line and each Record.
- Write both READMEs for a humanist reader: what it does, how to run it, what the numbers mean.

---

## 9. Open questions for the faculty meeting (Cat to fill in)

- Centuries, page counts, print vs. handwriting split?
- Diplomatic edition, normalized reading text, or just searchable content?
- Are sources digitized? IIIF? Which library or archive?
- "Map data": points from texts, historical maps, existing datasets, or all three?
- Who corrects the output, and in which interface (Transkribus vs. eScriptorium)?
- Data sensitivity or licensing limits on sending images to commercial APIs?

---

## 10. References

- Transkribus German models: https://website-beta.transkribus.org/blog/3-ai-models-for-transcribing-german-text-in-fraktur-kurrent-and-sutterlin
- Kraken: https://kraken.re/main/ · eScriptorium docs: https://escriptorium.readthedocs.io/
- CHURRO paper: https://aclanthology.org/anthology-files/pdf/emnlp/2025.emnlp-main.1763.pdf · code: https://github.com/stanford-oval/Churro
- OpenRouter Qwen3-VL: https://openrouter.ai/models/qwen/qwen3-vl-30b-a3b-instruct
- Allmaps: https://allmaps.org/ · IIIF Georeference extension: https://iiif.io/news/2023/05/15/georef-extension-published/
- GOV: https://gov.genealogy.net/ · World Historical Gazetteer: https://whgazetteer.org/
