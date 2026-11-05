# Kurrent handwriting: summary

**Purpose.** Measure every available reader on German handwriting, on pages
with known text, before Ben's own pages are corrected.

**Workflow.** Three synthetic Kurrent pages (exact ground truth) and three
real pages with Commons transcriptions; Kraken, Tesseract as a control, and
five vision-language models; explorer and consensus.

**Findings.** Gemini 3.8 Flash and 3.1 Pro read a clean 1864 hand at CER
0.06 where Kraken has 0.21; on a fast 1896 hand Gemini 3.1 Pro is at 0.18
and the rest at 0.43 or worse; a photographed 1901 album defeats everyone.
One empty reply from Gemini 3.8 Flash is recorded as an error. The whole
run cost $0.24.

**Limits.** Three real pages, community transcriptions, no Transkribus or
eScriptorium reading yet, no model trained on Ben's hand.
