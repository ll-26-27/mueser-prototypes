# Handouts to a house style

*Scoped, not yet built.* [`HANDOFF.md`](HANDOFF.md) is the brief.

What it will do: read your existing class handouts and write down the
style they mostly share (fonts, sizes, spacing, margins, how a reading
entry looks) as `inputs/config/house-style.yml` and a report you can read
before anything changes; apply that style to a handout, leaving its words
untouched and listing any paragraph it could not place; and update a
handout for a new term from one small file of course facts (code, title,
term, meeting times, readings), with the readings set in your citation
style.

Commands, once built, from the repository root:

```sh
uv run python -m mueser.style handout infer  01-use-cases/style/01-handouts/inputs/handouts/*.docx --out 01-use-cases/style/01-handouts/inputs/config/
uv run python -m mueser.style handout norm   <handout.docx> --style 01-use-cases/style/01-handouts/inputs/config/ --out 01-use-cases/style/01-handouts/outputs/out/
uv run python -m mueser.style handout update <handout.docx> --course 01-use-cases/style/01-handouts/inputs/config/course.yml --out 01-use-cases/style/01-handouts/outputs/out/
```

Every run writes to a new folder under `outputs/out/` with a `diff.html`
showing exactly what changed, and the text of the document is checked to
be identical before and after a restyle.

What you supply: three to five handouts as `.docx` in `inputs/handouts/`
(not committed; see [`inputs/README.md`](inputs/README.md)). Then: whether
you want the house style as a Word template you apply yourself, which
citation style, and whether any handouts are in LaTeX.
