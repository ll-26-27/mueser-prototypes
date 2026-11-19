#!/bin/sh
# Step 03 (deterministic code): the newest build + the newest translation run + the log -> outputs/index.html.
uv run python -m mueser.reading build --case 01-use-cases/transcription/04-reading-room
