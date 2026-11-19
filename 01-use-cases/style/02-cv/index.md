# CV: file by file

| path | what it is | made by |
|---|---|---|
| `README.md` | what the case will do and how Ben runs it | hand |
| `summary.md` | purpose, workflow, findings, limits | hand |
| `HANDOFF.md` | the brief (5 November 2026, moved here 19 November) | hand |
| `CLAUDE.md` | rules for assistants in this folder | hand |
| `inputs/README.md` | what Ben drops in `inputs/cv/` | hand |
| `inputs/cv/cv.docx` | the CV; gitignored | Ben |
| `inputs/config/cv.yml` | the CV as data: sections, entries, fingerprints, geometry; new entries added by hand | `cv extract`, then Ben |
| `inputs/fixtures/synth-cv.docx` | a synthetic CV for tests | `operations/00-make-fixtures.py` |
| `operations/0*-*.sh` | the exact commands | hand |
| `outputs/out/<run_id>/cv.docx`, `report.txt`, `run.json` | the extended CV and the check report; gitignored | `render`, `check` |

Code: `src/mueser/style/cv/`, shared parts in `src/mueser/style/shared/`.
