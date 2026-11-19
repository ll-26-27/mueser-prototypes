# HANDOFF — Reading room: scan, transcription and translation in one page

**Owner:** Madeleine (Bok Center Learning Lab), for Ben
**Status:** Scoped 5 November 2026 after the first meeting with Ben; built 10 November 2026 on the three fixture pages. `README.md` says what exists and what was checked. Departures from this brief: anchoring runs inside `settle` (no separate `anchor` command); the CLI is flat (`settle`, `translate`, `build`, `serve`, `apply`, `ingest`, `log`, `cite`, `collect`, `init-doc`); a `collect` command generalises `operations/00-collect-inputs.py` for new material; a translation run is a sibling of a build, not inside it, and `apply` joins the two; segment verification accepts first and last words that straddle a line end.
**Audience:** a coding agent (CLI) building this use case inside `mueser-prototypes`. Read the repository `CLAUDE.md`, `context/handoff.md` and `context/roadmap.md` first, then `01-use-cases/transcription/README.md` and the README of `03-layout-and-hybrid/`.

---

## 1. Context

The transcription use cases end in an explorer page that shows a scan beside every reader's text and a consensus page that lists the spans a person should check. Ben's reaction was: that is the right material, in the wrong shape for reading. He wants one page per scan where he can **read**, not compare readers, and where what he decides is kept.

What he asked for, in his order:

1. The **scan on the left**. On the right, the **transcription** and the **translation** of the same page, with toggle buttons to switch between them, and the rows kept in register so the passage he is looking at stays at the same height whichever he is showing.
2. When he **selects text** in the transcription or the translation, the **part of the scan it came from lights up**. He called this the thing that "would be huge".
3. A **Zotero-like export**: select a passage, copy it with a **citation** (page number, document metadata) ready to paste.
4. A way to **make calls on unresolved differences** in both workflows: the transcription spans the consensus flagged, and the differences between translations.
5. While selecting, a way to **mark an issue or question**, with a **comment**, that is **logged** and can be **returned to later**. The log lives in the folder, in the repository, as a file.
6. "This never has to be an app." A local page he opens, with the record kept locally.

What exists to build on (verified in the code on 5 November 2026):

- **Readings with coordinates.** `03-layout-and-hybrid/outputs/runs/{print,hand}-20261105/` holds, for all six real pages, a `kraken/` reading and a `hybrid/google_gemini-3.8-flash/` reading whose every line has `bbox` (pixels, `[x, y, w, h]`) and `baseline`. Whole-page vision readings in all three cases have `bbox: null`.
- **The consensus** (`src/mueser/text/compare.py`) computes a medoid reading and disagreement spans per page, and writes `consensus.json`, `checkin.csv` and an HTML page. Its spans are offsets into **normalised, flattened** text (`evaluate.normalize`: ſ→s, superscript umlauts folded, hyphenated line ends joined, whitespace collapsed, line breaks gone). `compare apply` therefore writes a flattened, normalised text and says so. The diplomatic lines of the medoid survive untouched in its run JSON under `outputs/runs/<run>/<backend>/<model>/<page>.json`.
- **The HTML** is Python f-strings (`report.py`, `compare.py`, `layout.py`), then `shared/review.py` `enhance_html(document, out, kind)` injects `shared/web/review.css` and `review.js`. `review.js` is progressive enhancement over the existing DOM: it has no persistence, no `fetch`, and no editing. Check-in decisions are typed into `checkin.csv` by hand; all four current files have zero decisions.
- **Coordinates drawn over an image** exist once: `layout.py` `overlay` writes an SVG `<rect>` per region and line over the page. That is the pattern for the image pane.
- **No translation step exists.** `transcribe_de.md` rule 1 is "Do not translate"; keep it that way. Translation is a new, separate layer.
- **The OpenRouter client** `shared/openrouter.py` `chat(model, system, user_text, image_path, schema, ...)` returns `{text, parsed, usage, cost_usd, cached, model, provider, raw, key}`, caches every reply under `cache/openrouter/`, and logs cost per step. Prompts live as Markdown with `<!-- PROMPT START -->` / `<!-- PROMPT END -->` markers, loaded by a small regex (`layout.load_prompt`, `extract.load_prompt`).
- **Run manifests** are `shared/runs.py` `RunManifest(run_id, step, params, inputs, outputs, cost_usd, seconds, notes, ...)`, written as `run.json`.

Not yet known (do not block on these; leave hooks): Ben's browser; whether he reads English or German translations first; which of his own pages come first and whether they are IIIF.

---

## 2. Where it lives

```
01-use-cases/transcription/04-reading-room/
├── HANDOFF.md                 # this brief
├── CLAUDE.md                  # rules for this folder
├── README.md                  # for Ben: what ran, what it found, how to use the page (written at the end)
├── summary.md  index.md       # as in the other cases
├── inputs/
│   ├── README.md              # origins and rights of every page, as in 02-kurrent-handwriting
│   ├── pages/                 # real-grimm-khm-1812-i-p093.jpg, real-kaskel-to-schnorr-1864.jpg, real-schiller-musenalmanach-1796-p093.jpg
│   ├── metadata.json          # document metadata for citations (§4.5)
│   └── readings/              # copies of the medoid run JSONs, the boxed segmentation JSONs, the consensus.json files
│       └── provenance.json    # where each copy came from: case, run id, path, sha256
├── operations/
│   ├── 00-collect-inputs.py   # copies pages and readings from cases 01–03 and writes provenance.json
│   ├── 01-settle.sh           # python -m mueser.reading settle build …
│   ├── 02-anchor.sh           # python -m mueser.reading anchor run …
│   ├── 03-translate.sh        # python -m mueser.reading translate run … (two models)
│   ├── 04-build.sh            # python -m mueser.reading build …
│   ├── 05-review.md           # how Ben opens the page, decides, exports, and how a decision becomes text
│   └── work/                  # scratch, not committed if large
└── outputs/
    ├── index.html             # the reading room (regenerated by `build`, like every other index.html)
    └── reading/
        ├── log.jsonl          # append-only record of everything Ben does in the page (§4.4)
        ├── inbox/             # exported logs dropped here when the page ran as file:// (§4.6)
        ├── runs/<run_id>/translation/<model_slug>/<page_id>.json + run.json
        └── builds/<build_id>/ settled.json · transcription/<page>.txt · translation/<page>.txt · run.json
```

The code is a new subpackage, `src/mueser/reading/`, with a typer CLI at `python -m mueser.reading`:

| module | what it does | commands |
|---|---|---|
| `settle.py` | medoid lines from `consensus.json` + the medoid's run JSON; remap normalised spans onto raw lines; build the settled layer; apply recorded decisions | `settle build`, `settle apply` |
| `anchor.py` | align settled lines to a reading that has boxes | `anchor run` |
| `translate.py` | two-model sentence translation with line references; verify; align into blocks; divergence | `translate run`, `translate compare` |
| `log.py` | the event model; append, read, validate, ingest exported logs | `log show`, `log ingest` |
| `cite.py` | citation from `metadata.json` plus provenance; plain, Markdown, CSL-JSON | `cite` |
| `build.py` | assemble one JSON for the page; render `index.html` | `build`, `init-doc` |
| `serve.py` | local server that serves the case folder and appends to the log | `serve` |
| `web/reading.html` `reading.js` `reading.css` | the client | |

The translation prompt goes with the others: `src/mueser/text/backends/prompts/translate_de_en.md`.

Reuse, by name: `compare.dist` (alignment cost and divergence), `compare.disagreements` and `compare.Reading` (word-widened spans inside a divergent translation block), the `compare.apply` pattern (made line-aware), `evaluate.normalize` (drives the offset map), `evaluate.char_diff` (in-block diffs), `layout.overlay`'s SVG rects and `layout.kraken_lines`, `KrakenBackend.segment` (only for pages with no boxed reading), `shared.openrouter.chat` with a strict schema, `RunManifest`, `review.enhance_html(kind="reading")`, `ingest.folder` / `ingest.iiif` and their `pages.json`.

---

## 3. Components

### 3.1 Settle: the layer Ben reads

The reading layer is the **medoid reading's diplomatic lines**, with recorded decisions applied. Not the ground truth (`inputs/gt/*.txt` is paragraph text, not line-aligned, and is irrelevant here), and not `compare apply`'s flattened text.

`settle build --consensus <dir> --runs <dir> --pages <dir> --out outputs/reading/builds/` writes `builds/<build_id>/settled.json` (§4.1) and `transcription/<page>.txt` (diplomatic line breaks kept). For each page it:

1. reads `consensus.json` `pages[pid].medoid.overall` and loads that reader's run JSON (`lines[].text`);
2. builds, per raw line, `norm_map(raw_line) -> list[int]` where `pos[i] = len(normalize(raw_line[:i+1]))`, and the line's offset into `base_text` from the cumulative normalised lengths plus one for the space, minus the hyphen-join correction when a line ends with `-`. Lines are short, so this is robust to every substitution `normalize` makes;
3. remaps each `spans[]` entry to `(line_id, start, end)` pieces; a span crossing a line break becomes two pieces sharing `span_id`;
4. records the build: `build_id`, the consensus run id, the medoid reader, the medoid run path, the sha256 of `evaluate.normalize`'s source (so a later change to normalisation is visible), and `notes`.

`settle apply --build <id> --log outputs/reading/log.jsonl --out outputs/reading/builds/` reads the log, takes the **latest decision per target** by `ts`, and writes a **new** build: `settled` text per line with pieces replaced (blank or `keep` means the medoid stands), translation blocks resolved to the chosen model's text or the custom text. A build is never modified. The new build id goes into every later event, so each decision can be checked against the text it was made on.

Pages where readers agree poorly (the 1901 album, agreement 0.41) produce one giant span. Keep the warning `compare run` already prints and let the viewer offer **whole-line** decisions on such pages.

### 3.2 Anchor: lines to boxes

Most medoids are whole-page vision readings with no boxes. `anchor run --build <id> --segmentation <run folder with boxes> [--segment-now]` aligns each page's settled lines to the lines of a reading that has `bbox`, preferring a hybrid reading (boxes and good text) and falling back to Kraken's own reading. `--segment-now` runs `KrakenBackend.segment` only for pages with no boxed reading at all, and is off by default (Ben's machine may not have Kraken).

Algorithm: Needleman–Wunsch over the two **lists of line strings** with cost `compare.dist(a, b)` and four operations:

| op | meaning | box |
|---|---|---|
| `match` | one settled line, one polygon | that polygon's bbox |
| `merge` | two settled lines against one polygon (cost `dist(a1 + " " + a2, b)`) | both lines get the polygon's bbox, flagged |
| `split` | one settled line against two polygons (a column gap) | union of the two |
| `unanchored` | a settled line with no polygon | none |

A polygon with no settled text (ornament, masthead lettering) is dropped and counted. `confidence = 1 - dist` of the final pairing; pairs above `--max-dist 0.55` are demoted to `unanchored`. Results go into `settled.json` `lines[].anchor` and a per-page `anchors` summary (`segmentation {run_id, backend, model, path}, matched, merged, split, unanchored, dropped_polygons, mean_confidence`). Line-level alignment rather than character-level because the failure modes (missing, merged, split, non-text polygons) are then explicit and each gets a confidence.

Evidence that this is tractable: on the Grimm page Kraken and hybrid have 30 lines, the whole-page reading 29; on Kaskel 24 against 22. On the Schiller page the hybrid reading is itself the medoid, so every line is a 1:1 match.

In the viewer an unanchored line still renders, with a dotted left edge, and lights nothing on the scan. The README states the counts per page.

### 3.3 Translate: sentences that know their lines

`translate run --build <id> --models google/gemini-3.8-flash,anthropic/claude-sonnet-5.5 --out outputs/reading/runs/` sends each page's settled lines as `l1: …`, `l2: …` (the `extract.numbered` style, with line ids) and asks for sentence segments under a strict JSON schema:

```json
{"segments": [{"line_start": "l5", "line_end": "l7", "first_words": "Meine Freude wurde", "last_words": "Vater unter den",
               "translation": "My joy was doubled when …", "note": ""}], "notes": ""}
```

Prompt rules (`translate_de_en.md`): translate sentence by sentence into English; one segment per sentence; a segment may span lines and must never skip one; keep `[...]` and `[?word]` as they are; do not resolve abbreviations, fill gaps, or modernise names; `first_words` and `last_words` are the first and last three words of the source sentence, verbatim. Temperature 0. The same system and user text goes to both models so the cache keys differ only by model.

`verify_segments` (the `extract.verify_surface` idea): `first_words` must occur in `line_start`'s text and `last_words` in `line_end`'s, after `normalize`; if not, search neighbouring lines and correct the range (`verified: "corrected"`); otherwise `verified: false`, kept and flagged. Segments must be in order and cover every line; uncovered lines are listed in `notes`. Each page result records `model`, `run_id`, `prompt_sha256`, `cache_key`, `cost_usd`, and `layer_sha256`, the sha256 of the page's settled text at translation time. After `settle apply` changes a line, the build marks that page's translation **stale**; it is not reused silently.

`translate compare` aligns the two models' segments into **blocks** whose line ranges coincide (greedy walk on `line_end`, merging segments until both sides agree), computes `compare.dist` per block, and marks a block **divergent** at `--min-divergence 0.35`. Inside a divergent block, `compare.disagreements(Reading(a), [Reading(b)])` gives the word-widened spans to show. The threshold is recorded in `run.json`: two faithful translations differ in wording everywhere; at 35 % edit distance they usually differ in sense. Divergent blocks are the translation check-in list; a decision is `a`, `b` or custom text.

### 3.4 Build and serve: the page

`build --case <folder> --build <id> [--translation <run_id>]` assembles one JSON (`reading.json`: metadata, pages, lines with anchors and spans, translation segments and blocks, the current log snapshot) and renders `outputs/index.html` from `web/reading.html` with the JSON in `<script type="application/json" id="reading-data">` (escape `<` as `<`, as `review.py` does), `reading.css` and `reading.js` inline, and a `<noscript>` block listing every line's diplomatic text with its id. Then `enhance_html(doc, out, "reading")` for the shared top bar.

Client-side rendering from one blob, not f-string DOM, because the client must map selections to line ids and character offsets, redraw rects, switch modes and keep rows in register, all of which is a render from data. Everything the page needs at open time is in the file: `fetch()` of sibling files is blocked under `file://` in Chrome.

Viewer mechanics:

- Image pane: `<div class="fig"><img><svg viewBox="0 0 W H" preserveAspectRatio="none">` with one `<rect data-line="l2">` per anchored line (the `layout.overlay` pattern).
- Text pane: each line is `<span class="ln" data-line="l2">` carrying the settled text, with `<mark data-span>` for open spans. Translation rows render each block as a grid row: the block's lines on the left, the translations (both models, or the settled one) on the right. Transcription / translation / both are **the same row list with columns hidden**, so register costs nothing. A sentence that starts mid-line is labelled "from l5, mid-line" rather than splitting the line element.
- `selectionchange`: walk `Range.startContainer` up to `.ln` (or `.seg`), compute the character offset by summing preceding text nodes. Hover or selection adds `.active` to the matching rects and, for a translation segment, to its lines.
- Decisions open a small form prefilled from `spans[].alternatives` or the block's two translations, with `keep | alt | custom` and a note.
- Issue / question: select, type a comment, save. The log panel lists open items with filters (type, page, status) and a "go to" that scrolls and highlights.
- Copy with citation: a menu with plain, Markdown and CSL-JSON (§4.5); the copy also appends an `excerpt` event.
- A `who` field in the top bar (default from `serve --who`, else what the person types) goes on every event.

`serve --case <folder> [--port 8765] [--who ben]`: stdlib `ThreadingHTTPServer` on `127.0.0.1`, static files only from inside the case folder (reject any resolved path outside it), `GET /api/ping` → `{build_id, who}`, `GET /api/log` → the file, `POST /api/log` → validate one event with `log.Event` and against the build (anchors must resolve), append, echo the stored line. It opens the browser. Under 120 lines.

### 3.5 Persistence without a server

Every event gets a client id `evt_<uuid4>` and is written to `localStorage["mueser.reading.<doc_id>"]` first. If the page was served over `http:` and `/api/ping` answered at load, it is POSTed and marked synced. Under `file://` a banner says: "Not connected: notes are kept in this browser. Export log writes them to a file; drop it into `outputs/reading/inbox/` and run `python -m mueser.reading log ingest`." The build embeds the log snapshot, and the viewer overlays localStorage on it, so a `file://` reader sees state. `log ingest` appends unseen ids and reports duplicates.

The File System Access API is not used: Chrome and Edge only, permission every session, and it rewrites whole files, which an append-only log should not do.

### 3.6 Citation export

`cite.py` builds a citation from `inputs/metadata.json` (§4.5) plus the provenance of the selection, and `reading.js` mirrors it for the clipboard (the Python side is tested; the JS side is what Ben pastes). Three formats:

- **plain:** `Grimm, Kinder- und Haus-Märchen, Erster Band (Berlin, 1812), p. 93, ll. 2–4. Transcription: medoid openrouter:google/gemini-3.8-flash, run print-20261105, settled build b-20261106-1005, 2 decisions by ben. Translation: anthropic/claude-sonnet-5.5, run 20261106-1030, block b03 decided by ben.`
- **Markdown:** the selection as a blockquote and a footnote with the plain citation, the repo path of `settled.json` and the line ids.
- **CSL-JSON:** `{"type", "title", "author": [{"family", "given"}], "issued": {"date-parts": [[1812]]}, "publisher", "publisher-place", "URL", "archive", "archive_location", "note": "<provenance sentence>", "locator": "93, lines 2–4", "label": "page"}`. Zotero imports CSL-JSON from the clipboard, which gives the Zotero path without an add-on; `note` carries provenance because CSL has no slot for it.

`init-doc --pages <folder with pages.json> --out inputs/metadata.json` writes a skeleton for Ben's own documents from `ingest`'s `pages.json` (page ids, canvas ids, sha256 filled; bibliographic fields empty for him to complete).

---

## 4. Data model

### 4.1 `settled.json`

```json
{"build_id": "b-20261106-1005", "doc_id": "real-grimm-khm-1812-i", "consensus_run": "print-20261105",
 "normalize_sha256": "…", "created": "2026-11-06T10:05:11-0500",
 "pages": {"real-grimm-khm-1812-i-p093": {
   "image": "../inputs/pages/real-grimm-khm-1812-i-p093.jpg", "width": 1168, "height": 1752,
   "diplomatic": {"reader": "openrouter:google/gemini-3.8-flash", "run_id": "print-20261105", "path": "…json", "prompt_sha256": "…"},
   "lines": [{"line_id": "l2",
              "diplomatic": "die Tauben wieder herein und thaten freund-",
              "settled": "die Tauben wieder herein und thaten freund-",
              "anchor": {"bbox": [131, 285, 566, 65], "op": "match", "confidence": 0.97, "seg_idx": [1]},
              "spans": [{"span_id": "3", "start": 30, "end": 33, "base": "und", "alternatives": {"kraken:german_print.mlmodel": "vnd"},
                         "weight": 0.24, "status": "open", "decision_event": null}]}],
   "anchors": {"segmentation": {"run_id": "print-20261105", "backend": "hybrid", "model": "google/gemini-3.8-flash", "path": "…"},
               "matched": 27, "merged": 1, "split": 0, "unanchored": 1, "dropped_polygons": 1, "mean_confidence": 0.93},
   "translation": {"run_id": "20261106-1030", "stale": false,
                   "segments": {"google/gemini-3.8-flash": [...], "anthropic/claude-sonnet-5.5": [...]},
                   "blocks": [{"block_id": "b03", "lines": ["l5", "l7"], "a": "s07", "b": "s06", "dist": 0.41, "divergent": true,
                               "status": "open", "decision_event": null}]}}}}
```

`diplomatic` never changes. `settled` is `diplomatic` with decisions applied.

### 4.2 Translation segment (in the run JSON and in `settled.json`)

```json
{"segment_id": "s07", "line_start": "l5", "line_end": "l7",
 "first_words": "Meine Freude wurde", "last_words": "Vater unter den",
 "translation": "My joy was doubled when …", "note": "",
 "verified": true, "model": "anthropic/claude-sonnet-5.5", "run_id": "20261106-1030",
 "prompt_sha256": "…", "layer_sha256": "…", "cache_key": "…"}
```

### 4.3 Anchor (per line)

`{"bbox": [x, y, w, h] | null, "op": "match|merge|split|unanchored", "confidence": 0.0–1.0 | null, "seg_idx": [int, …]}`

### 4.4 Log event (`outputs/reading/log.jsonl`, one per line, append-only)

```json
{"id": "evt_8d3f…", "ts": "2026-11-06T10:12:44-0500", "who": "ben", "client": "reading-room@<git sha>", "build_id": "b-20261106-1005",
 "type": "decision",
 "anchor": {"doc": "real-grimm-khm-1812-i", "page": "real-grimm-khm-1812-i-p093", "layer": "transcription",
            "lines": ["l4"], "segment": null, "start": {"line": "l4", "char": 0}, "end": {"line": "l4", "char": 14}, "quote": "leſen?“ „Ja, —"},
 "body": {"target": "span:real-grimm-khm-1812-i-p093:17", "choice": "alt", "reader": "kraken:german_print.mlmodel", "text": "leſen?“ „Ja, —", "note": ""},
 "ref": null}
```

- `type` ∈ `highlight | comment | issue | question | decision | status | excerpt`.
- `anchor.layer` ∈ `transcription | translation`; for translation, `segment` is set and `start.char` / `end.char` are offsets in that segment's text.
- `body` by type: **decision** `{target: "span:<page>:<span_id>" | "block:<page>:<block_id>" | "line:<page>:<line_id>", choice: "keep|alt|custom", reader?, text, note}`; **issue / question / comment** `{text}`; **status** `{target: "<event id>", status: "open|resolved|wontfix", note}`; **excerpt** `{format, text, citation}`; **highlight** `{}`.
- `ref` is the id of the event this one answers (a comment on an issue).
- Status changes are events that reference the issue, so the history is kept and nothing is edited in place. `who` is whatever the person typed; the README says so.
- `ts` uses the `RunManifest` timestamp format.

### 4.5 `inputs/metadata.json`

```json
{"docs": {"real-grimm-khm-1812-i": {
  "type": "book", "title": "Kinder- und Haus-Märchen, Erster Band", "author": ["Jacob Grimm", "Wilhelm Grimm"],
  "date": "1812", "place": "Berlin", "publisher": "Realschulbuchhandlung",
  "archive": "Wikimedia Commons", "shelfmark": null, "url": "https://commons.wikimedia.org/wiki/File:…", "iiif_manifest": null,
  "licence": "public domain", "language": "de", "synthetic": false,
  "pages": {"real-grimm-khm-1812-i-p093": {"label": "p. 93", "iiif_canvas": null, "image_sha256": "…"}}}}}
```

`type` is a CSL type (`book`, `manuscript`, `personal_communication`, `article-newspaper`). Synthetic documents carry `"synthetic": true` and every citation of them says so.

### 4.6 Exported log (`outputs/reading/inbox/<who>-<timestamp>.jsonl`)

The same events as §4.4, one per line, as the browser held them. `log ingest` appends the ones whose ids are not yet in `log.jsonl`.

---

## 5. Credentials

`OPENROUTER_API_KEY` for translation only. Settle, anchor, build and serve run with no key. With no key, `translate run` skips with a clear message and the page shows the transcription alone; the mode toggle still works with translation absent.

---

## 6. Build order and done criteria

| phase | work | done when | tests |
|---|---|---|---|
| 1 | `log.py`; `settle.py` (`norm_map`, `spans_to_lines`, `build_settled`, `latest_decisions`, `apply_decisions`); `operations/00`, `01` | `settle build` on Grimm and Kaskel writes a build whose `transcription/<page>.txt` equals the medoid's `.txt` line for line; `apply` with one hand-written decision event changes exactly one line | `tests/test_reading_settle.py`: `norm_map` on `"Aſchenputtel aͤ  b"`; a span over a hyphenated line end lands as two pieces; `latest_decisions` picks the latest by `ts`; apply round trip |
| 2 | `anchor.py`; `operations/02` | ≥ 90 % of Grimm lines and ≥ 80 % of Kaskel lines anchored at confidence ≥ 0.6; merge/split/unanchored counts in the README | `tests/test_reading_anchor.py` on synthetic line lists: perfect, missing line, merged pair, split line, extra ornament polygon, all unreadable |
| 3 | `build.py`, `web/*`, `review.js` early return, `refresh_review_ui.py` branch | `outputs/index.html` opened from `file://` shows the scan with rects; hover in either direction highlights; mode toggle works with translation absent; `<noscript>` lists the lines | `tests/test_reading_build.py`: `assemble` is valid JSON with a bbox on every anchored line; the HTML has the data blob and one `rect` per anchored line |
| 4 | `serve.py`, localStorage queue, Export and `log ingest`, decision form for spans, `settle apply` from the viewer's events | a decision made in the browser is one line in `log.jsonl`; the same under `file://` arrives via export and ingest; `apply` writes a new build and `build` shows it | `tests/test_reading_serve.py`: start on port 0, POST valid and invalid events, check append and 400; `ingest` dedupes ids |
| 5 | `translate_de_en.md`, `translate.py`, blocks and divergence, translation rows and block decisions in the viewer | both models on three pages with `run.json` and cost; both translations in register; a block decision round-trips | `tests/test_reading_translate.py`: `verify_segments` corrects a wrong range and flags an invented excerpt; `align_segments` on different sentence splits; the threshold |
| 6 | `cite.py` and its JS mirror; issue / question / status UI; excerpt events; `README.md`, `summary.md`, `index.md`; group README, `01-use-cases/README.md`, root `index.html` card, `review.js home()` | CSL-JSON pasted into Zotero makes an item with the locator; an issue marked resolved shows in the log; `uv run pytest -q` green | `tests/test_reading_cite.py`: plain, Markdown, CSL for a book and a manuscript; line-range formatting; synthetic docs labelled |
| 7 | `init-doc` from `pages.json`; optional PDF ingest (`pypdfium2`, new extra); a section in `02-your-project/README.md` | a folder of JPEGs goes ingest → bakeoff (kraken, a vision model, hybrid) → compare → settle → anchor → build with no hand edits | smoke test on the fixture pages |

Small edits outside the package: `review.js` gets `if (config.kind === 'reading') return;` after the top bar and a `reading` entry in `makeHeader`'s type map; `home()` gets an eighth card and its maps-intro condition moves from `count === 3` to `count === 4`; `scripts/refresh_review_ui.py` sniffs `id="reading-data"` as `reading`; the root `index.html` gets a card and a row in "Where the evidence is".

Cost: translating three pages with two models is cents. Everything else is local.

---

## 7. Conventions

Those of the repository `CLAUDE.md`, plus:

- `log.jsonl` is append-only. No command rewrites it; `ingest` appends; a mistake is corrected by a later event.
- A build folder is immutable. `apply` writes a new one. Every event carries the build id it was made against.
- The `diplomatic` text of a line is never edited by any command. Decisions produce `settled`.
- A translation is a layer beside the transcription and is marked stale when its source line changes.
- Thresholds (`--max-dist`, `--min-divergence`) are recorded in `run.json` with the result.
- Synthetic pages, if any are added, carry `synthetic: true` in `metadata.json` and the word in every citation.

---

## 8. Open questions for Ben

- Which browser, and does he mind running one command (`serve`) before opening the page? If he would rather double-click the file, the export path is the one he will live with.
- English translation only, or also a normalised modern German layer beside the diplomatic one?
- Which of his own documents first, and are they digitised as IIIF (library) or his own photographs or PDFs?
- Does he use Zotero? If so, which citation style, so the plain format can match it.
- Who else will read the page and decide? `who` is a free field; if there are two people, say so in the README.

---

## 9. References

- The consensus method: `01-use-cases/transcription/README.md`, "Reading the consensus page".
- `src/mueser/text/compare.py` (`dist`, `Reading`, `Span`, `disagreements`, `apply`); `src/mueser/text/evaluate.py` (`normalize`, `char_diff`); `src/mueser/text/layout.py` (`overlay`, `kraken_lines`); `src/mueser/shared/review.py`, `src/mueser/shared/web/review.js`; `src/mueser/shared/openrouter.py` (`chat`); `src/mueser/shared/runs.py` (`RunManifest`).
- The boxed readings to anchor against: `01-use-cases/transcription/03-layout-and-hybrid/outputs/runs/print-20261105/hybrid/google_gemini-3.8-flash/real-grimm-khm-1812-i-p093.json` and its `hand-20261105` sibling.
- CSL-JSON: https://docs.citationstyles.org/en/stable/specification.html · Zotero clipboard import: Zotero "Import from Clipboard" accepts CSL-JSON.
- IIIF Image API (for Ben's library scans): https://iiif.io/api/image/3.0/
