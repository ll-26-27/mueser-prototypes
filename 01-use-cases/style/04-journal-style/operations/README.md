# Operations

Numbered steps on the synthetic files, run from the repository root, in
order. Each prints the command it runs; use the same command with your own
paths.

- `00-make-fixtures.py` writes the synthetic draft and articles.
- `01-profile.sh` counts the synthetic journal's conventions into `outputs/out/synth-profile.yml`.
- `02-check.sh` lists where the synthetic draft differs (run folder `synth-check`).
- `03-decide.sh` accepts the spelling, quotation-mark and range rules as `demo`.
- `04-apply.sh` writes the accepted rows into a copy (run folder `synth-apply`).

`01` and `02` take `--citations` as an argument to add the model passes
(needs `OPENROUTER_API_KEY`). Run folders are never overwritten: remove
`outputs/out/synth-*` to run the sequence again.
