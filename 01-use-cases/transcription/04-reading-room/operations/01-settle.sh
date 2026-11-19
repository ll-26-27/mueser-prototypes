#!/bin/sh
# Step 01 (deterministic code): the medoid's lines with the consensus spans remapped, anchored to the hybrid reading's boxes.
# Run from the repository root. Builds are immutable; this id was used once, on 10 November 2026.
uv run python -m mueser.reading settle --case 01-use-cases/transcription/04-reading-room --build-id b-20261110-01 --max-dist 0.55
