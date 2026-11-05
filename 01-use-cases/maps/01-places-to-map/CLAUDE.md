# CLAUDE.md — Places to map

Read the repository `CLAUDE.md` first. In this folder:

- Never set `lat`/`lon` on a record by hand. Put the chosen URI in
  `review.csv` → `your_choice` and rerun the resolver, so the status is
  `reviewed` and the reason is recorded.
- When the resolver's rule is changed (threshold, margin, tie-break), say so
  in the README's results table and in `run.json`; old decisions are not
  edited.
- The cache under `cache/gazetteer_*` is evidence. Do not delete it.
