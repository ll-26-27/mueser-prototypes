# Reading room

One page per scan. The image is on the left with a box around every line;
on the right is the transcription the readers settled on, with the passages
they disagreed about marked, and beside it an English translation, sentence
by sentence, kept in register with the German. Select any passage in either
text and its lines light up on the scan. Copy it and the citation comes with
it. Click a marked passage and choose between the readers, or write your
own. Leave a question or an issue on anything. Everything you do is appended
to one file, `outputs/reading/log.jsonl`, and nothing you do changes the
readers' text until you ask for it to be applied.

Open it with one command from the repository root:

```sh
uv run python -m mueser.reading serve --case 01-use-cases/transcription/04-reading-room --who ben
```

It prints `http://127.0.0.1:8765/01-use-cases/transcription/04-reading-room/outputs/index.html`
and opens it (the server serves the whole repository, so the top bar's links
to the home page and the consensus pages work; `.env` and other dotfiles are
refused). While it runs, every decision and note is written to the log as
you make it. The pages in the room are numbered under *Source page*; move
with *Previous* and *Next*, the ← → keys, or the page buttons. *Add a
source* shows the commands that bring another document in. You can
also double-click `outputs/index.html`; then the page keeps your work in
the browser and the **Export log** button writes it to a file to drop into
`outputs/reading/inbox/` (see [Keeping what you did](#keeping-what-you-did)).

## What ran, on what

Three real pages, taken with their readings from
[`03-layout-and-hybrid`](../03-layout-and-hybrid/) (origins and sha256 of
every copy in `inputs/readings/provenance.json`; rights in
[`inputs/README.md`](inputs/README.md)):

| page | readers in the consensus | agreement | the text you read is | passages marked (to check) |
|---|---|---|---|---|
| Grimm, *Kinder- und Haus-Märchen* I (1812), p. 93, Fraktur | 4 | 0.972 | Gemini 3.8 Flash, whole page | 32 (32) |
| Kaskel to Schnorr von Carolsfeld (1864), leaf 84, secretary's hand | 5 | 0.871 | Gemini 3.8 Flash, whole page | 51 (36) |
| *Musen-Almanach für das Jahr 1796*, p. 93, Antiqua | 4 | 0.993 | Gemini 3.8 Flash reading Kraken's line crops (hybrid) | 8 (8) |

"The text you read" is the **medoid**: the reading closest to all the
others, as [`03`'s consensus](../03-layout-and-hybrid/outputs/consensus-print/index.html)
computed it. A marked passage is one where at least one other reader has
something else; a passage "to check" is one where the dissenting readers
carry at least a quarter of the page's reliability. Hover a mark for every
reader's alternative.

**Settle** (`settle`, deterministic code). The consensus works on
normalised, flattened text (ſ folded to s, hyphenated line ends joined, no
line breaks), so its spans are offsets into that. This step finds where each
of the medoid's raw lines sits in that text and cuts every span into
per-line pieces in raw offsets. All 102 pieces across the three pages land
on text that normalises to the span they came from. A span that crosses a
line end (`präch-` / `tig`) becomes two pieces that share an id.

**Anchor** (inside `settle`, deterministic code). Two of the three medoids
are whole-page readings with no coordinates. Each settled line is aligned to
the lines of the hybrid reading of the same page, which has a box for every
line Kraken segmented, by sequence alignment over the line strings with the
declared normalised distance as the cost:

| page | lines | matched 1:1 | merged (two lines, one box) | split (one line, two boxes) | unanchored | polygons with no text | mean confidence |
|---|---|---|---|---|---|---|---|
| Grimm 1812 | 29 | 28 | 0 | 1 | 0 | 1 | 0.973 |
| Kaskel 1864 | 22 | 17 | 4 | 1 | 2 | 3 | 0.907 |
| Schiller 1796 | 18 | 18 | 0 | 0 | 0 | 0 | 1.0 (the medoid is the boxed reading itself) |

An unanchored line has a dotted left edge in the page and lights nothing on
the scan. On the Kaskel letter they are the page number `84` (the hybrid
read that crop as `[?O]`) and `Ihr treu ergebener`, whose polygon the
segmenter split differently from the closing lines around it; the merges
are the signature block, where Kraken drew one polygon across two of the
medoid's lines. A pairing is refused above a normalised distance of 0.55
(recorded in `run.json`).

**Translate** (`translate`, model judgment). Each page's settled lines go,
numbered, to two models with the same prompt
([`translate_de_en.md`](../../../src/mueser/text/backends/prompts/translate_de_en.md)):
translate sentence by sentence, name the first and last line of each
sentence, copy its first and last three words, keep `[...]` and `[?word]`,
change nothing in the German. Run `20261110-01`, Gemini 3.8 Flash and
Claude Sonnet 5.5, $0.098, 136 s:

| page | segments (Gemini / Claude) | verified against the lines they name | blocks | divergent |
|---|---|---|---|---|
| Grimm 1812 | 11 / 11 | all; Claude left the page-number line `— 93 —` uncovered | 10 | 0 |
| Kaskel 1864 | 7 / 6 | all | 6 | 1 |
| Schiller 1796 | 5 / 5 | all | 5 | 0 |

A segment is verified when its first three words occur in the line it says
it starts on (or in that line joined with the next, since three words can
straddle a line end) and its last three in the line it ends on. The two
models' segments are then grouped into **blocks** whose line ranges
coincide, and a block is **divergent** when the two translations are at
least 0.35 apart by normalised edit distance. The one divergent block is
`Gott erhalte Sie!` on the letter: *May God preserve you!* against *God keep
you!* (distance 0.41). Everywhere else the two translations differ in
wording only, and the page shows Gemini's with Claude's one click away.
Neither translation has been checked by a reader of German here.

**Build** (`build`, deterministic code) assembles the settled layer, the
translation and the log into one self-contained `outputs/index.html`.

## What you can do in the page

- **See where a passage is.** Hover or select text in either column and
  its lines light on the scan; hover a box on the scan and the line lights.
- **Decide a marked passage.** Click it: keep the medoid, take a reader's
  alternative, or type your own. The page shows your choice at once and
  counts it as pending until applied.
- **Replace a whole line** with ✎ at the line's end, for pages where the
  readers disagreed too much for passage-by-passage work.
- **Decide a translation block** where the two models diverge: one, the
  other, or your own. Elsewhere, "Other reading" shows the second model.
- **Copy with a citation.** Select, then *Cite* (the passage with a
  one-sentence citation and its provenance), *Markdown* (a blockquote with
  a footnote) or *CSL-JSON* (paste into Zotero with *File → Import from
  Clipboard*; the provenance travels in the item's note). Every copy is
  logged as an excerpt, so a quotation can be traced.
- **Leave an issue, a question or a comment** on a selection. The log panel
  lists them, filters by page, type and status, jumps back to the passage,
  and marks them resolved. Resolution is itself an event; nothing is deleted.

Your name in *Reading as* goes on every event. It is free text.

## Keeping what you did

Served through `serve`, each event is appended to
`outputs/reading/log.jsonl` as it happens. Opened as a file, the page keeps
events in the browser; *Export log* downloads them, and

```sh
uv run python -m mueser.reading ingest --case 01-use-cases/transcription/04-reading-room
```

appends the ones not yet in the log from `outputs/reading/inbox/`.

Decisions become text only when you say so:

```sh
uv run python -m mueser.reading apply --case 01-use-cases/transcription/04-reading-room
uv run python -m mueser.reading build --case 01-use-cases/transcription/04-reading-room
```

`apply` reads the log, takes the latest decision per passage, and writes a
**new** build under `outputs/reading/builds/` with the settled transcription
and translation as text files; the earlier build stays as it was, and every
event records which build it was made against. `build` renders the page
from the newest build. The *diplomatic* text of every line, as the medoid
reader wrote it, is kept in `settled.json` beside the settled text and is
never edited. Two things to know: the readers' alternatives are shown as the
consensus normalised them (s for ſ), so choosing one inserts that form;
typing your own reading keeps whatever you type. And when a line's text
changes, the page marks its translation stale rather than reusing it; rerun
`translate` for a fresh one.

## What was checked

- The remapped span pieces: all 102 normalise to the span text they came
  from (none off); the counts of merges, splits and unanchored lines are
  the ones in the table above.
- The page, in a headless Chrome driven over the DevTools protocol: hover
  lights the right box; clicking a mark opens the choices and saving writes
  one event; a selection across two lines lights both boxes and opens the
  toolbar; an issue is logged, listed and resolved; a divergent translation
  block, a passage and a whole line were decided; a CSL-JSON excerpt was
  logged with the right locator; the server received every event. `apply`
  then produced a build that differed from its parent in exactly the two
  decided lines of the letter and took the chosen translation for `l19`.
  Those test events and that build were removed afterwards, so the log is
  empty for you; they were made under the name "ben" by the agent that
  built this, not by Ben.
- `tests/test_reading.py`: 13 tests on invented lines (span remapping over a
  hyphenated line end, alignment with a merge, a split, a missing line and
  an ornament polygon, segment verification and correction, block
  alignment and the divergence threshold, the log and its ingest, applying
  and reverting a decision, citations for a book and a manuscript, the
  server accepting a valid event and refusing an invalid one).

## Your own pages

Once a folder of pages has been through the bake-off with a hybrid reader
and the consensus step (see [`02-your-project/README.md`](../../../02-your-project/README.md)):

```sh
uv run python -m mueser.reading collect --case <new case> --consensus <outputs/consensus/consensus.json> \
  --runs <outputs/runs/<run_id>> --pages <inputs/pages> --segmentation "hybrid:*"
uv run python -m mueser.reading init-doc --pages <inputs/my-source> --out <new case>/inputs/metadata.json
uv run python -m mueser.reading settle --case <new case>
uv run python -m mueser.reading translate --case <new case>     # needs OPENROUTER_API_KEY; skips without it
uv run python -m mueser.reading build --case <new case>
uv run python -m mueser.reading serve --case <new case> --who <your name>
```

`init-doc` writes the page ids and image hashes; the title, author, date,
place, publisher, archive and shelfmark are yours to fill, and the citations
are only as good as that record. Without a hybrid or Kraken reading the page
still works, with no boxes on the scan.

## Files

See [`index.md`](index.md). The commands are in `src/mueser/reading/`;
`operations/` holds the exact invocations that produced what is here.
