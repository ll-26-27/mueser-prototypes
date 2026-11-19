# Journal style: file by file

| path | what it is | made by |
|---|---|---|
| `README.md` | what the commands do, what was run, limits | hand |
| `summary.md` | purpose, workflow, findings, limits | hand |
| `CLAUDE.md` | rules for assistants in this folder | hand |
| `inputs/README.md` | what goes in `inputs/` | hand |
| `inputs/samples/` | recent articles from the journal; gitignored | Ben |
| `inputs/draft/` | the draft as `.docx`; gitignored | Ben |
| `inputs/config/<journal>.yml` | the journal's profile: counts, examples, decisions, citation examples | `journal profile`, then Ben |
| `inputs/config/synth-synthetic-review.yml` | the profile of the three synthetic articles, with the model's citation examples | `journal profile --citations` |
| `inputs/fixtures/synth-article.docx`, `synth-journal-sample-{1,2,3}.txt` | a synthetic draft and three synthetic articles | `operations/00-make-fixtures.py` |
| `operations/0*-*` | the exact commands | hand |
| `outputs/out/<run_id>/review.csv` | every finding with rule, proposed text, edits, flag, model and prompt hash if any, status, who decided and when | `journal check`, then `journal decide` or Ben |
| `outputs/out/<run_id>/report.html` | the review as one page | `journal check`, `journal report` |
| `outputs/out/<run_id>/decisions.jsonl` | each decision as it was recorded | `journal decide` |
| `outputs/out/<run_id>/work/paragraphs.jsonl` | the draft's paragraphs and notes as extracted | `journal check` |
| `outputs/out/<run_id>/<draft>.docx`, `diff.html`, `run.json` | the copy with accepted rows applied | `journal apply` |

Code: `src/mueser/style/journal/` (`rules.py`, `profile.py`, `check.py`,
`report.py`, `apply.py`), shared parts in `src/mueser/style/shared/`.
Tests: `tests/test_style_journal.py`. Raw model replies:
`cache/openrouter/`.
