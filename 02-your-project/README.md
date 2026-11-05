# Your project

Ben's workspace. Keep source material in `inputs/`, saved prompts and
scripts in `operations/`, results in `outputs/`. The use cases in
`01-use-cases/` are patterns to copy; the package in `src/mueser/` is what
their operations call.

## Starting points

**A folder of page images**

```sh
uv run python -m mueser.text.ingest folder <folder of images> 02-your-project/inputs/my-source --doc-id my-source
uv run python -m mueser.text.bakeoff run --pages 02-your-project/inputs/my-source/pages \
  --backends kraken,tesseract,openrouter --mode print --out 02-your-project/outputs
```

Add `--gt <folder>` once a few pages have been corrected (one `.txt` or
PAGE-XML per page, same stem as the image) and the run reports CER.

**A IIIF manifest** (a digitised volume at a library)

```sh
uv run python -m mueser.text.ingest iiif <manifest url> 02-your-project/inputs/my-volume --limit 10
```

**A spreadsheet of places**

```sh
uv run python -m mueser.maps.load table <file.csv|.xlsx> --db 02-your-project/operations/work/research.duckdb \
  --doc-id my-table --name-col <name column> --date-col <date column> --also-jsonl 02-your-project/operations/work/records.jsonl
uv run python -m mueser.maps.resolve run --records 02-your-project/operations/work/records.jsonl --out 02-your-project/operations/work
```

then export and build the map as in `01-use-cases/maps/01-places-to-map/README.md`.

**Transcriptions to places**

```sh
uv run python -m mueser.text.extract run --transcripts <folder of page .txt> --doc-id my-source \
  --out 02-your-project/operations/work/records.jsonl
```

needs `OPENROUTER_API_KEY`; the mention list it produces is checked
verbatim against each line, and the rejected mentions are reported.
