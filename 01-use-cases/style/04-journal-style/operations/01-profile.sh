#!/bin/sh
# Count the synthetic journal's conventions. Run from the repository root. Pass --citations to add the model pass.
CASE=01-use-cases/style/04-journal-style
set -x
uv run python -m mueser.style journal profile $CASE/inputs/fixtures/synth-journal-sample-*.txt \
    --name "Synthetic Review" --out $CASE/outputs/out/synth-profile.yml "$@"
