#!/bin/sh
# Step 04: open the page on 127.0.0.1 so that every decision and note is appended to outputs/reading/log.jsonl as it is made.
uv run python -m mueser.reading serve --case 01-use-cases/transcription/04-reading-room --who "${1:-ben}"
