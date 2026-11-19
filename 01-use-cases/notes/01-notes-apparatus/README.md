# Notes apparatus

*Scoped, not yet built.* [`HANDOFF.md`](HANDOFF.md) is the brief.

One place for your notes: email, voice memos, text files, PDF highlights
and reference-manager items go into a local database, are gathered by
project, tagged with themes and connections once you have reviewed them,
and read in a single page that opens from disk. A note that belongs to
two projects appears under both.

Drop files into `inputs/inbox/` by kind (see
[`inputs/README.md`](inputs/README.md)). Nothing you drop in is ever
changed or moved, and nothing in `inputs/inbox/` or `outputs/store/` is
committed to git.

Commands, once built, from the repository root
(`--case 01-use-cases/notes/01-notes-apparatus`):

```sh
uv run python -m mueser.notes ingest --case …            # inbox → database, raw copies kept
uv run python -m mueser.notes enrich --case …            # proposals: summary, projects, themes, connections (needs OPENROUTER_API_KEY; --no-model for the rule-based parts only)
uv run python -m mueser.notes build  --case …            # outputs/index.html
uv run python -m mueser.notes serve  --case … --who ben  # the page on 127.0.0.1, writing your review to the log
uv run python -m mueser.notes apply  --case …            # log → accepted tags
uv run python -m mueser.notes export --case … --project <id>   # one Markdown digest, items whole
```

Everything a model proposes stays a proposal until you accept it in the
page; the controlled lists in `inputs/config/` grow only that way, or by
a rule you have written there. An item marked private is never sent to a
model.

What you supply: how your email can be exported (Mail.app, Gmail Takeout
`.mbox`, or forwarding to one address); a few voice notes; your project
list and first themes; then whether you use Zotero and which sources must
never leave the machine.
