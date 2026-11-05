# Fraktur print bake-off: file guide

- `README.md`: results, the pipeline, how to rerun and add backends.
- `summary.md`: purpose, workflow, findings in a paragraph each.
- `CLAUDE.md`: instructions for Claude Code in this folder.
- `inputs/pages/`: `synth-01.png` … `synth-05.png` (rendered; `.json`
  beside each records font, size, blur, speckle, rotation) and three
  `real-*.jpg` pages from Wikimedia Commons.
- `inputs/gt/`: one `.txt` per page; `provenance.json`; the raw `.wikitext`
  of each Wikisource page.
- `inputs/synthetic-text/`: the invented journal and its README.
- `operations/00-make-synthetic-pages.py`, `operations/01-fetch-ground-truth.py`.
- `outputs/index.html`: the explorer. `outputs/bakeoff_<run_id>.csv` and
  `.json`: the scores. `outputs/runs/<run_id>/`: every reading as text,
  PAGE-XML and JSON, plus `run.json`.
