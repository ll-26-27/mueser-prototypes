# Reading room: summary

**Purpose.** Give a person one page per scan on which to read, decide and
cite: the image with a box on every line, the readers' settled text with
their disagreements marked, an English translation in register, and a log
in the folder of everything decided, asked or copied.

**Workflow.** `settle` takes a page's consensus and the medoid reader's raw
lines, remaps the consensus spans from normalised, flattened offsets onto
those lines, and aligns the lines to a reading that has boxes (the hybrid
reading), writing an immutable build. `translate` sends the numbered lines
to two models, verifies that each sentence's first and last words occur in
the lines it names, groups the two models' sentences into blocks and marks
the blocks where they diverge. `build` renders one self-contained page;
`serve` puts it on 127.0.0.1 and appends the page's events to
`outputs/reading/log.jsonl`; `apply` turns the latest decisions into a new
build; `ingest` brings in logs exported from a browser that could not save.

**Findings.** On three real pages every line of the Grimm and Schiller
pages and 20 of the 22 lines of the Kaskel letter were anchored to a box
(mean confidence 0.97, 0.91 and 1.0); the unanchored two are a page number
the hybrid misread and a closing line the segmenter cut differently. All
102 remapped span pieces normalise to the span they came from. Two models
translated the three pages for $0.10 in 136 seconds; every segment verified
against its lines; of 21 blocks one diverged (*May God preserve you!* /
*God keep you!*), the rest differ in wording only. The browser loop was
exercised end to end: hover, decide, select across lines, log an issue,
resolve it, decide a translation block and a whole line, copy a CSL-JSON
excerpt; `apply` changed exactly the decided lines.

**Limits.** The medoid is a model's reading and on the Grimm page it has
already folded ſ to s, so "diplomatic" here means "as that reader wrote
it"; the readers' alternatives are shown normalised, so taking one inserts
s for ſ. The translations have not been checked by a reader of German.
Anchoring is by text similarity, so a line the segmenter merged or missed
gets a shared box or none. Everything a person does is attributed to the
name typed in the page, which is free text. A page opened as a file keeps
its events in that browser until exported.
