# CLAUDE.md — From page to map

Read the repository `CLAUDE.md` first. In this folder:

- `inputs/` are OCR readings copied from a recorded bake-off run. Do not
  correct them; the errors are the point.
- If you add or change a mention in `operations/02-mentions.json`, keep the
  `method` field true: say what changed, by whom, and rerun step 3 so every
  record is re-verified.
- A mention is only a record if its `surface_form` is on the stated line.
  Never widen that check to make a count look better.
