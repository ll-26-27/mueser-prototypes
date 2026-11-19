# Notes apparatus: summary

**Purpose.** Put Ben's notes from every source into one local database,
gather them by project, tag them with themes and connections after
review, post a note under every project it belongs to, and show it all
in one page that opens from disk.

**Workflow.** `ingest` copies each inbox file once by its hash and makes
items of messages, transcripts, files, PDF annotations and Zotero
records, text whole. `enrich` finds connection candidates and project
matches by rule, then asks a model for a summary, projects and themes
from the controlled lists, and a ranking of the candidates; everything
lands as a proposal. `build` writes the page; `serve` appends review
actions to the log; `apply` turns accepted proposals into tags; `export`
writes a Markdown digest per project with every item in full.

**Findings.** None yet: scoped 5 November 2026, moved into this
repository 19 November 2026, not built.

**Limits.** Voice transcription is local Whisper by default, so quality
depends on the machine; a hosted model is a flag. The controlled lists
start empty and are agreed with Ben from the first ingest. A model's
connections are only a ranking of candidates found by rule, so a link no
rule proposes cannot appear.
