# Journal style: summary

**Purpose.** Bring a draft to the house style of the journal it is going
to, from a few of the journal's recent articles, with every change listed
and decided before it is made.

**Workflow.** `profile` counts fifteen conventions in the sample articles
and records one as the journal's only above a threshold (80 per cent of at
least five hits); with `--citations` a model returns example citations,
each kept only if it occurs word for word in the samples. `check` lists
every place the draft differs as a row in `review.csv`, proposing an edit
where the change is mechanical and flagging where it is not; with
`--citations` a model restyles the notes, each a proposal compared word by
word with the original. `decide` records decisions with a name and time.
`apply` writes accepted rows into a copy and reads it back against the
expected text.

**Findings.** Built 19 November 2026 and run on synthetic files only:
12 of 15 rules decided from three invented articles; 24 findings on an
invented draft; 17 accepted rows applied and verified. In two live runs
the model restyled a page range into a first page and a pinpoint the draft
never gave, which the word check does not catch in its second form.
Eleven tests.

**Limits.** Synthetic results are an upper bound, not a finding about a
real journal. PDF samples are read as plain text, without italics and
without separating body from notes. English rules only. Curly quotation
marks only. Italics in restyled notes are not changed. Footnote to
author-date conversion is not attempted.
