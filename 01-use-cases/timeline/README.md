# Timeline

One case, [`01-thinkers-and-events/`](01-thinkers-and-events/): thinkers, works, events, periods and concepts on one band of years, every node cited and linked to the reference works, with layers for how they connect.

The design follows the mock-up Ben had made for the project some years ago: a grey band of periods and events over a year axis, the chosen figure's life beneath it with born and died marked, and three columns below, *Influenced by* on the left, the figure in the middle with overview, notable works, school of thought and a connection map, *Events* and *Influenced* on the right. Choosing an event turns the band's bar pale and the columns to its context, its outcome and the people connected to it.

What is different from the mock-up, and why:

- **The nodes are drawn by written rules from Wikidata**, not typed in. Every person with a Stanford Encyclopedia of Philosophy or Internet Encyclopedia of Philosophy entry, one hop of influence above a coverage threshold, their works, the wars, revolutions, treaties and periods with enough coverage, the concepts and movements. The rule is in `inputs/rules.json`, so the set can be widened or narrowed and rerun, and each node says which rule admitted it.
- **Every node is cited.** The Stanford citation is built from the entry's own metadata (title, authors, substantive revision); the overview is the Wikipedia lead with its revision and licence; the link-outs are the identifiers Wikidata holds (Britannica, the ODNB, Oxford Reference, Oxford Bibliographies, the OED, Deutsche Biographie, Treccani, Gutenberg, the Internet Archive, Open Library, VIAF, the Library of Congress, GND). A citation copies as text, Markdown or CSL-JSON for Zotero, and every copy is logged.
- **Connections have a source and a standing.** A Wikidata statement is *recorded*; a thinker-to-event connection a model read in the extract is *proposed*, quoting the sentence it rests on, until Ben accepts or rejects it; a connection Ben draws himself is *added here*. The layers menu shows connections by what they join (thinkers to thinkers, thinkers to events, works to works, …) and by whose they are. That second axis is where a further perspective goes: the connections one commentator draws across these same nodes, read from a book or article with its page references, as its own line in the menu beside the record and the model. The case README says how.

The group has no shared code beyond `src/mueser/timeline/`; the log-and-serve pattern is the reading room's.
