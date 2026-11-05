# Use cases

Seven worked examples in two groups, each with `inputs/`, numbered
`operations/`, and `outputs/` whose `index.html` is an explorer that shows
the process, not only the result. Every number in a README comes from a run
folder you can open. Each group README opens with a conceptual flow chart
and then charts every chain in detail.

| Group | What the examples do | Start with |
|---|---|---|
| [`transcription/`](transcription/) | Nine readers (OCR engines and vision-language models) read the same Fraktur and Kurrent pages; every reading is scored against known text, shown beside the image with its diff, cost and prompt, and merged into a consensus with a check-in list; a layout pass maps regions, lines and marginalia; a hybrid mode keeps every line's coordinates. | [`01-fraktur-print-bakeoff/`](transcription/01-fraktur-print-bakeoff/) |
| [`maps/`](maps/) | Historical place names go through three gazetteers with a recorded decision per name into a database and a map; a historical map scan can be warped underneath; the names can come from the transcriptions; or the work starts from map data with no text at all. | [`01-places-to-map/`](maps/01-places-to-map/) |

## Every example

| Use case | What you will see | Open |
|---|---|---|
| [Transcription · 01 · Fraktur print](transcription/01-fraktur-print-bakeoff/) | Nine readers on five synthetic and three real pages. Gemini 3.8 Flash and 3.1 Pro at normalised CER 0.010–0.018 on real Fraktur, Kraken 0.03, Tesseract 0.07–0.09; Kraken best on the Antiqua page. $0.23. | [Guide](transcription/01-fraktur-print-bakeoff/README.md) · [Explorer](transcription/01-fraktur-print-bakeoff/outputs/index.html) · [Consensus](transcription/01-fraktur-print-bakeoff/outputs/consensus/index.html) |
| [Transcription · 02 · Kurrent handwriting](transcription/02-kurrent-handwriting/) | Seven readers on three synthetic and three real pages. Gemini at CER 0.06 on a clean 1864 hand where Kraken has 0.21; 0.18 on a fast 1896 hand; a photographed 1901 album defeats everyone. One empty reply recorded as an error. $0.24. | [Guide](transcription/02-kurrent-handwriting/README.md) · [Explorer](transcription/02-kurrent-handwriting/outputs/index.html) · [Consensus](transcription/02-kurrent-handwriting/outputs/consensus/index.html) |
| [Transcription · 03 · Layout and hybrid](transcription/03-layout-and-hybrid/) | A vision model maps each real page (regions by kind, every line's box, stamps, corrections, later hands, reading order) beside Kraken's segmentation; then Kraken's lines are read one crop at a time by a vision model, so the reading keeps coordinates. | [Guide](transcription/03-layout-and-hybrid/README.md) · [Layout overlay](transcription/03-layout-and-hybrid/outputs/layout.html) · [Explorer](transcription/03-layout-and-hybrid/outputs/index.html) |
| [Maps · 01 · Places to map](maps/01-places-to-map/) | 24 names from a 1786 ledger: 21 resolved by agreement or a recorded population tie-break, 3 in review. Click a point for every candidate and the reason. | [Guide](maps/01-places-to-map/README.md) · [Map](maps/01-places-to-map/outputs/index.html) |
| [Maps · 02 · Historical map overlay](maps/02-historical-map-overlay/) | What the Allmaps index offers at each point, with each sheet's scale and a control-point check; why the overlay ships off; how to turn it on. | [Guide](maps/02-historical-map-overlay/README.md) · [Table](maps/02-historical-map-overlay/outputs/georeferenced-maps.csv) |
| [Maps · 03 · From page to map](maps/03-from-page-to-map/) | Kraken's OCR of the five journal pages, errors included → 88 mentions checked verbatim → 52 place mentions on a map, each linked to a page and line. | [Guide](maps/03-from-page-to-map/README.md) · [Map](maps/03-from-page-to-map/outputs/index.html) |
| [Maps · 04 · From map data](maps/04-from-map-data/) | No text: a GOV bounding-box extract of 1,715 places and 3,721 dated names, questioned in SQL (552 German names end and 955 Polish names begin in 1945), mapped with a time slider, exported to SQLite and GeoPackage. | [Guide](maps/04-from-map-data/README.md) · [Map](maps/04-from-map-data/outputs/index.html) · [Queries](maps/04-from-map-data/outputs/queries.md) |

## The two diamonds

The transcription group is the first diamond: one page diverges into many
readings, which converge on a consensus with its doubts marked, and a
person settles the doubts; the corrected text becomes ground truth for the
next run. The maps group is the second: names diverge into gazetteer
candidates, a written rule converges on a point or a review row, and a
person settles the rows. The human check-in sits at the centre of each.

## Outputs that became inputs

The journal pages in `transcription/01` were rendered from an invented
text whose places are the rows of `maps/01`'s ledger; Kraken's reading of
those pages is the input of `maps/03`; `maps/02` queries the points
`maps/01` resolved; `maps/04` joins its region to the same route; the real
pages of `transcription/01` and `02` are the inputs of `transcription/03`.

## How each use case is organized

```text
<use-case>/
  inputs/        source material, with a README that says where it came from and under what licence
  operations/    numbered steps: scripts, prompts, the recorded mention list, and work/ with the files they pass along
  outputs/       index.html (the explorer), the scored CSV/JSON, consensus/, and runs/<run_id>/ with every reading and a run.json
  README.md      results, the pipeline, how to rerun and extend
  summary.md     purpose, workflow, findings, limits in a paragraph each
  index.md       file-by-file guide
  CLAUDE.md      instructions for Claude Code in that folder
```

Every step says whether it is **deterministic code** (same input, same
output), **deterministic lookup** (a cached, rate-limited call to a public
service) or **model judgment** (a language model reading and deciding, with
the prompt and model recorded).
