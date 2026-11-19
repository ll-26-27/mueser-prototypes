# CLAUDE.md — Journal style

Read the repository `CLAUDE.md` first; `README.md` here says what exists
and what was run. In this folder:

- Never overwrite an input, a profile or a run folder. `apply` writes a
  copy under `outputs/out/<run_id>/` with a `run.json`.
- Never silently pick. A convention is the journal's only above the
  recorded threshold; below it `decision` stays empty for a person. Do not
  fill a decision in for Ben.
- Nothing changes without a recorded decision. `apply` writes only rows
  whose status is `accepted`, and checks the copy against the expected text.
  Keep that check, and fail the run when it fails.
- Quoted matter is not respelled. Spelling and other body rules do not
  run in notes, the bibliography, block quotations, quotation marks or
  italics. Do not widen their scope to raise a count.
- A model's restyled note is a proposal. Keep the word check, the range
  check and the model, prompt hash and cache key on every row.
- Samples and notes go to the model whole. If a request exceeds the
  model's limit, surface the error and split by whole article or whole
  chapter; never cut.
- Only example citations found word for word in the samples are shown to
  the model that restyles.
- Missing credentials skip, they do not crash.
- `inputs/samples/`, `inputs/draft/` and `outputs/out/` are ignored by git.
  A profile in `inputs/config/` is committed and holds short excerpts of
  the journal's articles as examples. Fixtures are synthetic, named `synth-*`.

Commands, from the repository root:

```sh
uv run python -m mueser.style journal profile <samples…> --name "<journal>" [--citations]
uv run python -m mueser.style journal check <draft.docx> --profile <case>/inputs/config/<journal>.yml [--citations]
uv run python -m mueser.style journal decide --run <run> --rule <id> --accept|--reject --who <name>
uv run python -m mueser.style journal apply --source <draft.docx> --run <run>
```
