# HANDOFF — footnotes: a book's notes checked against its bibliography

**Owner:** Madeleine (Bok Center Learning Lab), for Ben
**Status:** Scoped 5 November 2026 (as part c of the `mueser-style` brief); moved here 19 November 2026. Nothing built. Ben's manuscript is not here yet.
**Audience:** a coding agent building this case. Read the repository `CLAUDE.md`, then the group brief [`../HANDOFF.md`](../HANDOFF.md) for the shared package `src/mueser/style/shared/`, then this file.

---

## 1. Context

Ben wants to go through a book-length manuscript and check the footnotes and the bibliography against each other: short forms that match no entry, entries never cited, broken ibid. chains, inconsistent page ranges and punctuation. Formats: Word (`.docx`) first, LaTeX second. Citation style: not yet known; assume Chicago notes-bibliography and keep it as a config value.

What this is not: a citation rewriter. Rules find faults and propose fixes; a model is asked only about pairs the rules could not settle; nothing in the manuscript changes without a recorded decision.

---

## 2. Layout

```
01-use-cases/style/03-footnotes/
├── README.md · HANDOFF.md · CLAUDE.md · summary.md · index.md
├── inputs/
│   ├── README.md
│   ├── book/                 # gitignored: manuscript.docx or chapters/, or main.tex + refs.bib
│   ├── config/               # committed: book.yml, the .csl file
│   └── fixtures/             # committed: synth-chapter.docx (40 footnotes, a bibliography, planted faults); synth-chapter.tex + synth-refs.bib
├── operations/               # 00-make-fixtures.py, 01-extract.sh, 02-check.sh, 03-report.sh, 04-apply.sh
└── outputs/out/<run_id>/     # gitignored: work/, review.csv, report.html, the edited copy, diff.html, run.json
```

Code: `src/mueser/style/book/{extract,rules,check,report,apply}.py`, commands `python -m mueser.style book {extract,check,report,apply}`. Model calls through `src/mueser/shared/openrouter.py`, cached in `cache/openrouter/`.

---

## 3. Components

**`python -m mueser.style book extract <manuscript.docx | main.tex> --out outputs/out/<run>/work/`**
Writes `footnotes.jsonl` (number, chapter or section heading above it, paragraph index, the full text of the note) and `bibliography.jsonl` (each entry's raw text and a parse into author, title, container, place, publisher, year, pages, where the parse succeeds; failures kept with `parsed: false`). Word footnotes come from `word/footnotes.xml` joined to their anchors in `document.xml`; LaTeX from `\footnote{}` and `\autocite`/`\cite` with the `.bib` file. The chapter heading is recorded so a finding can be located without a page number.

**`python -m mueser.style book check --work outputs/out/<run>/work/ --config inputs/config/book.yml [--model]`**
Deterministic rules first, each named and each producing findings with the note number, chapter, text, rule id and a proposed fix:

| rule | what it catches |
|---|---|
| `numbering` | gaps or repeats in note numbers per chapter |
| `ibid-chain` | ibid. / ebd. following a note that cites a different work, or following a note with several works |
| `page-range` | hyphen where the style wants an en dash; `p.`/`pp.`/`S.` inconsistent; ranges like 123–4 vs 123–124 mixed |
| `terminal` | notes without terminal punctuation, or with two |
| `quotes` | straight quotation marks, or German and English marks mixed against the configured convention |
| `short-form` | a short-form note (author, short title, pages) with no bibliography entry whose author and title match (rapidfuzz, threshold recorded) |
| `first-full` | a work whose first citation is not the full form the style requires |
| `uncited` | bibliography entries never cited |
| `variants` | one work cited with different titles, years or author spellings |

Then, **only if `--model` is passed**, a model pass over the ambiguous note-to-entry pairs (`short-form` findings whose best match scores between the low and high thresholds): the model sees the note and the candidate entries and says which, or none. Its answers go to `review.csv` as `proposed`, with model, prompt hash and cache key. The style comes from `inputs/config/book.yml` (`style: chicago-notes-bibliography`, a CSL path, language conventions for quotes and `S.` vs `p.`).

**Short forms are resolved, never guessed** (Ben's question of 19 November 2026, answered in the README). A short form such as *Woods 2006* is expanded only when exactly one bibliography entry matches it by author and year (and title word, if the note gives one) at or above `short_form.high`; between the thresholds it is a `short-form` proposal; below `short_form.low`, or with two entries that match equally, it is an `unresolved` finding whose proposed fix is empty and whose text asks Ben which source is meant. The model pass sees only entries from Ben's own bibliography as candidates and may answer "none". Ben's likely style is OSCOLA (OUP's law list; 4th edition, 2012; `oscola.csl` exists in the CSL repository), to be confirmed from his editor's guidelines; `book.yml` takes `style: oscola` and the CSL path.

**`python -m mueser.style book report --work … --out outputs/out/<run>/report.html`**
One page: counts by rule, then every finding with the note text, its location, the rule, the proposed fix and a decision cell. Readable without the manuscript open.

**`python -m mueser.style book report --work … --out outputs/out/<run>/report.html` is also the review step.** Every row of `review.csv` appears with its decision cell; Ben fills the cell (in the CSV, or in the page served the way the reading room is served, with the decisions appended to a log), and nothing is applied until he has. This is the check at the end he asked for: the proposed changes as a list, read before any edit, with no need to carry context into Zotero or a plugin.

**`python -m mueser.style book apply --source <manuscript.docx> --decisions outputs/out/<run>/review.csv --out outputs/out/<run2>/`**
Edits a copy, only for rows with a decision, only in the footnote or bibliography paragraph named, and writes a diff. Model output never changes a note without a decision in the CSV. Text outside notes and bibliography is never touched.

---

## 4. Data model

- `work/footnotes.jsonl`: `{n, chapter, para_index, text, cites: [{author, short_title, pages, kind: full|short|ibid}]}`.
- `work/bibliography.jsonl`: `{index, raw, parsed, author, title, container, place, publisher, year, pages}`.
- `review.csv`: `finding_id, rule, note_n, chapter, text, proposed_fix, candidate, score, model, prompt_sha256, status(proposed|accepted|rejected), decision, decided_by, decided_at`.
- `config/book.yml`: `{style: chicago-notes-bibliography, csl: <path>, quotes: german|english, pages: S.|p., range_dash: en, short_form: {low: 0.6, high: 0.9}}`.
- `outputs/out/<run>/run.json`: command, inputs with sha256, parameters, outputs, counts (findings by rule, pairs sent to the model), model and cost if any, timings.

---

## 5. Credentials

`OPENROUTER_API_KEY`, used only by `book check --model`. `extract`, the deterministic `check`, `report` and `apply` run without a key; without it `--model` says the pass was skipped.

---

## 6. Build order and done criteria

| phase | work | done when |
|---|---|---|
| 1 | fixture `synth-chapter.docx` with 40 footnotes and a bibliography, faults planted by `operations/00-make-fixtures.py` | `uv run pytest -q` green; `text()` round-trips it |
| 2 | `book extract` + deterministic `check` + `report` | on `synth-chapter.docx` with planted faults (one gap, two broken ibid., three hyphen ranges, two orphan short forms, one uncited entry) every fault is found and nothing else is |
| 3 | `book check --model` + `apply` | ambiguous pairs go to `review.csv` as proposed; `apply` changes only decided rows; a diff shows them and nothing else |
| 4 | LaTeX path; README for Ben | the same planted faults in a `.tex` + `.bib` fixture are found |

Then Ben's manuscript: `extract` and `check` with no model, show him the report, then decide together whether the model pass is worth running.

---

## 7. Conventions

Those of the group brief (`../HANDOFF.md` §6): never overwrite an input; deterministic checks before model judgment; every model answer a proposal until decided; model calls cached with model name and prompt hash, raw reply kept; `inputs/book/` and `outputs/out/` not committed; fixtures named `synth-*`; the manuscript goes to a model whole, never cut, and if it exceeds a model's limit the error is surfaced and the run split into whole-document passes.

---

## 8. Open questions for Ben

- Which citation style does the book use, and which conventions: `S.` or `p.`, German or English quotation marks, en dash in ranges?
- Does he use Zotero? A CSL-JSON or Better BibTeX export of his library would make `short-form` matching much stronger.
- How are his chapters stored: one file or one per chapter? Footnote numbering restarts per chapter?
- Are any chapters in LaTeX?

---

## 9. References

- python-docx: https://python-docx.readthedocs.io/ (no footnote API; read `word/footnotes.xml` with lxml).
- Office Open XML `w:footnotes`, `w:footnoteReference`: ECMA-376 Part 1, §17.11.
- citeproc-py: https://github.com/citeproc-py/citeproc-py · CSL styles: https://github.com/citation-style-language/styles (`chicago-note-bibliography.csl`).
- rapidfuzz: https://github.com/rapidfuzz/RapidFuzz · bibtexparser: https://github.com/sciunto-org/python-bibtexparser · TexSoup: https://github.com/alvinwan/TexSoup
- Chicago Manual of Style, 17th ed., ch. 14 (notes and bibliography), for the rule definitions.
- Group brief: [`../HANDOFF.md`](../HANDOFF.md).
