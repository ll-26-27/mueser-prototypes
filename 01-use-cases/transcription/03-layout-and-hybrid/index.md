# Layout and hybrid: file guide

- `README.md`, `summary.md`, `CLAUDE.md`.
- `inputs/pages-print/`, `inputs/pages-hand/`: the six real pages, copied from use cases 01 and 02; `inputs/gt/`: their ground truth.
- `inputs/work/crops/<page>/`: the line crops the hybrid mode read (ignored by git? no: small PNGs, kept for inspection).
- `operations/work/layout/<page>.layout.json` and `runs/<run_id>/run.json`: the layout pass.
- `outputs/layout.html`: the overlay. `outputs/index.html` (print) and `outputs/index-hand.html` (handwriting): the hybrid bake-offs. `outputs/bakeoff_*.{csv,json}`, `outputs/runs/`, `outputs/consensus-*/`.
