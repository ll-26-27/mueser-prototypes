# Layout and hybrid: summary

**Purpose.** Give the transcription step the two things a whole-page
reading lacks: a map of what is on the page (and what is not main text),
and a reading that keeps every line's coordinates.

**Workflow.** Gemini 3.8 Flash maps each of the six real pages into
regions and lines with kinds, hands, scripts and later-hand flags; the
overlay draws them beside Kraken's segmentation. Then Kraken's line crops
are read one by one by Gemini 3.8 Flash and Claude Haiku 5.5, scored like
any other backend.

**Findings.** The layout pass counts lines correctly, names the stamp, the
pencil pagination, the interlinear correction and the Latin-cursive names
inside Kurrent, and caught that the Schiller page is Antiqua. See the
README for the hybrid numbers against the whole-page readings.

**Limits.** The model's boxes are approximate; the hybrid mode pays one
call per line; six pages.
