# Inputs

There is one input: `rules.json`, the written rule for what is in the node set and which Wikidata properties become edges. `collect` writes it on its first run from the defaults in `src/mueser/timeline/collect.py` and copies it into every run folder, so a run can always be read against the rule that produced it.

To change the set, edit the rule and rerun `collect` with a new run id:

- `people.expand.min_sitelinks`: how much Wikipedia coverage a person one hop from the seed needs (20 as shipped).
- `events.classes` and `events.periods`: the Wikidata classes admitted and each one's threshold; `events.year_range`: the years kept.
- `edges`: the properties read as connections and the name each gets.

Nothing else is an input. Ben's own additions, the connections he draws in the page, go to `outputs/timeline/log.jsonl`, not here. A further perspective (one commentator's connections, from a book or article) would arrive as a new folder under `outputs/timeline/proposals/` with its own source prefix and citations; see the README's last section.
