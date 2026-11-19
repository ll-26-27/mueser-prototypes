#!/bin/sh
# Write a copy of the CV with the entries added in the data file. Run from the repository root.
CASE=01-use-cases/style/02-cv
CV=${1:-$CASE/inputs/fixtures/synth-cv.docx}
YML=${2:-$CASE/outputs/out/synth-cv.yml}
uv run python -m mueser.style cv render --cv "$YML" --source "$CV" --out "$CASE/outputs/out"
