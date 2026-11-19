# Footnotes: file by file

| path | what it is | made by |
|---|---|---|
| `README.md` | what the case will do and how Ben runs it | hand |
| `summary.md` | purpose, workflow, findings, limits | hand |
| `HANDOFF.md` | the brief (5 November 2026, moved here 19 November) | hand |
| `CLAUDE.md` | rules for assistants in this folder | hand |
| `inputs/README.md` | what Ben drops in `inputs/book/` | hand |
| `inputs/book/` | the manuscript (`.docx`, chapters, or `main.tex` + `.bib`); gitignored | Ben |
| `inputs/config/book.yml`, `*.csl` | the citation style and its conventions, the thresholds | hand |
| `inputs/fixtures/synth-chapter.docx`, `synth-chapter.tex`, `synth-refs.bib` | a synthetic chapter with planted faults | `operations/00-make-fixtures.py` |
| `operations/0*-*.sh` | the exact commands | hand |
| `outputs/out/<run_id>/work/footnotes.jsonl`, `bibliography.jsonl` | the extracted notes and entries | `book extract` |
| `outputs/out/<run_id>/review.csv` | every finding with rule, proposed fix, candidate, score, model if any, and the decision columns | `book check`, then Ben |
| `outputs/out/<run_id>/report.html` | the findings as one page | `book report` |
| `outputs/out/<run2>/<manuscript>.docx`, `diff.html`, `run.json` | the copy with decided fixes applied; gitignored | `book apply` |

Code: `src/mueser/style/book/`, shared parts in `src/mueser/style/shared/`. Raw model replies: `cache/openrouter/`.
