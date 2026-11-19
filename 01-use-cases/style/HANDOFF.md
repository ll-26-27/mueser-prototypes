# HANDOFF — style: handouts, CV and footnotes to one standard

**Owner:** Madeleine (Bok Center Learning Lab), for Ben
**Status:** Scoped 5 November 2026 as the private sibling repository `mueser-style`; moved into this repository on 19 November 2026 as three atomic cases. Nothing built. Ben's documents are not here yet.
**Audience:** a coding agent (CLI) building the three cases under `01-use-cases/style/`. Read the repository `CLAUDE.md` first, then this file for the shared package, then the case's own `HANDOFF.md`: [`01-handouts/HANDOFF.md`](01-handouts/HANDOFF.md), [`02-cv/HANDOFF.md`](02-cv/HANDOFF.md), [`03-footnotes/HANDOFF.md`](03-footnotes/HANDOFF.md). Each is complete on its own; this file holds what they share.

---

## 1. Context

Ben asked for help with three formatting chores that eat his time and that he wants done the same way every time:

- **a) Class handouts.** Norm his existing handouts to one "house style", and have a quick way to update them for a new term: new readings, year, course name, meeting times. → `01-handouts/`
- **b) The CV.** Add entries while keeping the same page size, margins, indentation and tab stops, so the document still looks like his CV and does not reflow unexpectedly. → `02-cv/`
- **c) Book-length work.** Go through a manuscript and check the footnotes and the bibliography against each other: short forms that match no entry, entries never cited, broken ibid. chains, inconsistent page ranges and punctuation. → `03-footnotes/`

Formats: Word (`.docx`) first, LaTeX second; he may have others. Citation style: not yet known; assume Chicago notes-bibliography and keep it as a config value.

What this is not: a document generator. Every command here takes one of Ben's documents, changes as little as possible, writes the result to a new place, and reports what changed and what it refused to change.

---

## 2. Layout

The package is `src/mueser/style/`, one subpackage per case plus `shared/`, called as `python -m mueser.style {handout,cv,book} …` from the repository root. Each case folder follows the repository shape.

```
src/mueser/style/
├── shared/               # docx.py (open, save-as, text extraction, paragraph XML clone), pdf.py (LibreOffice headless, page count), runs.py, diff.py
├── handout/              # infer.py, norm.py, update.py          → 01-handouts
├── cv/                   # extract.py, render.py, check.py        → 02-cv
├── book/                 # extract.py (docx + latex), rules.py, check.py, report.py, apply.py   → 03-footnotes
└── __main__.py           # typer: python -m mueser.style {handout,cv,book} …

01-use-cases/style/<case>/
├── README.md             # for Ben: what each command does, how to run it, what to check afterwards
├── HANDOFF.md            # the case's brief
├── CLAUDE.md             # rules for assistants in that folder
├── summary.md · index.md
├── inputs/               # Ben's documents: gitignored except README.md, config/ and fixtures/
│   ├── README.md         # what belongs here
│   ├── config/           # committed: house-style.yml, roles.yml, course.yml, fields.yml (01); cv.yml (02); book.yml, *.csl (03)
│   └── fixtures/         # committed: synthetic documents for tests, every filename starts with synth-, made by operations/00-make-fixtures.py
├── operations/           # numbered scripts: the exact invocations
└── outputs/
    └── out/<run_id>/     # gitignored: results, diff.html, report.html, run.json
```

Model calls go through the repository's cached OpenRouter client (`src/mueser/shared/openrouter.py`) and the shared cache in `cache/openrouter/`; `.env` holds `OPENROUTER_API_KEY` as elsewhere in this repository. Extras in `pyproject.toml`: `[docx]`, `[latex]`.

Dependencies: `python-docx` and `lxml` (footnotes and paragraph XML are not reachable through python-docx's API, so read `word/footnotes.xml` and clone `w:p` elements directly); LibreOffice headless (`soffice --headless --convert-to pdf`) for page counts and PDF previews, installed with `brew install --cask libreoffice` (**not installed on Madeleine's machine as of 5 November; the brief assumes it will be**); `pypdf` to count pages; `citeproc-py` and a CSL file to render reading lists; `rapidfuzz` for note-to-entry matching; `TexSoup` or regex plus `bibtexparser` for LaTeX; `rich` and `typer`.

---

## 3. The shared package

`shared/docx.py`: open a `.docx`, save a copy to a run folder (never in place), `text()` that extracts the document's text in order including footnotes, a paragraph deep-copy that keeps `w:pPr` and every `w:rPr`, and run-text replacement part by part. `shared/pdf.py`: LibreOffice headless conversion and `pypdf` page count, skipping with a clear message when `soffice` is absent. `shared/runs.py`: run folders under `outputs/out/<run_id>/` with `run.json` (command, inputs with sha256, parameters, outputs, counts, model and cost if any, timings). `shared/diff.py`: paragraph-level HTML diff of formatting and of text.

The one rule every case enforces through `shared`: after any formatting-only operation, the extracted text before and after is **identical** (`shared.docx.text()` on both; assert, and fail the run if not).

---

## 4. Credentials

`OPENROUTER_API_KEY`, used only by `book check --model` in `03-footnotes`. Everything else runs without a key. LibreOffice is a local install, not a credential, but `cv check` and the PDF previews skip with a clear message when `soffice` is absent.

---

## 5. Build order across the three cases

| phase | case | work | done when |
|---|---|---|---|
| 1 | shared | scaffold; `shared/` (open, save-as, `text()`, paragraph clone, LibreOffice PDF, page count, run folders, HTML diff); synthetic fixtures in each case's `inputs/fixtures/` (`synth-handout-*.docx`, `synth-cv.docx`, `synth-chapter.docx` with 40 footnotes and a bibliography, all generated by `operations/00-make-fixtures.py`) | `uv run pytest -q` green on a fresh clone; `text()` round-trips a fixture |
| 2 | 02-cv | `cv extract` / `render` / `check` | three entries added to `synth-cv.docx` appear with the sibling's indents and tabs (compare the `w:pPr` XML); `check` reports an unchanged page count; a fourth entry that overflows is reported and the run stops |
| 3 | 01-handouts | `handout infer` / `norm` | `infer` over three synthetic handouts with deliberately different fonts proposes the majority; `norm` on the odd one out produces identical text (asserted) and the reference styles; its one unmapped paragraph is listed |
| 4 | 01-handouts | `handout update` | a term change replaces every dated field and renders four readings in Chicago through citeproc; the diff lists exactly those changes |
| 5 | 03-footnotes | `book extract` + deterministic `check` + `report` | on `synth-chapter.docx` with planted faults (one gap, two broken ibid., three hyphen ranges, two orphan short forms, one uncited entry) every fault is found and nothing else is |
| 6 | 03-footnotes | `book check --model` + `apply` | ambiguous pairs go to `review.csv` as proposed; `apply` changes only decided rows; a diff shows them and nothing else |
| 7 | 03-footnotes, 01-handouts | LaTeX path for `book` (and `handout` if Ben has LaTeX handouts); README for Ben | the same planted faults in a `.tex` + `.bib` fixture are found |

The CV case is first because it is the smallest and the most valuable. Then Ben's documents: run `cv extract` and `handout infer` on his files first, show him the reports, and only then norm or render.

---

## 6. Conventions

- Never overwrite an input. Every command writes to `outputs/out/<run_id>/` with a `run.json`.
- After any formatting-only operation, assert that the extracted text is identical before and after. A failed assertion fails the run.
- Page geometry, fonts and styles are read from the source document, never from library defaults.
- Deterministic checks run before any model judgment; a model is only asked about what the rules could not settle, and its answer is a proposal until decided.
- Model calls are cached with model name and prompt hash and the raw reply is kept.
- `inputs/` (except `README.md`, `config/`, `fixtures/`) and `outputs/out/` are not committed. Fixtures are synthetic and named `synth-*`.
- Python 3.12, `uv`, type hints, `typer`, `pydantic` for the YAML models, `ruff`, `pytest`.

---

## 7. Open questions for Ben

- Which citation style does the book use, and which conventions: `S.` or `p.`, German or English quotation marks, en dash in ranges?
- Does he use Zotero? A CSL-JSON or Better BibTeX export of his library would make `short-form` matching much stronger.
- Does he want the house style as a Word template he can apply himself in Word (`reference.docx` with a style gallery), or only as the `norm` command?
- Are any handouts or chapters in LaTeX, Google Docs or Pages?
- How are his chapters stored: one file or one per chapter? Footnote numbering restarts per chapter?

---

## 8. References

- python-docx: https://python-docx.readthedocs.io/ (no footnote API; read `word/footnotes.xml` with lxml).
- Office Open XML `w:footnotes`, `w:footnoteReference`: ECMA-376 Part 1, §17.11.
- LibreOffice headless conversion: `soffice --headless --convert-to pdf --outdir <dir> <file>`.
- citeproc-py: https://github.com/citeproc-py/citeproc-py · CSL styles: https://github.com/citation-style-language/styles (`chicago-note-bibliography.csl`).
- Chicago Manual of Style, 17th ed., ch. 14 (notes and bibliography), for the rule definitions.
- Repository conventions: `CLAUDE.md` and `context/roadmap.md`.
