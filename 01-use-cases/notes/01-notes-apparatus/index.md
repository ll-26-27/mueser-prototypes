# Notes apparatus: file by file

| path | what it is | made by |
|---|---|---|
| `README.md` | what the case will do and how Ben runs it | hand |
| `summary.md` | purpose, workflow, findings, limits | hand |
| `HANDOFF.md` | the brief (5 November 2026, moved here 19 November) | hand |
| `CLAUDE.md` | rules for assistants in this folder | hand |
| `inputs/README.md` | what Ben drops where | hand |
| `inputs/config/projects.yml`, `themes.yml`, `rules.yml` | controlled lists and recorded auto-accept rules; start empty | hand, then accepted proposals |
| `inputs/inbox/{email,voice,text,pdf,zotero}/` | Ben's files; gitignored | Ben |
| `inputs/fixtures/synth-*` | synthetic items for tests | `operations/00-make-fixtures.py` |
| `operations/0*-*.sh`, `05-review.md` | the exact commands; how to work in the page | hand |
| `outputs/index.html` | the viewer, self-contained | `build` |
| `outputs/store/raw/<sha256>.<ext>` | immutable copy of every ingested file; gitignored | `ingest` |
| `outputs/store/notes.sqlite` | the database; gitignored, rebuildable from raw plus log | `ingest`, `enrich`, `apply` |
| `outputs/store/log.jsonl` | every review action, append-only; gitignored | the page through `serve`, or `log ingest` |
| `outputs/inbox/` | exported browser logs waiting for `log ingest`; gitignored | the page's Export button |
| `outputs/exports/<project>.md` | one digest per project, items whole; gitignored | `export` |

Code: `src/mueser/notes/`, prompts in `src/mueser/notes/prompts/`. Raw model replies: `cache/openrouter/`.
