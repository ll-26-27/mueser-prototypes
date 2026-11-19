# Footnotes: summary

**Purpose.** Check a book-length manuscript's footnotes against its
bibliography and against the configured citation style, report every
fault with its location and a proposed fix, and apply only what Ben
decides.

**Workflow.** `extract` writes the notes and the bibliography entries as
JSON lines, each note with its chapter heading. `check` runs nine named
deterministic rules (numbering, ibid. chains, page ranges, terminal
punctuation, quotation marks, short forms without an entry, first
citations not in full, uncited entries, variant titles); with `--model`
it asks a model about the short-form pairs the rules could not settle and
writes its answers to `review.csv` as proposals. `report` renders one page
of findings. `apply` edits a copy for decided rows only, with a diff.

**Findings.** None yet: scoped 5 November 2026, moved into this
repository 19 November 2026, not built.

**Limits.** The rules encode Chicago notes-bibliography until Ben names
his style; `S.`/`p.` and quotation conventions are config, not detected.
Bibliography parsing is best-effort and keeps failures as `parsed: false`.
The model sees only ambiguous pairs and only when asked.
