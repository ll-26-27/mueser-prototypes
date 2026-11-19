#!/bin/sh
# Stanford Encyclopedia entry pages (title, authors, dates) and Wikipedia lead extracts for every node, cached raw.
cd "$(dirname "$0")/../../../.." || exit 1
uv run python -m mueser.timeline sources --case 01-use-cases/timeline/01-thinkers-and-events --workers 4
