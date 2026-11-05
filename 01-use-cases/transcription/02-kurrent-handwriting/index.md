# Kurrent handwriting: file guide

- `README.md`, `summary.md`, `CLAUDE.md`: as in the Fraktur use case.
- `inputs/pages/`: `synth-01.png` … `synth-03.png` (with `.json` render
  records) and three `real-*.jpg` from Wikimedia Commons.
- `inputs/gt/`: one `.txt` per page, `provenance.json`, raw `.wikitext`.
- `inputs/synthetic-text/briefe.txt` and its README.
- `operations/00-make-synthetic-pages.py`, `operations/01-fetch-ground-truth.py`.
- `outputs/index.html`, `outputs/bakeoff_<run_id>.{csv,json}`,
  `outputs/runs/<run_id>/`.
