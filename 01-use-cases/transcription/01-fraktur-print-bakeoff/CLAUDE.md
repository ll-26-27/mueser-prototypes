# CLAUDE.md — Fraktur print bake-off

Read the repository `CLAUDE.md` first. In this folder:

- `inputs/` is read-only except through the two numbered operations. Never
  edit a ground-truth file by hand; fix the fetch script and rerun it so the
  provenance stays true.
- Every run goes to a new `outputs/runs/<run_id>/`; never overwrite one.
- When reporting results, give both CER columns and say which pages are
  synthetic. Do not average synthetic and real pages into one headline number
  without saying so.
- Adding a backend means adding it to `--backends`, not editing results.
