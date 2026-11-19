# Handouts: summary

**Purpose.** Norm Ben's class handouts to one house style inferred from
the handouts themselves, and update a handout for a new term (readings,
year, course name, meeting times) from one file of course facts.

**Workflow.** `infer` reads every handout and writes the majority value of
each formatting property, a reference document whose named styles carry
those values, and a report of what would change; Ben agrees the style
before anything is applied. `norm` maps each paragraph to a role by a
recorded rule table, applies the reference style, writes a copy and a
diff, and fails if the text is not identical before and after. `update`
replaces marked fields from `course.yml` and renders the reading list
through citeproc in the configured style.

**Findings.** None yet: scoped 5 November 2026, moved into this
repository 19 November 2026, not built.

**Limits.** Inference is majority voting over a handful of documents;
with three handouts a two-to-one split is the norm. A paragraph no rule
matches is listed, not styled. LibreOffice is needed for PDF previews and
is not installed on the build machine as of 5 November.
