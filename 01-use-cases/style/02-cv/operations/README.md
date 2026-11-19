# Operations

Numbered steps, run from the repository root, in order. Each takes the CV's
path as its first argument and uses the synthetic CV when none is given.

- `00-make-fixtures.py` writes the synthetic CV.
- `01-extract.sh [cv.docx] [cv.yml]` reads the CV into data and reports its geometry.
- `02-render.sh [cv.docx] [cv.yml]` writes a copy with the entries added in the data file.
- `03-check.sh <before.docx> <after.docx>` compares page counts (needs LibreOffice).

With no arguments, `01` writes `outputs/out/synth-cv.yml` so that a real
`inputs/config/cv.yml` is never in its way.
