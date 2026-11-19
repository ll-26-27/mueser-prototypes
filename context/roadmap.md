# Roadmap — what follows the prototypes

*Written 5 November 2026, after the first meeting with Ben; revised 19
November 2026. The two use-case groups in this repository are built and
documented. Four further projects were agreed, each with a brief written
for a coding agent, and all four now live in this repository as their own
use-case groups with one home page. This page says where the briefs are,
what they share, and what Ben has to supply.*

## The four projects

| # | project | lives in | brief | status |
|---|---|---|---|---|
| 1 | **Reading room.** Scan left, transcription and translation right, in register; selecting text lights the scan; copy with citation; settle open differences in both layers; mark issues and questions; everything logged to a file in the folder. | this repository, `01-use-cases/transcription/04-reading-room/`, new package `src/mueser/reading/` | [`04-reading-room/HANDOFF.md`](../01-use-cases/transcription/04-reading-room/HANDOFF.md) | built 10 November 2026 on the three fixture pages; see its README |
| 2 | **Style.** Class handouts normed to a house style and updated for a new term; the CV extended without changing its page geometry; a book-length manuscript's footnotes and bibliography checked. Three atomic cases. | `01-use-cases/style/{01-handouts,02-cv,03-footnotes,04-journal-style}/`, package `src/mueser/style/` | [`style/HANDOFF.md`](../01-use-cases/style/HANDOFF.md) (shared), then [`01-handouts/HANDOFF.md`](../01-use-cases/style/01-handouts/HANDOFF.md), [`02-cv/HANDOFF.md`](../01-use-cases/style/02-cv/HANDOFF.md), [`03-footnotes/HANDOFF.md`](../01-use-cases/style/03-footnotes/HANDOFF.md) | `02-cv` and `04-journal-style` (added at Ben's request of 19 November) built 19 November 2026 on synthetic files, see their READMEs; `01-handouts` and `03-footnotes` scoped |
| 3 | **Notes apparatus.** Email, voice notes, text notes, PDF annotations and Zotero items into one local database, aggregated by project, tagged with themes and connections after review, with a reviewer page. | `01-use-cases/notes/01-notes-apparatus/`, package `src/mueser/notes/` | [`01-notes-apparatus/HANDOFF.md`](../01-use-cases/notes/01-notes-apparatus/HANDOFF.md) | scoped; moved here 19 November 2026 |
| 4 | **Timeline: thinkers, works and events.** Wikidata-sourced nodes for people, works, events, periods and concepts; typed connections between them; link-outs to the Stanford Encyclopedia of Philosophy, the Internet Encyclopedia of Philosophy, Britannica, the ODNB and others; the same log-and-serve pattern. | `01-use-cases/timeline/01-thinkers-and-events/`, package `src/mueser/timeline/` | its `README.md` | built 19 November 2026, first version; see its README |

On 5 November projects 2 and 3 were scoped as separate private
repositories (`~/Development/26/mueser-style/`, `~/Development/26/mueser-notes/`),
because they share no code with the transcription work and would hold
Ben's CV, manuscripts and mail. On 19 November 2026 both were moved into
this repository as atomic use-case groups so that all four projects sit
behind one home page; the two sibling repositories are superseded and say
so in their READMEs. This repository is public, so Ben's material in those
groups (`inputs/` apart from README, `config/` and synthetic fixtures;
every store, export and run folder; every `.sqlite`) is excluded by the
root `.gitignore`. What is committed is code, config, labelled synthetic
fixtures and the pages.

## What every project shares

These are the rules of this repository's `CLAUDE.md`, carried over, plus
two patterns that project 1 sets and project 3 reuses.

- **Run folders.** Every output goes in a folder with a `run.json` saying
  what ran, on what, with which parameters and model. Nothing is
  overwritten; a redo is a new run, or the same id with a note saying why.
- **Provenance on every derived thing.** A line knows its reader, model
  and prompt hash; a translation segment its lines and model; a tag its
  prompt and the event that accepted it; a reformatted paragraph the style
  rule that mapped it.
- **Raw replies kept.** Every model call is cached on disk with the raw
  response. Caches are evidence, not clutter.
- **Decisions are recorded, not inferred.** Model output is a proposal
  until a person accepts it, or until a rule written in config accepts it
  and is named in the record. Append-only `log.jsonl` files hold the
  decisions; commands derive state from the log and never edit the log.
- **Static HTML plus a local `serve`.** Each project's viewer is one
  self-contained HTML file that opens from disk. Writing back to the folder
  goes through a one-command local server on `127.0.0.1`; without it the
  page keeps state in the browser and exports a log file to drop into an
  `inbox/`. No app, no account, no network beyond model calls.
- **Inputs stay out of public git.** In the style and notes groups
  `inputs/` (apart from README, `config/` and `fixtures/`), the inbox,
  stores, exports, run folders and databases are ignored by the root
  `.gitignore`; what is committed is code, config, synthetic fixtures and
  reports Ben agrees to keep.
- **Synthetic is labelled synthetic.** Fixtures made for tests say so in
  their names and metadata.
- **Nothing is cut.** Source material goes to a model whole. If a document
  exceeds a model's limit the error is surfaced and the run is split into
  whole-document passes.
- **Voice.** READMEs for Ben say what ran, on what, by which model, what it
  produced and what was checked. No reassurance about AI use.

## What Ben has to supply

| project | needed to start | needed to finish |
|---|---|---|
| 1 | nothing: it builds on the fixture pages in cases 01–03 | his own scans (PDF, JPEG or a IIIF manifest), the bibliographic record for each, his browser, whether he uses Zotero and which citation style |
| 2 | three to five handouts, the current CV, one manuscript or chapter, all as `.docx` (LaTeX sources too if any) | the citation style of the book, whether he wants the house style as a Word template he applies himself |
| 3 | how his email can be exported (Mail.app, Gmail Takeout `.mbox`, or forwarding to one address); a few voice notes; his project list and first themes | whether he uses Zotero; which sources must never go to a model |
| 4 | nothing: it builds from Wikidata and the reference works it links to | the thinkers, events and periods his courses need that the seed misses; which connection types matter to him; corrections to the record, made in the page |

## Order

Project 1 first: it is the direct continuation of what Ben saw, and it sets
the log-and-serve pattern projects 3 and 4 copy. Project 4 is being built
now, since it needs none of Ben's material to start. Projects 2 and 3 can
run in parallel in their own groups once his documents and notes arrive;
within 2, the CV case comes first.
