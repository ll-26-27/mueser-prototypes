# CV: file by file

| path | what it is | made by |
|---|---|---|
| `README.md` | what the commands do, how to add an entry, what was checked | hand |
| `summary.md` | purpose, workflow, findings, limits | hand |
| `HANDOFF.md` | the brief (5 November 2026); departures are listed in the README | hand |
| `CLAUDE.md` | rules for assistants in this folder | hand |
| `inputs/README.md` | what Ben drops in `inputs/cv/` | hand |
| `inputs/cv/cv.docx` | the CV; gitignored | Ben |
| `inputs/config/cv.yml` | the CV as data; new entries added by hand; gitignored | `cv extract`, then Ben |
| `inputs/fixtures/synth-cv.docx` | a synthetic CV for tests and for trying the commands | `operations/00-make-fixtures.py` |
| `operations/00-make-fixtures.py`, `01-extract.sh`, `02-render.sh`, `03-check.sh` | the exact commands | hand |
| `outputs/out/<run_id>/cv.docx`, `report.txt`, `run.json` | the extended CV and its report; gitignored | `cv render` |

Code: `src/mueser/style/cv/` (`extract.py`, `render.py`, `check.py`), shared
parts in `src/mueser/style/shared/` (`docx.py`, `pdf.py`). Tests:
`tests/test_style_cv.py`.
