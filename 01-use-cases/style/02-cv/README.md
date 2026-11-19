# The CV, extended without reflow

*Scoped, not yet built.* [`HANDOFF.md`](HANDOFF.md) is the brief.

What it will do: read your CV into a small data file, one entry per line
under its section; let you add entries there; and write a new copy of the
CV in which each new entry is a clone of a neighbouring entry's paragraph,
so the indents, tab stops, fonts and spacing are exactly yours. A check
step converts before and after to PDF and tells you the page count and
the first page that differs. If the CV grew by a page it says so and
stops; it never shrinks fonts or margins to fit.

Commands, once built, from the repository root:

```sh
uv run python -m mueser.style cv extract 01-use-cases/style/02-cv/inputs/cv/cv.docx --out 01-use-cases/style/02-cv/inputs/config/cv.yml
uv run python -m mueser.style cv render  --cv 01-use-cases/style/02-cv/inputs/config/cv.yml --source 01-use-cases/style/02-cv/inputs/cv/cv.docx --out 01-use-cases/style/02-cv/outputs/out/
uv run python -m mueser.style cv check   --before 01-use-cases/style/02-cv/inputs/cv/cv.docx --after 01-use-cases/style/02-cv/outputs/out/<run>/cv.docx
```

What you supply: the current CV as `.docx` in `inputs/cv/` (not
committed; see [`inputs/README.md`](inputs/README.md)). LibreOffice must be
installed for the page count.
