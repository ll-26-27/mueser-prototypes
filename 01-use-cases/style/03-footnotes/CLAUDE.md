# CLAUDE.md — Footnotes

Read the repository `CLAUDE.md` and the group brief `../HANDOFF.md`
first; `HANDOFF.md` here is the case's brief and `README.md` says what
exists. In this folder:

- Never overwrite an input. Every command writes to `outputs/out/<run_id>/`
  with a `run.json`.
- Rules before models. The nine deterministic rules run first. A model is
  asked only about the `short-form` pairs whose score falls between the
  thresholds in `book.yml`, and only with `--model`. Its answer is a
  proposal in `review.csv` until a person decides.
- Model output never changes a note without a recorded decision. `apply`
  edits only decided rows, only in the footnote or bibliography paragraph
  named, and never text outside them.
- Keep the raw reply: model calls go through the repository's cached
  OpenRouter client with model name and prompt hash.
- Nothing is cut: the manuscript's notes and bibliography go to a model
  whole; if a request exceeds a model's limit, surface the error and split
  into whole-document passes.
- `inputs/book/` and `outputs/out/` are ignored by git. Fixtures are
  synthetic, named `synth-*`, in `inputs/fixtures/`, with their planted
  faults listed in `operations/00-make-fixtures.py`.
- Missing credentials skip, they do not crash: without
  `OPENROUTER_API_KEY`, `--model` reports the pass skipped.

Commands, from the repository root:

```sh
uv run python -m mueser.style book extract <manuscript.docx|main.tex> --out <case>/outputs/out/<run>/work/
uv run python -m mueser.style book check   --work <…>/work/ --config <case>/inputs/config/book.yml [--model]
uv run python -m mueser.style book report  --work <…>/work/ --out <…>/report.html
uv run python -m mueser.style book apply   --source <manuscript.docx> --decisions <…>/review.csv --out <case>/outputs/out/<run2>/
```
