#!/bin/sh
# Step 02 (model judgment): two models translate each page's settled lines sentence by sentence, naming their lines.
# Needs OPENROUTER_API_KEY in .env; replies are cached under cache/openrouter/. Run 20261110-01 cost $0.098.
uv run python -m mueser.reading translate --case 01-use-cases/transcription/04-reading-room --run-id 20261110-01 \
  --models google/gemini-3.8-flash,anthropic/claude-sonnet-5.5 --min-divergence 0.35
