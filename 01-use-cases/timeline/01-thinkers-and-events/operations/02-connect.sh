#!/bin/sh
# A model proposes typed thinker-to-event connections from each thinker's extract; needs OPENROUTER_API_KEY, skips without it.
cd "$(dirname "$0")/../../../.." || exit 1
uv run python -m mueser.timeline connect --case 01-use-cases/timeline/01-thinkers-and-events --model google/gemini-3.8-flash --run-id connect-20261119-01
