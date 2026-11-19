# Use cases

Five groups: the four projects agreed with Ben in November 2026, and the
earlier maps work. Each case has `inputs/`, numbered `operations/`, and
`outputs/` whose `index.html` is a page that shows the process, not only
the result; a scoped case has the same folders, a `HANDOFF.md` for the
agent that will build it, and a README that says what it will do. Every
number in a README comes from a run folder you can open.

| Group | What it does | Status | Start with |
|---|---|---|---|
| [`transcription/`](transcription/) | The reading room: the settled text of a page and its translation beside the scan, decisions and citations in a log; behind it, nine readers scored against known text, merged into a consensus, a layout pass and a hybrid mode that keeps every line's coordinates. | built | [`04-reading-room/`](transcription/04-reading-room/) |
| [`timeline/`](timeline/) | Thinkers, works, events, periods and concepts from Wikidata by written rules, each cited and linked to the reference works, on one band of years with layers for how they connect; a model's proposed thinker-to-event connections wait for a decision. | built, first version | [`01-thinkers-and-events/`](timeline/01-thinkers-and-events/) |
| [`style/`](style/) | The CV extended without changing its page geometry; an article brought to a journal's house style from the journal's own articles, each change decided before it is made. Scoped: handouts normed to a house style; a book's footnotes checked against its bibliography. | two of four built | [`02-cv/`](style/02-cv/) |
| [`notes/`](notes/) | Email, voice memos, files, PDF highlights and Zotero items into one local database, aggregated by project, tagged with themes after review, with a reviewer page on the reading room's log pattern. | scoped | [`01-notes-apparatus/`](notes/01-notes-apparatus/) |
| [`maps/`](maps/) | Historical place names through three gazetteers with a recorded decision per name into a database and a map; names from the transcriptions; or map data with no text at all. | earlier work | [`01-places-to-map/`](maps/01-places-to-map/) |

## Every example

| Use case | What you will see | Open |
|---|---|---|
| [Timeline · 01 · Thinkers and events](timeline/01-thinkers-and-events/) | One node at a time: the periods and events of its years above, what came before it on the left, what it touched on the right, the overview, works, references and a connection map in the middle. Nodes from Wikidata by rule; Stanford Encyclopedia citations from the entries themselves; proposed connections quoting the sentence they rest on. | [Guide](timeline/01-thinkers-and-events/README.md) · [Timeline](timeline/01-thinkers-and-events/outputs/index.html) |
| [Style · 01 · Handouts](style/01-handouts/) | Scoped: infer the house style three to five handouts share, apply it without changing a word, refresh one for a new term. | [Guide](style/01-handouts/README.md) · [Brief](style/01-handouts/HANDOFF.md) |
| [Style · 02 · CV](style/02-cv/) | Built on a synthetic CV: the CV as data; a new entry is a copy of its neighbour's paragraph or table row with new text; every other paragraph compared with the source as XML; page count checked, never forced. | [Guide](style/02-cv/README.md) · [Brief](style/02-cv/HANDOFF.md) |
| [Style · 03 · Footnotes](style/03-footnotes/) | Scoped: nine named rules over a book's notes and bibliography; a short form resolved only to exactly one entry; every proposed change reviewed before it is applied. Answers Ben's question about what context to give. | [Guide](style/03-footnotes/README.md) · [Brief](style/03-footnotes/HANDOFF.md) |
| [Style · 04 · Journal style](style/04-journal-style/) | Built on synthetic files: fifteen conventions counted in a journal's articles; every place a draft differs listed with a proposed change; notes restyled by a model after the journal's verified examples, as proposals; accepted rows written to a copy and read back. | [Guide](style/04-journal-style/README.md) |
| [Notes · 01 · Notes apparatus](notes/01-notes-apparatus/) | Scoped: every note whole and immutable in SQLite with its source; projects, themes and connections as proposals; a reviewer page. | [Guide](notes/01-notes-apparatus/README.md) · [Brief](notes/01-notes-apparatus/HANDOFF.md) |
| [Transcription · 04 · Reading room](transcription/04-reading-room/) | Three real pages read beside their scans: the medoid's lines with the readers' doubts remapped onto them, anchored to the hybrid reading's boxes (29 of 29, 20 of 22, 18 of 18 lines), translated by two models sentence by sentence (one divergent block in 21). Selecting text lights the scan; a passage copies with a citation; decisions, questions and issues go to an append-only log. | [Guide](transcription/04-reading-room/README.md) · [Reading room](transcription/04-reading-room/outputs/index.html) |
| [Transcription · 01 · Fraktur print](transcription/01-fraktur-print-bakeoff/) | Nine readers on five synthetic and three real pages. Gemini 3.8 Flash and 3.1 Pro at normalised CER 0.010–0.018 on real Fraktur, Kraken 0.03, Tesseract 0.07–0.09; Kraken best on the Antiqua page. $0.23. | [Guide](transcription/01-fraktur-print-bakeoff/README.md) · [Explorer](transcription/01-fraktur-print-bakeoff/outputs/index.html) · [Consensus](transcription/01-fraktur-print-bakeoff/outputs/consensus/index.html) |
| [Transcription · 02 · Kurrent handwriting](transcription/02-kurrent-handwriting/) | Seven readers on three synthetic and three real pages. Gemini at CER 0.06 on a clean 1864 hand where Kraken has 0.21; 0.18 on a fast 1896 hand; a photographed 1901 album defeats everyone. One empty reply recorded as an error. $0.24. | [Guide](transcription/02-kurrent-handwriting/README.md) · [Explorer](transcription/02-kurrent-handwriting/outputs/index.html) · [Consensus](transcription/02-kurrent-handwriting/outputs/consensus/index.html) |
| [Transcription · 03 · Layout and hybrid](transcription/03-layout-and-hybrid/) | A vision model maps each real page (regions by kind, every line's box, stamps, corrections, later hands, reading order) beside Kraken's segmentation; then Kraken's lines are read one crop at a time by a vision model, so the reading keeps coordinates. | [Guide](transcription/03-layout-and-hybrid/README.md) · [Layout overlay](transcription/03-layout-and-hybrid/outputs/layout.html) · [Explorer](transcription/03-layout-and-hybrid/outputs/index.html) |
| [Maps · 01 · Places to map](maps/01-places-to-map/) | 24 names from a 1786 ledger: 21 resolved by agreement or a recorded population tie-break, 3 in review. Click a point for every candidate and the reason. | [Guide](maps/01-places-to-map/README.md) · [Map](maps/01-places-to-map/outputs/index.html) |
| [Maps · 02 · Historical map overlay](maps/02-historical-map-overlay/) | What the Allmaps index offers at each point, with each sheet's scale and a control-point check; why the overlay ships off; how to turn it on. | [Guide](maps/02-historical-map-overlay/README.md) · [Table](maps/02-historical-map-overlay/outputs/georeferenced-maps.csv) |
| [Maps · 03 · From page to map](maps/03-from-page-to-map/) | Kraken's OCR of the five journal pages, errors included → 88 mentions checked verbatim → 52 place mentions on a map, each linked to a page and line. | [Guide](maps/03-from-page-to-map/README.md) · [Map](maps/03-from-page-to-map/outputs/index.html) |
| [Maps · 04 · From map data](maps/04-from-map-data/) | No text: a GOV bounding-box extract of 1,715 places and 3,721 dated names, questioned in SQL (552 German names end and 955 Polish names begin in 1945), mapped with a time slider, exported to SQLite and GeoPackage. | [Guide](maps/04-from-map-data/README.md) · [Map](maps/04-from-map-data/outputs/index.html) · [Queries](maps/04-from-map-data/outputs/queries.md) |

## The same shape every time

One page diverges into many readings, which converge on a consensus with
its doubts marked, and a person settles the doubts. A thinker's extract
diverges into candidate events, a model proposes which bear on them and
quotes its sentence, and a person accepts or rejects. A footnote's short
form diverges into candidate entries, a rule converges on exactly one or
on a question, and a person answers. Names diverge into gazetteer
candidates, a written rule converges on a point or a review row, and a
person settles the rows. The decision sits at the centre of each, and it
is recorded, never inferred.

## Outputs that became inputs

The journal pages in `transcription/01` were rendered from an invented
text whose places are the rows of `maps/01`'s ledger; Kraken's reading of
those pages is the input of `maps/03`; `maps/02` queries the points
`maps/01` resolved; `maps/04` joins its region to the same route; the real
pages of `transcription/01` and `02` are the inputs of `transcription/03`;
the consensus and hybrid readings of `transcription/03` are the inputs of
`transcription/04`.

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
