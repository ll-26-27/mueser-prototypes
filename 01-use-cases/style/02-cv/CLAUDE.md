# CLAUDE.md — CV

Read the repository `CLAUDE.md` and the group brief `../HANDOFF.md`
first; `HANDOFF.md` here is the case's brief and `README.md` says what
exists. In this folder:

- Never overwrite an input. `render` edits a copy in
  `outputs/out/<run_id>/` with a `run.json`.
- Geometry from the source: page size, margins, fonts, indents and tab
  stops are read from Ben's document, never from library defaults. A new
  entry clones a sibling entry's paragraph XML (`w:p` with its `w:pPr`
  and run properties) and replaces only the run text.
- Never shrink to fit. If a change grows the page count, `check` reports
  it and stops. Ben decides what to cut.
- Existing entries stay byte-identical unless `cv.yml` changed their
  text; sections, headers, footers and page geometry are never touched.
- No model is involved in this case.
- `inputs/cv/` and `outputs/out/` are ignored by git. `inputs/config/cv.yml`
  is Ben's CV as data: commit it only if he agrees. Fixtures are synthetic,
  named `synth-*`, in `inputs/fixtures/`.
- LibreOffice (`soffice`) is needed for page counts; skip with a message
  when absent.

Commands, from the repository root:

```sh
uv run python -m mueser.style cv extract <cv.docx> --out <case>/inputs/config/cv.yml
uv run python -m mueser.style cv render  --cv <case>/inputs/config/cv.yml --source <cv.docx> --out <case>/outputs/out/
uv run python -m mueser.style cv check   --before <cv.docx> --after <case>/outputs/out/<run>/cv.docx
```
