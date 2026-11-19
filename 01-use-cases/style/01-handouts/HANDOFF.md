# HANDOFF — handouts: one house style, updated each term

**Owner:** Madeleine (Bok Center Learning Lab), for Ben
**Status:** Scoped 5 November 2026 (as part a of the `mueser-style` brief); moved here 19 November 2026. Nothing built. Ben's handouts are not here yet.
**Audience:** a coding agent building this case. Read the repository `CLAUDE.md`, then the group brief [`../HANDOFF.md`](../HANDOFF.md) for the shared package `src/mueser/style/shared/`, then this file.

---

## 1. Context

Ben teaches from handouts he has made over years, in slightly different fonts, spacings and layouts. He wants them normed to one "house style", and a quick way to update a handout for a new term: new readings, year, course name, meeting times. Formats: Word (`.docx`) first, LaTeX second. Reading lists should render in the configured citation style (assume Chicago notes-bibliography; config value).

What this is not: a document generator. Each command takes one of his handouts, changes as little as possible, writes the result to a new place, and reports what changed and what it refused to change.

---

## 2. Layout

```
01-use-cases/style/01-handouts/
├── README.md · HANDOFF.md · CLAUDE.md · summary.md · index.md
├── inputs/
│   ├── README.md
│   ├── handouts/             # gitignored: his .docx handouts
│   ├── config/               # committed: house-style.yml, roles.yml, reference.docx, report.html (from infer); course.yml, fields.yml (for update); the .csl file
│   └── fixtures/             # committed: synth-handout-*.docx, made by operations/00-make-fixtures.py
├── operations/               # 00-make-fixtures.py, 01-infer.sh, 02-norm.sh, 03-update.sh
└── outputs/out/<run_id>/     # gitignored: <name>.docx, diff.html, run.json
```

Code: `src/mueser/style/handout/{infer,norm,update}.py`, commands `python -m mueser.style handout {infer,norm,update}`.

---

## 3. Components

**`python -m mueser.style handout infer inputs/handouts/*.docx --out inputs/config/`**
Reads every handout and writes three things:

- `config/house-style.yml`: page size and margins, body font and size, line spacing, heading levels with their fonts and spacing, list styles, header and footer fields, the paragraph roles found (title, course line, meeting line, section heading, reading entry, body, note) and the **majority value** of each property across the handouts, with the per-document values beside it.
- `config/reference.docx`: a document whose named styles (`Title`, `Course`, `Meeting`, `Heading 1`, `Reading`, `Body`, `Note`) carry those majority values. Built by copying the most representative handout and renaming its styles, not from a blank document, so the look is his.
- `config/report.html`: each handout's current values against the proposed norm, so Ben can see what would change before anything does.

Ben edits `house-style.yml` (or says "yes") before `norm` is run on anything. Inference is deterministic; no model is involved.

**`python -m mueser.style handout norm <in.docx> --style inputs/config/ --out outputs/out/`**
Opens the document, maps each paragraph to a role by a **recorded rule table** (`config/roles.yml`: position, existing style name, formatting signature, regex on text), applies the reference style for that role, saves to `outputs/out/<run>/<name>.docx`, and writes `diff.html` (paragraph-level before/after of formatting) and `run.json`. Paragraphs no rule matches are listed as **unmapped** and left as they were; nothing is guessed. Hard rule: the extracted text of the document before and after is **identical** (`shared.docx.text()` on both; assert, and fail the run if not).

**`python -m mueser.style handout update <in.docx> --course inputs/config/course.yml --out outputs/out/`**
`course.yml` holds the fields: course code, title, term, year, instructor, meeting pattern, room, office hours, policies, and `readings` as CSL-JSON (or a path to a `.bib`). Two ways to mark fields in a handout: a template copy with `{{course.title}}` placeholders, or `config/fields.yml` mapping old literal values to fields for an existing handout ("Fall 2025" → `course.term_year`). Readings render through citeproc in the configured CSL style, one paragraph per reading in the `Reading` style. Output in a run folder with a text diff and the list of fields replaced, with counts.

---

## 4. Data model

- `config/house-style.yml`: `{page: {size, margins}, body: {font, size, spacing}, roles: {<role>: {font, size, bold, italic, space_before, space_after, indent, numbering}}, sources: [{file, values: {...}}]}`.
- `config/roles.yml`: ordered rules `[{role, when: {style_name?, regex?, position?, signature?}}]`.
- `config/course.yml`: `{code, title, term, year, instructor, meeting, room, office_hours, policies: {...}, readings: [<CSL-JSON item>] | {bib: path}}`.
- `config/fields.yml`: `[{old: "Fall 2025", field: course.term_year}, …]`.
- `outputs/out/<run>/run.json`: command, inputs with sha256, parameters, outputs, counts (paragraphs mapped, unmapped, fields replaced), timings.

---

## 5. Credentials

None. Every command in this case runs without a key. LibreOffice is needed only for PDF previews and skips with a message when `soffice` is absent.

---

## 6. Build order and done criteria

| phase | work | done when |
|---|---|---|
| 1 | fixtures: three `synth-handout-*.docx` with deliberately different fonts, spacings and one odd paragraph, from `operations/00-make-fixtures.py` | `uv run pytest -q` green; `text()` round-trips each fixture |
| 2 | `handout infer` / `norm` | `infer` over the three fixtures proposes the majority; `norm` on the odd one out produces identical text (asserted) and the reference styles; its one unmapped paragraph is listed |
| 3 | `handout update` | a term change replaces every dated field and renders four readings in Chicago through citeproc; the diff lists exactly those changes |
| 4 | LaTeX path, if Ben has LaTeX handouts; README for Ben | the same fixture faults handled in `.tex` |

Then Ben's handouts: run `infer`, show him `report.html`, agree `house-style.yml`, then `norm`.

---

## 7. Conventions

Those of the group brief (`../HANDOFF.md` §6): never overwrite an input; text identity asserted after every formatting-only operation; geometry from the source; unmapped means listed; `inputs/handouts/` and `outputs/out/` not committed; fixtures named `synth-*`.

---

## 8. Open questions for Ben

- Does he want the house style as a Word template he can apply himself in Word (`reference.docx` with a style gallery), or only as the `norm` command?
- Are any handouts in LaTeX, Google Docs or Pages?
- Which citation style for reading lists, and does he use Zotero (a CSL-JSON export would feed `course.yml` directly)?

---

## 9. References

- python-docx: https://python-docx.readthedocs.io/ · styles and `w:pPr`: ECMA-376 Part 1, §17.3 and §17.7.
- citeproc-py: https://github.com/citeproc-py/citeproc-py · CSL styles: https://github.com/citation-style-language/styles (`chicago-note-bibliography.csl`).
- LibreOffice headless conversion: `soffice --headless --convert-to pdf --outdir <dir> <file>`.
- Group brief: [`../HANDOFF.md`](../HANDOFF.md).
