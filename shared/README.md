# Shared record schema

`record.schema.json` is the one data shape the two halves of this repository
agree on. The transcription half ends by emitting records; the maps half begins
by loading them. Nothing in between needs glue code.

A record is **one mention** of a place, person, event or organisation **in one
source**, not an entity. If Breslau appears on three pages, that is three
records; the maps half groups them by `place_uri` after resolution.

Three rules the schema enforces:

1. **The verbatim text is never lost.** `surface_form` is what the source says,
   historical spelling and all. `normalized` sits next to it and may be null.
2. **Every record points back to its page.** `source.doc_id` and
   `source.page_id` are required; `line_index` and `bbox` are kept when the
   backend produced them, so a reader can go from a dot on the map to the line
   on the page.
3. **Resolution is explicit.** `resolution_status` is `auto` (one candidate was
   far ahead and the threshold is recorded), `reviewed` (a person chose), or
   `unresolved`. Nothing is silently placed.

Dates are stored as text so that fuzzy historical dates survive (`1743~`,
`174X`, `1743/1745`); `year_start` and `year_end` are derived integers for
sorting and the time slider. The Python model in
`src/mueser/shared/record.py` validates against this file and derives the
years.

## Example

```json
{
  "id": "b1c9e2…",
  "type": "place",
  "surface_form": "Breßlau",
  "normalized": "Breslau",
  "source": {
    "doc_id": "reisetagebuch-1786",
    "page_id": "p003",
    "line_index": 7,
    "bbox": null,
    "iiif_canvas": null,
    "transcription_backend": "openrouter/qwen/qwen3-vl-30b-a3b-instruct",
    "extraction_method": "llm/anthropic/claude-haiku-4.5"
  },
  "date_start": "1786-06",
  "date_end": null,
  "year_start": 1786,
  "year_end": 1786,
  "place_uri": "https://gov.genealogy.net/BRELAUJO81SB",
  "lat": 51.1079,
  "lon": 17.0385,
  "resolution_status": "auto",
  "resolution_source": "gov",
  "confidence": 0.93,
  "notes": null
}
```
