# Fraktur print bake-off: summary

**Purpose.** Measure how well each available OCR backend reads German
Fraktur print, on pages whose correct text is known, before any of Ben's
own pages have been corrected.

**Workflow.** Render five synthetic pages from an invented 1786 journal
(exact ground truth) and fetch three real pages with Wikisource
transcriptions; run five local backends on all eight; score each reading raw
and normalised; build an explorer that shows the diff.

**Findings.** Kraken's `german_print` model is the best on the real pages
(normalised CER 0.015–0.034) and Tesseract `frak2021` second (0.026–0.093);
on synthetic pages the ranking flips, which is why synthetic scores are an
upper bound and not a finding about sources. No vision-language model has
been scored yet: that is the next run, and it costs about a cent a page.

**Limits.** Three real pages. Wikisource ground truth normalises ſ and drops
prose line breaks. No handwriting here (see `02-kurrent-handwriting/`).
