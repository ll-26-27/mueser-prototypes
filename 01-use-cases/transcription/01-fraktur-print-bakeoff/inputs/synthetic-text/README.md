# Synthetic source text

`reisetagebuch-1786.txt` is a **made-up** travel journal, written for this
repository on 4 November 2026 by Claude (Fable 5.1) in the spelling habits of
late-eighteenth-century German print (long s, "seyn", "gieng", "Thür",
"Dreßden"). It is not a historical document and cites no real one; the people
and dates are invented, the places are real. Its only purpose is to give the
transcription bake-off pages whose correct text is known character for
character, so error rates can be computed before any real page has been
hand-corrected.

Each `#` line is a page heading; each page of the synthetic set is rendered
from one section. The place names match the ledger in
`01-use-cases/maps/01-places-to-map/inputs/places.csv`, so the bridge use case
can carry the same places from page to map.

Known limits of synthetic pages: a font is cleaner than any 1786 impression,
there is no show-through, no broken type, no ink spread. Scores on these pages
are an upper bound. The real-sample pages in `inputs/pages/real-*` are the
other half of the test set.
