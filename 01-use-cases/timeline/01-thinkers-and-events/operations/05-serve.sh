#!/bin/sh
# The page on 127.0.0.1:8767, saving every decision, note and excerpt to outputs/timeline/log.jsonl as it happens.
cd "$(dirname "$0")/../../../.." || exit 1
uv run python -m mueser.timeline serve --case 01-use-cases/timeline/01-thinkers-and-events --who "${1:-ben}"
