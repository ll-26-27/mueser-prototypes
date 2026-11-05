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
inside Kurrent, and caught that the Schiller page is Antiqua. The hybrid
reading is the best of all on the clean Antiqua page (CER 0.010) and
slightly behind the whole-page reading on Fraktur (0.024 against 0.015);
on handwriting it loses clearly (0.14 against 0.06 on the 1864 hand),
because a line cut from its page loses the context that settles a
letterform. It is the way to put coordinates on a model reading, not the
way to get the best first reading of a hand.

**Limits.** The model's boxes are approximate; the hybrid mode pays one
call per line; six pages.
