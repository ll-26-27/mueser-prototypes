# Kurrent handwriting: summary

**Purpose.** Establish the open-source baseline for German handwriting
before the paid and hosted backends are added, on pages with known text.

**Workflow.** Render three synthetic Kurrent pages (exact ground truth) and
fetch three real pages with Commons transcriptions; run Kraken's open German
handwriting model and Tesseract as a control; build the explorer.

**Findings.** Kraken reads a clean 1864 secretary hand at one wrong
character in five and a 1901 album photograph at four in five. The
Kurrent-specific Kraken model from 2026 does not load in the current Kraken.
No vision-language or Transkribus reading exists yet; those are the
comparisons that will decide the tool.

**Limits.** Three real pages, community transcriptions, no Transkribus.
