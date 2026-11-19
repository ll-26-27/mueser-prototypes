# Reading room: file by file

| path | what it is | made by |
|---|---|---|
| `README.md` | what ran, what the page does, how to keep and apply decisions, how to add your own pages | hand |
| `summary.md` | purpose, workflow, findings, limits | hand |
| `HANDOFF.md` | the brief this was built from (5 November 2026) | hand |
| `CLAUDE.md` | rules for assistants in this folder | hand |
| `inputs/README.md` | origin and rights of each page | hand |
| `inputs/pages/<page>.jpg` | the three scans | copied from `03-layout-and-hybrid/inputs/` |
| `inputs/metadata.json` | the bibliographic record of each document, for citations | hand |
| `inputs/readings/consensus/<page>.consensus.json` | the per-page slice of `03`'s `consensus.json` (medoid, spans, base text, agreement) | `operations/00-collect-inputs.py` |
| `inputs/readings/medoid/<page>.json` | the medoid reader's run JSON (raw lines, prompt hash, cost) | copied |
| `inputs/readings/segmentation/<page>.json` | the hybrid reading of the page: every line with a box | copied |
| `inputs/readings/provenance.json` | origin path and sha256 of every copy | `operations/00-collect-inputs.py` |
| `operations/00-collect-inputs.py` | the copy step above (deterministic code) | hand |
| `operations/01-settle.sh` … `04-serve.sh` | the exact commands that produced the outputs | hand |
| `operations/05-review.md` | how a person works in the page and how decisions become text | hand |
| `outputs/index.html` | the reading room, self-contained | `python -m mueser.reading build` |
| `outputs/reading/reading.json` | the data the page is rendered from (a derived view; the evidence is below) | `build` |
| `outputs/reading/log.jsonl` | every event made in the page, append-only; created on first use | the page, through `serve` or `ingest` |
| `outputs/reading/inbox/` | exported browser logs waiting for `ingest` | the page's Export button |
| `outputs/reading/builds/<build_id>/settled.json` | per page: diplomatic and settled text per line, remapped spans with status, anchors, consensus and medoid provenance | `settle`, then `apply` |
| `outputs/reading/builds/<build_id>/transcription/<page>.txt` | the settled text, one line per line | `settle`, `apply` |
| `outputs/reading/builds/<build_id>/translation/<page>.txt` | the settled translation, one block per line (only after `apply` with a translation run) | `apply` |
| `outputs/reading/builds/<build_id>/run.json` | parameters, inputs, notes | `settle`, `apply` |
| `outputs/reading/runs/<run_id>/translation/<model>/<page>.json` | one model's segments for one page, verified, with cost and cache key | `translate` |
| `outputs/reading/runs/<run_id>/translation/<page>.blocks.json` | the two models' segments aligned into blocks, with divergence | `translate` |
| `outputs/reading/runs/<run_id>/run.json` | models, prompt hash, threshold, cost, time | `translate` |

Code: `src/mueser/reading/` (`settle.py`, `anchor.py`, `translate.py`,
`log.py`, `cite.py`, `build.py`, `serve.py`, `web/`), prompt
`src/mueser/text/backends/prompts/translate_de_en.md`, tests
`tests/test_reading.py`. Raw model replies: `cache/openrouter/`.
