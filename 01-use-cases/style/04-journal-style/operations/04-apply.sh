#!/bin/sh
# Write the accepted rows into a copy of the synthetic draft. Run from the repository root.
CASE=01-use-cases/style/04-journal-style
set -x
uv run python -m mueser.style journal apply --source $CASE/inputs/fixtures/synth-article.docx \
    --run $CASE/outputs/out/synth-check --run-id synth-apply
