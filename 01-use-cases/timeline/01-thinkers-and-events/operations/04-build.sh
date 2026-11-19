#!/bin/sh
# timeline.json + the log -> outputs/index.html. Rerun after decisions to see them applied.
cd "$(dirname "$0")/../../../.." || exit 1
uv run python -m mueser.timeline db --case 01-use-cases/timeline/01-thinkers-and-events
uv run python -m mueser.timeline build --case 01-use-cases/timeline/01-thinkers-and-events
