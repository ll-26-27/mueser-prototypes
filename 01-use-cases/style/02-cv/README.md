# The CV, extended without reflow

Built 19 November 2026. [`HANDOFF.md`](HANDOFF.md) is the original brief;
where the build departs from it is listed at the end.

You keep your CV as the Word file it is. The tool reads it into a small
data file, one line per entry under its section. You add an entry there as
a line of text. The tool then writes a new copy of the CV in which the new
entry is a copy of the neighbouring entry's paragraph (or table row) with
your text in it, so the indents, tab stops, fonts and spacing are exactly
that entry's. Your original file is never written to.

## Three commands

From the repository root. Put your CV at `inputs/cv/cv.docx` in this
folder (that folder is not committed), or give any path.

```sh
# 1. Read the CV into data, and report page size, margins and fonts
uv run python -m mueser.style cv extract 01-use-cases/style/02-cv/inputs/cv/cv.docx

# 2. Add entries in 01-use-cases/style/02-cv/inputs/config/cv.yml, then write the copy
uv run python -m mueser.style cv render --source 01-use-cases/style/02-cv/inputs/cv/cv.docx

# 3. Compare page counts (needs LibreOffice)
uv run python -m mueser.style cv check --before 01-use-cases/style/02-cv/inputs/cv/cv.docx \
    --after 01-use-cases/style/02-cv/outputs/out/<run>/cv.docx
```

To try it first on the synthetic CV in `inputs/fixtures/`, run the scripts
in [`operations/`](operations/).

## Adding an entry

`cv.yml` lists every entry as text. A tab is written `\t`, italic is
`*like this*`, bold is `**like this**`.

```yaml
- title: Publications
  entries:
  - id: u007
    text: "2023\t“A Synthetic Article,” *Journal of Examples* 12 (2023): 1–20."
  - text: "2022\t“An Added Article,” *Journal of Examples* 11 (2022): 5–9."   # the new line
  - id: u008
    text: "2021\t“Another Invented Piece,” *Review of Samples* 8 (2021): 45–67."
```

- A new entry goes where you put it in the list. Its format is copied from
  the entry above it, or from the entry below if it is first in its section.
  To copy a different entry's format, add `like: u008`.
- Where your CV separates entries with a blank paragraph, the new entry
  gets one too.
- In a section laid out as a table, an entry is a row and `\t` moves to the
  next cell. The text must have as many parts as the row has cells.
- Changing the `text` of an existing entry rewrites that entry's text and
  nothing else.
- Removing a line from `cv.yml` does not remove it from the CV. Nothing is
  ever deleted; the report says which entries were left in place.

## What to read afterwards

`outputs/out/<run>/report.txt` lists each entry added, which entry its
format was copied from and where it was placed, each entry reworded, and
each entry refused with the reason. A new entry is refused when its
section has no existing entry to copy, or when a table row is given the
wrong number of cells.

The run then compares every other paragraph and table row of the copy
with your original as XML. If one differs, nothing is written.

`cv check` converts both files to PDF and reports the page count before
and after and the first page that differs. If the CV grew by a page it
says so and exits with an error. It never shrinks a font or a margin to
fit; what to cut is your decision.

## What was run and checked

On the synthetic CV (`inputs/fixtures/synth-cv.docx`: a table of three
degrees, three publications with hanging indents and two tab stops, three
talks separated by blank paragraphs): three entries added, one reworded,
two refused on purpose. The new publication's paragraph properties are
identical to its neighbour's; its journal title is italic and its font is
the neighbour's; the new table row has its neighbour's cell properties;
the new talk brought its blank paragraph. Six tests in
`tests/test_style_cv.py` hold this.

Not yet run on a real CV. `cv check` has not been run at all:
LibreOffice is not installed on the machine this was built on, so the
command reports that and skips. Install it with
`brew install --cask libreoffice`.

## Limits

- Section headings are found by a rule: a heading style, or a short line
  with no tab that is all bold, all capitals or small capitals. A heading
  the rule misses is listed as an entry, which is harmless: placement
  depends only on the neighbouring entries.
- A new or reworded entry carries bold and italic as you mark them, in the
  font of the neighbour's longest run. Other run-level formatting inside
  one entry (small capitals on a single word, a hyperlink) is not carried
  into new text.
- Text boxes, content controls and tables nested inside tables are not
  read. `extract` reports how many blocks it skipped.
- LibreOffice may break lines differently from Word, so its page count can
  differ from Word's. The before-and-after comparison is like for like.

## Where the build departs from the brief

- **Position, not date order.** The brief had new entries inserted in date
  order. They go where you place them in `cv.yml`, which also covers
  sections that are not chronological.
- **Entries are whole lines of marked text**, not date, title, venue and
  note fields. CVs differ too much for fixed fields to fit.
- **Table rows are supported**, since many CVs are laid out as tables.
- **Lines per section are not reported.** That needs Word's own layout.
