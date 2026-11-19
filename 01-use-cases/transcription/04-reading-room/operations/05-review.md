# Step 05: a person reads, decides, and the decisions become text

1. `sh operations/04-serve.sh <your name>` from the repository root. The
   page opens at `http://127.0.0.1:8765/01-use-cases/transcription/04-reading-room/outputs/index.html`;
   the badge in the top bar says it is saving to the log. *Previous*,
   *Next* and the ← → keys move between the room's pages.
2. Read a page. Hover or select text to see it on the scan. Click a marked
   passage to decide it; use ✎ at a line's end to replace a whole line;
   decide a divergent translation block with its *Decide* button.
   Select text and use *Issue*, *Question* or *Comment* to leave a note,
   or *Cite* / *Markdown* / *CSL-JSON* to copy it with its citation.
3. Each action is one line in `outputs/reading/log.jsonl`. The log panel
   on the right lists them and marks issues resolved.
4. If the page was opened as a file instead, press *Export log*, drop the
   file into `outputs/reading/inbox/`, and run
   `uv run python -m mueser.reading ingest --case 01-use-cases/transcription/04-reading-room`.
5. To settle the decisions into the text:
   `uv run python -m mueser.reading apply --case 01-use-cases/transcription/04-reading-room`
   writes a new build under `outputs/reading/builds/` (the old one stays);
   then `sh operations/03-build.sh` renders the page from it. If a line's
   text changed, its translation is marked stale; rerun
   `sh operations/02-translate.sh` with a new `--run-id` for a fresh one.
