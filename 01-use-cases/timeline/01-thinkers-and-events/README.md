# Thinkers and events

One node at a time: a thinker, a work, an event, a period or a concept.
Above it, the grey band of the periods and events of its years over a year
axis, with the chosen thinker's life beneath, born and died marked and
their works as ticks. Below, three columns: what came before it on the
left (*Influenced by*, or an event's *Context*), the node itself in the
middle with its overview, notable works, school of thought, references and
a connection map, and on the right the *Events* that bear on it and what
it *Influenced* (for an event: the *People* connected to it and its
*Outcome*). Every node carries the citation of the reference work that
covers it and links out to the rest; every connection says where it comes
from; every decision you make is appended to one file,
`outputs/timeline/log.jsonl`.

Open it with one command from the repository root:

```sh
uv run python -m mueser.timeline serve --case 01-use-cases/timeline/01-thinkers-and-events --who ben
```

It prints `http://127.0.0.1:8767/01-use-cases/timeline/01-thinkers-and-events/outputs/index.html`
and opens it. The page also opens by double-clicking `outputs/index.html`;
then it keeps your work in the browser and **Export log** writes a file to
drop into `outputs/timeline/inbox/` (see [Keeping what you did](#keeping-what-you-did)).
Images come from Wikimedia Commons and need a connection; everything else
is in the file.

The layout is the mock-up Ben had made for the project some years ago,
kept on purpose for this first version; what differs is where the data
comes from and that every connection has a standing. The group README,
[`../README.md`](../README.md), sets the two side by side.

## What ran, on what

**Collect** (`collect`, deterministic lookup; run `collect-20261119-01`,
46 minutes, 1,000 cached Wikidata queries). The node set is the rule in
[`inputs/rules.json`](inputs/rules.json), and each node records which
clause admitted it:

| type | nodes | admitted by |
|---|---|---|
| people | 1,463 | 615 with a Stanford Encyclopedia of Philosophy (SEP) or Internet Encyclopedia of Philosophy (IEP) entry; 848 one hop away by *influenced by* (596, both directions), *student of* / *student* (177), *doctoral advisor* / *doctoral student* (75), each with at least 20 Wikipedia articles |
| works | 4,651 | 3,428 notable works (P800) of those people; 1,223 further works whose author is one of them, with at least 8 Wikipedia articles |
| events | 1,325 | by class above a coverage threshold: 455 wars, 241 treaties, 98 historical events, 76 rebellions, 74 battles, 52 revolutions, 22 massacres, 10 constitutions, 8 coups, 7 pandemics, 5 famines; plus 277 events a person in the set took part in or is recorded as having as a significant event, whatever their coverage; 108 dropped for having no usable date or falling outside 800 BCE–2030 |
| periods | 172 | historical periods with at least 30 Wikipedia articles and a start date; 89 dropped for no date or outside the range |
| concepts and movements | 1,170 | 909 non-human items with an SEP or IEP entry (the Encyclopedia's topic entries: *social contract*, *sovereignty*, …); 261 movements a person in the set belongs to |

The recorded connections are Wikidata statements between two nodes of the
set, each named by its property: 16,677 in all. *Influenced by* 2,529;
*author* 4,732 and *notable work* 3,450; *student of* / *teacher of* 821;
*doctoral advisor* / *student* 401; *movement* 763; *field of work* 564;
*about* (main subject) 622; *part of* 756; *follows* / *followed by* 1,223;
*caused by* / *led to* 126; *significant event* 187; *took part in* /
*participant* 503. The sitelink thresholds are a measure of Wikipedia
coverage, used as a cut-off and recorded on every node, not a judgment of
importance; `inputs/README.md` says how to move them.

**Sources** (`sources`, deterministic lookup). For the 1,261 nodes with
an SEP entry, the entry page's own metadata (title, authors, first
published, substantive revision), from which the citation the Encyclopedia
asks for is built. For every node with a Wikipedia article, the lead
section through the summary endpoint, with revision id and timestamp; it is
shown as the overview under the article's name and licence (CC BY-SA 4.0).
Counts: see *What was checked*.

**Connect** (`connect`, model judgment). Wikidata rarely records which wars
or revolutions a thinker answered, took part in or suffered under. For
each person with an SEP or IEP entry and a Wikipedia extract, Gemini 3.8
Flash was given that extract and the list of events and periods in the set
whose dates overlap the person's life, and asked which bear on the person,
with a type from a closed list (*lived through*, *took part in*, *wrote in
response to*, *suffered under*, *shaped by*), a one-sentence reason, and the
sentence of the extract that supports it, copied exactly
([the prompt](../../../src/mueser/text/backends/prompts/timeline_connect.md)).
The sentence is checked verbatim here; a proposal whose sentence is not in
the extract is kept and marked. Every proposal is `proposed` until you
accept or reject it in the page. Counts and cost: see *What was checked*.

**Database and page** (`db`, `build`, deterministic code). Everything goes
into `outputs/timeline/timeline.sqlite` (tables `nodes`, `node_ids`,
`links`, `texts`, `sep_entries`, `citations`, `edges`, `sources`, `meta`)
and one JSON file, and the page is rendered from that with the log
embedded. `python -m mueser.timeline query --case … "SELECT …"` runs SQL
against the database.

## What you can do in the page

- **Choose a node** by typing in the search box at the top; `←`/`→` on the
  band is drag, scroll is zoom, *Fit* returns to the node's span. Click any
  bar, tick, card or map node to move to it. The address bar carries the
  node, so a page can be bookmarked or sent.
- **Read the references.** *Where to read about it* lists the reference
  works that cover the node, by kind (encyclopedias, texts, authority
  records), each a link; *Cite* copies the citation as text, Markdown or
  CSL-JSON (paste into Zotero with *File → Import from Clipboard*). Every
  copy is logged as an excerpt.
- **Decide a proposed connection.** A card marked *proposed* shows the
  model's reason and the sentence it rests on; *Accept* or *Reject* writes
  one decision to the log and the page shows it at once.
- **Add a connection** of your own, to any node, with a type, a reason and
  a reference; it is marked *added here* and kept beside the record.
- **Choose layers.** *Layers* shows connections by what they join
  (thinkers to thinkers, thinkers to events, works to works, …) and by whose
  they are: the record, the model's reading, the readers of this page.
- **Leave an issue, a question or a comment** on any node or connection;
  the log panel lists them, jumps back, and marks them resolved. Resolution
  is itself an event; nothing is deleted.

Your name in *Reading as* goes on every event.

## Keeping what you did

Served through `serve`, each event is appended to
`outputs/timeline/log.jsonl` as it happens. Opened as a file, the page
keeps events in the browser; *Export log* downloads them, and

```sh
uv run python -m mueser.timeline ingest --case 01-use-cases/timeline/01-thinkers-and-events
uv run python -m mueser.timeline db --case 01-use-cases/timeline/01-thinkers-and-events
uv run python -m mueser.timeline build --case 01-use-cases/timeline/01-thinkers-and-events
```

appends the ones not yet in the log, then rebuilds the database and the page
with every decision applied: an accepted proposal becomes an `accepted`
edge, a rejected one is hidden unless *Show rejected* is on, and a
connection you added is an edge with your name as its source. The run
folders the page was built from are never changed; `data_id` in the page's
footer names them.

## What was checked

- **Sources.** 1,242 of the 1,261 Stanford entries parsed (title, authors,
  dates); the 19 that did not are identifiers Wikidata holds that no longer
  resolve to an entry page (404) or pages without the citation metadata,
  listed in `sources/sep.json` with their status. Wikipedia extracts for
  7,294 of the 7,303 nodes that have an article, 136 of them from the
  German Wikipedia where there is no English one. The first attempt, one
  request per node, was rate-limited after 821; the batch endpoint (twenty
  titles a request) replaced it and the failed replies were dropped from
  the cache, which is why `cache/wikipedia/` holds requests of both shapes.
- **Connect.** 610 people asked (those with an SEP or IEP entry, an extract
  and a birth year); 170 proposals for 137 of them, every one quoting a
  sentence found verbatim in the extract and naming an event from the list
  it was given: 90 *lived through*, 43 *took part in*, 17 *wrote in response
  to*, 16 *suffered under*, 4 *shaped by*. Run `connect-20261119-01`,
  Gemini 3.8 Flash, $4.57, 245 s with 24 parallel calls. The run was done
  twice: the first pass cut five long replies at the token limit; the limit
  was raised and the run redone under the same id, which is why the cost
  log shows two passes ($4.99 and $4.57). Proposals are few on purpose:
  the prompt forbids a connection the extract does not support.
- **The page, in a headless Chrome driven over the DevTools protocol**
  against the served page: Thomas Hobbes opens with his life on the band
  (born 1588, died 1679, four works as ticks), twelve periods and events of
  his years as bars, *Influenced by* 4, *Events* 1, *Influenced* 6; the
  references list the Stanford entry, Britannica, the ODNB, Oxford
  Reference, Deutsche Biographie, Treccani, Gutenberg, Open Library, VIAF,
  the Library of Congress, GND, both Wikipedias, Wikidata and Commons; the
  Stanford citation reads *Duncan, Stewart, "Thomas Hobbes", The Stanford
  Encyclopedia of Philosophy (Sat Mar 1, 2025)…*; the layers menu lists ten
  classes of connection with their counts; accepting the one proposal (the
  English Civil War, *wrote in response to*) wrote one event to the log
  through the server; searching *English Civil War* opened the event with
  its bar highlighted, *Context* 1 (Wars of the Three Kingdoms), *People* 3,
  *Outcome* 0. That test decision was removed afterwards, so the log is
  empty for Ben.
- `tests/test_timeline.py` (dates and precision labels, link-outs and the
  Stanford citation, candidate events and the verbatim check, the log with
  decisions, added edges and ingest, the database and page on a synthetic
  run), `tests/test_local_servers.py` (both servers refuse hidden and
  encoded paths and symlink escapes, accept a valid event and refuse an
  invalid one) and `tests/timeline_queue.test.cjs` (the page's save queue
  across reloads and failed saves): 43 Python tests and 6 Node tests pass.
- **Size.** The page is 35 MB because it carries every extract, link and
  citation for 8,781 nodes; it opens in a second or two on a laptop. The
  SQLite file and the JSON beside it hold the same data.

## Widening the set, and other perspectives

The node set is a rule. To take in more thinkers, lower
`people.expand.min_sitelinks` or add a seed clause; to take in more events,
add a class or lower its threshold; then run `collect` with a new run id,
`sources`, `db` and `build`. Nothing is added by hand; a node Ben wants
that no rule admits is the occasion to write the rule.

The layers menu has a second axis, *whose connections*: the record, the
model, the readers. That is where a further perspective goes. The
connections a particular commentator draws across these same nodes, from a
book or a series of articles, would be a run under
`outputs/timeline/proposals/` with its own source prefix
(`perspective:<name>`), each edge carrying the work, the page and the
quoted passage, and would appear in the menu as its own line: the same
thinkers and events, connected the way that author connects them. Two
commentators give two lines, and the page shows where they agree and where
one draws a connection the other never makes. The ingest for that is not
built; its shape is the one `connect` already uses, with a text and page
references in place of the Wikipedia extract.

## Files

See [`index.md`](index.md). The commands are in `src/mueser/timeline/`;
`operations/` holds the exact invocations that produced what is here.
