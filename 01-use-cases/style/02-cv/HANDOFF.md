# HANDOFF — CV: new entries, same page

**Owner:** Madeleine (Bok Center Learning Lab), for Ben
**Status:** Scoped 5 November 2026 (as part b of the `mueser-style` brief); moved here 19 November 2026. **Built 19 November 2026** on a synthetic CV; the README records what runs and where the build departs from this brief. Ben's CV is not here yet.
**Audience:** a coding agent building this case. Read the repository `CLAUDE.md`, then the group brief [`../HANDOFF.md`](../HANDOFF.md) for the shared package `src/mueser/style/shared/`, then this file.

---

## 1. Context

Ben wants to add entries to his CV while keeping the same page size, margins, indentation and tab stops, so the document still looks like his CV and does not reflow unexpectedly. Format: Word (`.docx`).

What this is not: a CV generator. The command takes his document, changes as little as possible, writes the result to a new place, and reports what changed and what it refused to change.

---

## 2. Layout

```
01-use-cases/style/02-cv/
├── README.md · HANDOFF.md · CLAUDE.md · summary.md · index.md
├── inputs/
│   ├── README.md
│   ├── cv/cv.docx            # gitignored
│   ├── config/cv.yml         # committed only if Ben agrees; it holds his CV as data
│   └── fixtures/synth-cv.docx
├── operations/               # 00-make-fixtures.py, 01-extract.sh, 02-render.sh, 03-check.sh
└── outputs/out/<run_id>/     # gitignored: cv.docx, report, run.json
```

Code: `src/mueser/style/cv/{extract,render,check}.py`, commands `python -m mueser.style cv {extract,render,check}`.

---

## 3. Components

**`python -m mueser.style cv extract inputs/cv/cv.docx --out inputs/config/cv.yml`**
Writes the CV as data: sections in order, entries per section, each entry's text split into its visible parts (date, title, venue, note) and a **format fingerprint**: paragraph style name, left and hanging indents, tab stops, alignment, space before and after, and the run-level bold/italic/small-caps pattern. Also writes a report: page size, margins, fonts, page count (via LibreOffice to PDF, then `pypdf`), and lines per section.

Ben adds entries in `cv.yml` under the section they belong to.

**`python -m mueser.style cv render --cv inputs/config/cv.yml --source inputs/cv/cv.docx --out outputs/out/`**
Edits a **copy** of the original. For each new entry it finds a sibling entry in the same section, deep-copies that paragraph's `w:p` XML (so every indent, tab, font and run property comes with it), replaces the run text part by part, and inserts it in date order. It never touches sections, page geometry, headers or footers. Existing entries are left byte-identical unless `cv.yml` changed their text, in which case only the run text changes.

**`python -m mueser.style cv check --before inputs/cv/cv.docx --after outputs/out/<run>/cv.docx`**
Converts both to PDF, reports page count, per-section line counts, and the first page on which the two differ. If the page count grew it says so and **stops**: it never shrinks fonts, margins or spacing to fit. Ben decides what to cut.

---

## 4. Data model

- `config/cv.yml`: `{document: {page, margins, fonts, pages}, sections: [{title, entries: [{id, parts: {date, title, venue, note}, fingerprint: {...}, source_index}]}]}`. New entries have no `source_index`.
- `outputs/out/<run>/run.json`: command, inputs with sha256, parameters, outputs, counts (entries added, entries changed, page count before and after), timings.

---

## 5. Credentials

None. LibreOffice is a local install, not a credential; `cv check` and the PDF page count skip with a clear message when `soffice` is absent.

---

## 6. Build order and done criteria

| phase | work | done when |
|---|---|---|
| 1 | fixture `synth-cv.docx` (three sections, entries with hanging indents and tab stops) from `operations/00-make-fixtures.py` | `uv run pytest -q` green; `text()` round-trips it |
| 2 | `cv extract` / `render` / `check` | three entries added to `synth-cv.docx` appear with the sibling's indents and tabs (compare the `w:pPr` XML); `check` reports an unchanged page count; a fourth entry that overflows is reported and the run stops |
| 3 | README for Ben | he can add an entry to `cv.yml` and get a new `cv.docx` with the report |

This is the smallest case with the highest value; build it first. Then Ben's CV: run `extract`, show him the report, and only then render.

---

## 7. Conventions

Those of the group brief (`../HANDOFF.md` §6): never overwrite an input; geometry from the source; never shrink to fit; existing entries byte-identical unless their text changed; `inputs/cv/` and `outputs/out/` not committed; fixtures named `synth-*`.

---

## 8. Open questions for Ben

- Is the CV one `.docx`, and is it the master (not a PDF export of something else)?
- Does he want `cv.yml` committed here, so the CV-as-data is versioned, or kept with the document? The repository is public, so the default is not.
- Any sections where entries are not in date order?

---

## 9. References

- python-docx: https://python-docx.readthedocs.io/ · paragraph properties `w:pPr`, tabs `w:tabs`, indents `w:ind`: ECMA-376 Part 1, §17.3.1.
- LibreOffice headless conversion: `soffice --headless --convert-to pdf --outdir <dir> <file>`; `pypdf` for the page count.
- Group brief: [`../HANDOFF.md`](../HANDOFF.md).
