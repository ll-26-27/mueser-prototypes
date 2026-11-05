---
title: From page to map — the bridge
description: Kraken's OCR of five synthetic Fraktur pages, reading errors included → a mention list made in session and recorded as model judgment → every mention checked verbatim against its line → shared records with page and line → the same gazetteer resolver → a map where each point links back to a line of a page.
author: claude
created: 2026-11-04
---

# From page to map: the bridge

Open **`outputs/index.html`**. Every point carries its mentions with document,
page and line number, and the gazetteer candidates behind the choice.

## What happened

The input is not the clean synthetic text but **Kraken's reading of the
rendered pages** (`inputs/synth-0?.txt`, copied from the Fraktur bake-off
run `20261104-171047`), so the names arrive the way they would from a real
OCR run: "Verlin", "Lieqnitz", "Rönigsberg", "Lolberg", "Rant" for Kant.

| step | count |
|---|---|
| lines of OCR text, five pages | 73 |
| mentions listed (places, people, organisations) | 89 |
| rejected because the surface form is not verbatim on the stated line | 1 ("Gaſthofe zum goldenen Engel", which spans two lines) |
| records written | 88: 73 places, 8 people, 7 organisations |
| distinct place names sent to the gazetteers | 56 |
| resolved automatically | 36 |
| left for review | 20 |
| place mentions on the map | 52 of 73 |

**Who did the extraction.** No API key existed, so the mention list
(`operations/02-mentions.json`) was written by Claude (Fable 5.1) inside
the Claude Code session that built this repository, following the same
prompt the API path uses (`src/mueser/text/backends/prompts/extract_de.md`).
The file says so in its `method` field, and every record's
`source.extraction_method` is `in-session/claude-fable-5-1`. With a key,
`python -m mueser.text.extract run` does the same job per page with a JSON
schema, and the records say `llm/<model id>` instead. Either way step 3
rejects any mention whose `surface_form` is not on the line it claims.

**What the OCR errors did.** The resolver looks up the `normalized` name,
which the extractor supplies from context, so "Verlin" resolves to Berlin
and "Rönigsberg" to Königsberg, and the record keeps the garbled surface
form beside the modern name. That is the designed path: a human-readable
`normalized` guess, a verbatim `surface_form`, and the line number to check
either. Where the extractor could not normalise with confidence it said so
in `notes`.

**What stayed unresolved**, the twenty names in `decisions.json`: countries
and regions whose names tie at 1.0 across several GOV objects of different
kinds (Deutschland, England, Holland, Polen, Schlesien) or score only 0.80
on an alias (Großpolen, Mark Brandenburg, Königreich Preußen); rivers and
landforms (Elbe, Katzbach, Frische Nehrung); buildings and streets the
gazetteers do not hold as places (Peterskirche Görlitz, Marienkirche
Danzig, Schloss Sanssouci, Odertor, Burgstraße); the historical quarters of
Königsberg (Kneiphof, Löbenicht); and two of the ledger's ambiguous towns,
Neustadt and Stettin (Halle resolved this time because the extractor wrote
"Halle (Saale)", which is the kind of context the ledger lacked). Each has
its candidates in `operations/work/review.csv`. The bare-name fallback is
what resolved "Königsberg (Preußen)", "Memel (river)", "Spree (river)",
"Weichsel (river)" and "Landeskrone (hill near Görlitz)", and the reason
says "bare name".

## The pipeline

1. **`inputs/`** (copied, not edited): Kraken's five `.txt` readings and
   their `.json` sidecars from the Fraktur bake-off, plus the page images.
2. **`operations/02-mentions.json`** (model judgment, recorded): every
   mention with `surface_form`, `normalized`, `type`, `line_index`, dates,
   and a note where a human should look.
3. **`operations/03-records-from-mentions.py`** (deterministic code):
   verifies each surface form on its line, writes
   `operations/work/03-records.jsonl` (+ `.csv`) and `03-report.json` with
   the rejects.
4. **Resolve, load, export, build** exactly as in `01-places-to-map`:

   ```sh
   B=01-use-cases/maps/03-from-page-to-map
   uv run python $B/operations/03-records-from-mentions.py
   uv run python -m mueser.maps.resolve run --records $B/operations/work/03-records.jsonl --out $B/operations/work --sources gov,wikidata,whg
   uv run python -m mueser.maps.load records $B/operations/work/records_resolved.jsonl --db $B/operations/work/research.duckdb
   uv run python -m mueser.maps.export geojson --db $B/operations/work/research.duckdb --out $B/outputs/records.geojson
   uv run python -m mueser.maps.build_map build --geojson $B/outputs/records.geojson --decisions $B/operations/work/decisions.json --out $B/outputs/index.html --title "From page to map"
   ```

With a key, replace step 2 by

```sh
uv run python -m mueser.text.extract run --transcripts $B/inputs --doc-id reisetagebuch-1786-synthetic --page-date 1786 --out $B/operations/work/03-records.jsonl
```

and compare the two mention lists: that comparison, in-session reading
against API reading of the same 73 lines, is a cheap audit of the
extraction step itself.

## Rights

Inputs are machine readings of invented text; the gazetteer and tile rights
are as in `01-places-to-map`.
