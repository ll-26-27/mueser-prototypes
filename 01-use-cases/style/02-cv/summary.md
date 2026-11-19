# CV: summary

**Purpose.** Add entries to Ben's CV without changing its page size,
margins, indentation or tab stops, and tell him when a change grows the
page count instead of fitting it by force.

**Workflow.** `extract` writes the CV as data: sections, one line of
marked text per entry, a format fingerprint each, and the page geometry.
Ben adds lines in `cv.yml`. `render` edits a copy: each new entry is a
deep copy of the neighbouring paragraph's or table row's XML with its text
replaced; every other paragraph and row is then compared with the source
as canonical XML and the run fails if one differs. `check` converts before
and after to PDF and reports page count and the first page that differs,
exiting with an error if the count grew.

**Findings.** Built 19 November 2026. On the synthetic CV, three entries
added (a table row, a hanging-indent paragraph, a paragraph with its
blank spacer), one reworded, two refused as designed; paragraph and cell
properties of each new entry identical to its neighbour's. Six tests.
Not yet run on a real CV.

**Limits.** A section with no existing entry has no neighbour to copy;
such entries are refused and reported. Page counts need LibreOffice, not
installed on the build machine, so `check` has only been exercised on its
skip path. Headings are detected by rule. Run-level formatting other than
bold and italic is not carried into new text. `cv.yml` holds the CV as
data and is not committed.
