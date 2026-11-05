# Use cases

Five worked examples in two groups, each with `inputs/`, numbered
`operations/`, and `outputs/` whose `index.html` is an explorer that shows
the process, not only the result. Every number in a README comes from a run
folder you can open.

| Group | What the examples do | Start with |
|---|---|---|
| [`transcription/`](transcription/) | Several OCR/HTR backends read the same Fraktur and Kurrent pages; every reading is scored against known text and shown beside the image with its diff, cost and prompt. | [`01-fraktur-print-bakeoff/`](transcription/01-fraktur-print-bakeoff/) |
| [`maps/`](maps/) | Historical place names go through three gazetteers with a recorded decision per name into a database and a map; a historical map scan can be warped underneath; and the names can come from the transcriptions instead of a table. | [`01-places-to-map/`](maps/01-places-to-map/) |

## Every example

| Use case | What you will see | Open |
|---|---|---|
| [Transcription · 01 · Fraktur print](transcription/01-fraktur-print-bakeoff/) | Five Tesseract and Kraken models on five synthetic and three real pages. Kraken wins on real pages (CER 0.015–0.034), Tesseract on synthetic ones; the explorer shows why. | [Guide](transcription/01-fraktur-print-bakeoff/README.md) · [Explorer](transcription/01-fraktur-print-bakeoff/outputs/index.html) |
| [Transcription · 02 · Kurrent handwriting](transcription/02-kurrent-handwriting/) | The open handwriting model on three letters and album pages: CER 0.21 on a clean 1864 hand, 0.82 on a photographed album. The vision models and Transkribus are wired and waiting for keys. | [Guide](transcription/02-kurrent-handwriting/README.md) · [Explorer](transcription/02-kurrent-handwriting/outputs/index.html) |
| [Maps · 01 · Places to map](maps/01-places-to-map/) | 24 names from a 1786 ledger: 21 resolved by agreement or a recorded population tie-break, 3 in review. Click a point for every candidate and the reason. | [Guide](maps/01-places-to-map/README.md) · [Map](maps/01-places-to-map/outputs/index.html) |
| [Maps · 02 · Historical map overlay](maps/02-historical-map-overlay/) | What the Allmaps index offers at each point, with each sheet's scale and a control-point check; why the overlay ships off; how to turn it on. | [Guide](maps/02-historical-map-overlay/README.md) · [Table](maps/02-historical-map-overlay/outputs/georeferenced-maps.csv) |
| [Maps · 03 · From page to map](maps/03-from-page-to-map/) | Kraken's OCR of the five journal pages, errors included → 88 mentions checked verbatim → 52 place mentions on a map, each linked to a page and line. | [Guide](maps/03-from-page-to-map/README.md) · [Map](maps/03-from-page-to-map/outputs/index.html) |

## Outputs that became inputs

The journal pages in `transcription/01` were rendered from an invented
text whose places are the rows of `maps/01`'s ledger; Kraken's reading of
those pages is the input of `maps/03`; `maps/02` queries the points
`maps/01` resolved. One synthetic journey runs through all five folders, so
a name can be followed from a Fraktur line to a gazetteer candidate to a dot.

## How each use case is organized

```text
<use-case>/
  inputs/        source material, with a README that says where it came from and under what licence
  operations/    numbered steps: scripts, prompts, the recorded mention list, and work/ with the files they pass along
  outputs/       index.html (the explorer), the scored CSV/JSON, and runs/<run_id>/ with every reading and a run.json
  README.md      results, the pipeline, how to rerun and extend
  summary.md     purpose, workflow, findings, limits in a paragraph each
  index.md       file-by-file guide
  CLAUDE.md      instructions for Claude Code in that folder
```

Every step says whether it is **deterministic code** (same input, same
output), **deterministic lookup** (a cached, rate-limited call to a public
service) or **model judgment** (a language model reading and deciding, with
the prompt and model recorded).
