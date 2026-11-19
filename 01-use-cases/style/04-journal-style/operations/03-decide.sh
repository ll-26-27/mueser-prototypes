#!/bin/sh
# Accept four rules as "demo". Run from the repository root.
CASE=01-use-cases/style/04-journal-style
set -x
uv run python -m mueser.style journal decide --run $CASE/outputs/out/synth-check --who demo --accept \
    --rule spelling-ize --rule spelling-british-american --rule quote-primary --rule range-dash
