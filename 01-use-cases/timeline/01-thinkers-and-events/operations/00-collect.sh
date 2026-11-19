#!/bin/sh
# Wikidata -> nodes and recorded edges, by the rules in ../inputs/rules.json (written on the first run).
# Every SPARQL reply is cached under cache/wikidata/; a repeat run with the same rules makes no request.
cd "$(dirname "$0")/../../../.." || exit 1
uv run python -m mueser.timeline collect --case 01-use-cases/timeline/01-thinkers-and-events --run-id collect-20261119-01
