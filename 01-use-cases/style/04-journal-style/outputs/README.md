# Outputs

One folder per run under `out/<run_id>/`. A check run holds `review.csv`,
`report.html`, `decisions.jsonl` once anything is decided, `work/` with
the extracted paragraphs, and `run.json`. An apply run holds the edited
copy, `diff.html` and `run.json`. `out/` is gitignored because it holds
your draft.
