# Handouts: file by file

| path | what it is | made by |
|---|---|---|
| `README.md` | what the case will do and how Ben runs it | hand |
| `summary.md` | purpose, workflow, findings, limits | hand |
| `HANDOFF.md` | the brief (5 November 2026, moved here 19 November) | hand |
| `CLAUDE.md` | rules for assistants in this folder | hand |
| `inputs/README.md` | what Ben drops in `inputs/handouts/` | hand |
| `inputs/handouts/*.docx` | his handouts; gitignored | Ben |
| `inputs/config/house-style.yml` | the inferred majority style with per-document values | `handout infer` |
| `inputs/config/reference.docx` | his most representative handout with named styles | `handout infer` |
| `inputs/config/report.html` | each handout against the proposed norm | `handout infer` |
| `inputs/config/roles.yml` | the ordered paragraph-to-role rules | hand, from `infer`'s proposal |
| `inputs/config/course.yml`, `fields.yml`, `*.csl` | course facts, field mapping, citation style | hand |
| `inputs/fixtures/synth-handout-*.docx` | synthetic handouts for tests | `operations/00-make-fixtures.py` |
| `operations/0*-*.sh` | the exact commands | hand |
| `outputs/out/<run_id>/<name>.docx`, `diff.html`, `run.json` | a restyled or updated handout and what changed; gitignored | `norm`, `update` |

Code: `src/mueser/style/handout/`, shared parts in `src/mueser/style/shared/`.
