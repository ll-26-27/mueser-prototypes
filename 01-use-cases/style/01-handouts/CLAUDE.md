# CLAUDE.md — Handouts

Read the repository `CLAUDE.md` and the group brief `../HANDOFF.md`
first; `HANDOFF.md` here is the case's brief and `README.md` says what
exists. In this folder:

- Never overwrite an input. Every command writes to `outputs/out/<run_id>/`
  with a `run.json` naming the command, the inputs with their sha256, the
  parameters, the outputs and the counts.
- Text identity after formatting: after `norm` the extracted text before
  and after must be identical. Assert it; a failed assertion fails the run.
- Geometry from the source: page size, margins, fonts, indents and tab
  stops come from Ben's handouts, never from library defaults.
  `reference.docx` is a copy of his most representative handout with its
  styles renamed, not a blank document.
- Unmapped means listed: a paragraph no rule in `roles.yml` matches is left
  as it was and named in the report. Nothing is guessed.
- `infer` is deterministic; no model is involved in this case.
- `inputs/handouts/` and `outputs/out/` are ignored by git. Fixtures are
  synthetic and named `synth-*`; they live in `inputs/fixtures/`.
- Nothing is cut: a document is read whole.

Commands, from the repository root:

```sh
uv run python -m mueser.style handout infer  <handouts…> --out <case>/inputs/config/
uv run python -m mueser.style handout norm   <in.docx> --style <case>/inputs/config/ --out <case>/outputs/out/
uv run python -m mueser.style handout update <in.docx> --course <case>/inputs/config/course.yml --out <case>/outputs/out/
```
