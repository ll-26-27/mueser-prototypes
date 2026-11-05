# Fraktur print bake-off: summary

**Purpose.** Measure how well each available reader handles German Fraktur
print, on pages whose correct text is known, before any of Ben's own pages
have been corrected.

**Workflow.** Five synthetic pages from an invented 1786 journal (exact
ground truth) and three real pages with Wikisource transcriptions; four
Tesseract models, Kraken and four vision-language models; scores raw and
normalised; an explorer with the diff; a consensus with a check-in list.

**Findings.** Gemini 3.8 Flash and 3.1 Pro read the real Fraktur pages at
normalised CER 0.010–0.018, Kraken at 0.029–0.034, the best Tesseract at
0.074–0.093; on the Antiqua page Kraken is best. Haiku modernises ſ on
every line and the raw column shows it. The whole vision run cost $0.23.

**Limits.** Three real pages; Wikisource ground truth normalises ſ and
drops prose line breaks; no handwriting here.
