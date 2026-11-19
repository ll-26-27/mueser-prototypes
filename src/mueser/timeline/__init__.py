"""mueser.timeline: thinkers, works and events on one timeline, with every node cited.

The node set is drawn from Wikidata by written rules (``collect``): every person with an entry in the Stanford
Encyclopedia of Philosophy or the Internet Encyclopedia of Philosophy, the people they influenced, taught or
studied under, their works, the historical periods, wars, revolutions and treaties with enough Wikipedia
coverage to matter, and the concepts and movements those encyclopedias and Wikidata name. Every node keeps
its Wikidata id and every external identifier Wikidata has for it, so a citation is a link to a real entry.

Steps, each a command of ``python -m mueser.timeline``:

- ``collect``   Wikidata -> nodes and recorded edges, by the rules in ``collect.py`` (one run folder)
- ``sources``   Stanford Encyclopedia entry pages and Wikipedia summaries for every node, cached raw
- ``connect``   a model proposes typed person-to-event connections from the fetched texts; verified verbatim
- ``db``        everything into ``outputs/timeline/timeline.sqlite`` and one JSON for the page
- ``build``     the JSON + the log -> one self-contained ``outputs/index.html``
- ``serve``     the page on 127.0.0.1 with ``POST /api/log`` appending to the log
- ``ingest``    exported browser logs -> the log
"""

from pathlib import Path

WEB = Path(__file__).parent / "web"


def case_paths(case: Path) -> dict[str, Path]:
    case = Path(case)
    out = case / "outputs"
    tl = out / "timeline"
    return {
        "case": case,
        "inputs": case / "inputs",
        "rules": case / "inputs" / "rules.json",
        "out": out,
        "timeline": tl,
        "runs": tl / "runs",
        "graph": tl / "graph",
        "sources": tl / "sources",
        "proposals": tl / "proposals",
        "db": tl / "timeline.sqlite",
        "json": tl / "timeline.json",
        "log": tl / "log.jsonl",
        "inbox": tl / "inbox",
        "index": out / "index.html",
    }
