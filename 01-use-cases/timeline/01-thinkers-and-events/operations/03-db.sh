#!/bin/sh
# Everything into outputs/timeline/timeline.sqlite and timeline.json (latest collect run, sources, latest proposals, the log).
cd "$(dirname "$0")/../../../.." || exit 1
uv run python -m mueser.timeline db --case 01-use-cases/timeline/01-thinkers-and-events
