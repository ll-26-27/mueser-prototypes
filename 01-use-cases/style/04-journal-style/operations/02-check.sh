#!/bin/sh
# List where the synthetic draft differs from the profile. Run from the repository root. Pass --citations to add the model pass.
CASE=01-use-cases/style/04-journal-style
set -x
uv run python -m mueser.style journal check $CASE/inputs/fixtures/synth-article.docx \
    --profile $CASE/outputs/out/synth-profile.yml --run-id synth-check "$@"
