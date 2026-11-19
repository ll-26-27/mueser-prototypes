"""Tests for the timeline on invented data: dates, the connection check, the log, the database and the page.

Nothing here touches the network. Node and edge records are shaped as collect.py writes them.
"""

import json
import sqlite3
from pathlib import Path

from mueser.timeline import case_paths
from mueser.timeline.build import build, noscript_block, render
from mueser.timeline.connect import candidates, verify
from mueser.timeline.db import build_db, citations_for
from mueser.timeline.log import Anchor, append, edge_decisions, ingest, make, person_edges, read
from mueser.timeline.sources import links_for, sep_citation
from mueser.timeline.wikidata import date_label, year_of


def test_year_of_handles_bce_and_precision_labels():
    assert year_of("1588-04-05T00:00:00Z") == 1588
    assert year_of("-0384-01-01T00:00:00Z") == -384
    assert year_of(None) is None
    assert date_label("1588-04-05T00:00:00Z", 11) == "1588-04-05"
    assert date_label("1588-04-05T00:00:00Z", 9) == "1588"
    assert date_label("1640-01-01T00:00:00Z", 8) == "1640s"
    assert date_label("1601-01-01T00:00:00Z", 7) == "17th century"
    assert date_label("-0384-01-01T00:00:00Z", 9) == "384 BCE"


def test_links_and_sep_citation():
    node = {"id": "Q37621", "label": "Thomas Hobbes", "ids": {"P3123": "hobbes", "P1417": "biography/Thomas-Hobbes"},
            "wiki": {"en": "Thomas Hobbes"}, "image": "http://commons.wikimedia.org/wiki/Special:FilePath/Thomas%20Hobbes.jpg"}
    links = links_for(node)
    urls = {L["scheme"]: L["url"] for L in links}
    assert urls["P3123"] == "https://plato.stanford.edu/entries/hobbes/"
    assert urls["P1417"] == "https://www.britannica.com/biography/Thomas-Hobbes"
    assert urls["wikipedia:en"] == "https://en.wikipedia.org/wiki/Thomas_Hobbes"
    assert urls["wikidata"].endswith("/Q37621") and "commons" in urls
    meta = {"id": "hobbes", "url": "https://plato.stanford.edu/entries/hobbes/", "ok": True, "title": "Thomas Hobbes",
            "authors": ["Duncan, Stewart"], "published": "2009/03/11", "pubinfo": "First published Wed Mar 11, 2009; substantive revision Sat Mar 1, 2025"}
    c = sep_citation(meta, "2026-11-19")
    assert c["plain"].startswith('Duncan, Stewart, "Thomas Hobbes", The Stanford Encyclopedia of Philosophy (Sat Mar 1, 2025)')
    assert "plato.stanford.edu/entries/hobbes" in c["plain"]
    two = sep_citation({**meta, "authors": ["Duncan, Stewart", "Lloyd, Sharon A."]}, "2026-11-19")
    assert two["who"] == "Duncan, Stewart and Sharon A. Lloyd"


def test_candidates_and_verify():
    person = {"id": "Q1", "label": "A", "start": {"year": 1588}, "end": {"year": 1679}}
    events = [{"id": "E1", "label": "civil war", "start": {"year": 1642}, "end": {"year": 1651}},
              {"id": "E2", "label": "later", "start": {"year": 1700}, "end": {"year": 1710}},
              {"id": "E3", "label": "undated"}]
    assert [e["id"] for e in candidates(person, events)] == ["E1"]
    extract = "Hobbes fled to Paris in 1640, where he stayed through the English Civil War.  He wrote Leviathan there."
    ok = verify({"event": "E1", "type": "lived_through", "evidence": "He wrote Leviathan there.", "reason": "r", "work": ""}, extract, {"E1"})
    assert ok["verified"] and ok["in_list"] and ok["status"] == "proposed"
    spaced = verify({"event": "E1", "type": "lived_through", "evidence": "he wrote leviathan  there", "reason": "r", "work": ""}, extract, {"E1"})
    assert spaced["verified"], "spacing and case differences are not a mismatch"
    bad = verify({"event": "E9", "type": "lived_through", "evidence": "He returned to London in 1651.", "reason": "r", "work": ""}, extract, {"E1"})
    assert not bad["verified"] and not bad["in_list"]


def test_log_round_trip_decisions_and_ingest(tmp_path):
    log = tmp_path / "log.jsonl"
    d1 = make("decision", who="x", anchor=Anchor(node="Q1", edge="lived_through:Q1:E1"), body={"choice": "accept"})
    d2 = make("decision", who="x", anchor=Anchor(node="Q1", edge="lived_through:Q1:E1"), body={"choice": "reject", "note": "no"})
    e1 = make("edge", who="x", anchor=Anchor(node="Q1"), body={"src": "Q1", "dst": "E1", "type": "took_part_in", "reason": "r"})
    for ev in (d1, d2, e1):
        append(log, ev)
    events = read(log)
    assert [e.id for e in events] == [d1.id, d2.id, e1.id]
    assert edge_decisions(events)["lived_through:Q1:E1"]["choice"] == "reject"
    pe = person_edges(events)
    assert pe[0]["id"] == "took_part_in:Q1:E1" and pe[0]["status"] == "person"
    inbox = tmp_path / "inbox"; inbox.mkdir()
    q = make("question", who="y", anchor=Anchor(node="Q1", quote="A"), body={"text": "why?"})
    (inbox / "export.jsonl").write_text(d1.model_dump_json() + "\n" + q.model_dump_json() + "\nnot json\n", encoding="utf-8")
    assert ingest(inbox, log) == {"added": 1, "duplicate": 1, "invalid": 1, "files": 1}
    assert len(read(log)) == 4


def _synthetic_case(tmp_path: Path) -> Path:
    case = tmp_path / "case"
    P = case_paths(case)
    run = P["runs"] / "collect-synthetic-01"
    run.mkdir(parents=True)
    nodes = [
        {"id": "Q1", "type": "person", "rule": "seed:sep", "label": "Synthetic Thinker", "label_lang": "en", "description": "invented philosopher",
         "sitelinks": 12, "image": None, "wiki": {"en": "Synthetic Thinker"}, "instances": ["human"], "ids": {"P3123": "synthetic"},
         "start": {"value": "1588-04-05T00:00:00Z", "year": 1588, "precision": 11, "label": "1588-04-05"},
         "end": {"value": "1679-12-04T00:00:00Z", "year": 1679, "precision": 11, "label": "1679-12-04"},
         "birthplace": "Nowhere", "deathplace": None, "countries": ["Utopia"], "occupations": ["philosopher"]},
        {"id": "W1", "type": "work", "rule": "work:P800", "label": "Synthetic Treatise", "description": "", "sitelinks": 3, "image": None, "wiki": {},
         "instances": ["book"], "ids": {"P2034": "12345"}, "start": {"value": "1651-01-01T00:00:00Z", "year": 1651, "precision": 9, "label": "1651"}, "end": None,
         "language": "English", "title": "Synthetic Treatise", "genres": []},
        {"id": "E1", "type": "event", "rule": "event:Q198", "label": "Synthetic War", "description": "an invented war", "sitelinks": 40, "image": None,
         "wiki": {"en": "Synthetic War"}, "instances": ["war"], "ids": {}, "start": {"value": "1642-01-01T00:00:00Z", "year": 1642, "precision": 9, "label": "1642"},
         "end": {"value": "1651-01-01T00:00:00Z", "year": 1651, "precision": 9, "label": "1651"}, "point": False, "locations": [], "countries": ["Utopia"]},
        {"id": "C1", "type": "concept", "rule": "seed:sep", "label": "Synthetic Contract", "description": "", "sitelinks": 9, "image": None, "wiki": {},
         "instances": [], "ids": {"P3123": "synthetic-contract"}, "start": None, "end": None, "point": False, "locations": [], "countries": []},
    ]
    edges = [
        {"id": "author:W1:Q1", "type": "author", "src": "W1", "dst": "Q1", "source": "wikidata:P50", "status": "recorded"},
        {"id": "main_subject:W1:C1", "type": "main_subject", "src": "W1", "dst": "C1", "source": "wikidata:P921", "status": "recorded"},
    ]
    (run / "nodes.json").write_text(json.dumps(nodes), encoding="utf-8")
    (run / "edges.json").write_text(json.dumps(edges), encoding="utf-8")
    (run / "run.json").write_text("{}", encoding="utf-8")
    P["sources"].mkdir(parents=True)
    (P["sources"] / "sep.json").write_text(json.dumps({"accessed": "2026-11-19", "entries": {"Q1": {
        "id": "synthetic", "url": "https://plato.stanford.edu/entries/synthetic/", "ok": True, "title": "Synthetic Thinker",
        "authors": ["Author, Some"], "published": "2010/01/02", "pubinfo": "First published Sat Jan 2, 2010"}}}), encoding="utf-8")
    (P["sources"] / "wikipedia.json").write_text(json.dumps({"accessed": "2026-11-19", "summaries": {"Q1": {
        "lang": "en", "title": "Synthetic Thinker", "extract": "Synthetic Thinker lived through the Synthetic War. He wrote the Synthetic Treatise.",
        "revision": "1", "timestamp": "2026-11-01T00:00:00Z", "url": "https://en.wikipedia.org/wiki/Synthetic_Thinker", "licence": "CC BY-SA 4.0"}}}), encoding="utf-8")
    prop = P["proposals"] / "connect-synthetic-01"
    prop.mkdir(parents=True)
    (prop / "proposals.json").write_text(json.dumps([{"person": "Q1", "model": "synthetic/model", "proposals": [
        {"event": "E1", "type": "lived_through", "reason": "says so", "evidence": "Synthetic Thinker lived through the Synthetic War.", "work": "",
         "in_list": True, "verified": True, "status": "proposed"},
        {"event": "E9", "type": "lived_through", "reason": "outside the list", "evidence": "x", "work": "", "in_list": False, "verified": False, "status": "proposed"}]}]),
        encoding="utf-8")
    return case


def test_db_build_and_page(tmp_path):
    case = _synthetic_case(tmp_path)
    P = case_paths(case)
    run = P["runs"] / "collect-synthetic-01"
    prop = P["proposals"] / "connect-synthetic-01"
    # a decision in the log rejects the proposal; a person adds an edge of their own
    append(P["log"], make("decision", who="t", anchor=Anchor(node="Q1", edge="lived_through:Q1:E1"), body={"choice": "reject"}))
    append(P["log"], make("edge", who="t", anchor=Anchor(node="Q1"), body={"src": "Q1", "dst": "E1", "type": "took_part_in", "reason": "invented"}))
    db, js = build_db(case, run, prop, echo=lambda *a: None)
    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0] == 4
    rows = {r[0]: r for r in con.execute("SELECT id, status, source, verified FROM edges")}
    assert rows["lived_through:Q1:E1"][1] == "rejected" and rows["lived_through:Q1:E1"][2] == "model:synthetic/model" and rows["lived_through:Q1:E1"][3] == 1
    assert "lived_through:Q1:E9" not in rows, "a proposal naming an event outside the list is not an edge"
    assert rows["took_part_in:Q1:E1"][1] == "person"
    assert rows["author:W1:Q1"][1] == "recorded"
    assert con.execute("SELECT COUNT(*) FROM citations WHERE node_id='Q1'").fetchone()[0] == 3  # SEP, Wikipedia, Wikidata
    sep = con.execute("SELECT citation FROM sep_entries WHERE node_id='Q1'").fetchone()[0]
    assert sep.startswith('Author, Some, "Synthetic Thinker", The Stanford Encyclopedia of Philosophy')
    assert con.execute("SELECT url FROM links WHERE node_id='W1' AND scheme='P2034'").fetchone()[0] == "https://www.gutenberg.org/ebooks/12345"
    data = json.loads(js.read_text(encoding="utf-8"))
    assert data["nodes"][0]["sep"]["title"] == "Synthetic Thinker" and data["nodes"][0]["text"]["t"].startswith("Synthetic Thinker lived")
    assert {e["id"] for e in data["edges"]} == set(rows)
    out = build(case, echo=lambda *a: None)
    doc = out.read_text(encoding="utf-8")
    assert 'id="timeline-data"' in doc and "Synthetic War (1642–1651)" in noscript_block(data)
    assert "\\u003c" in render(data, [], title="t") or "<script" not in json.dumps(data), "embedded JSON must not close the script tag"
    assert "Synthetic Treatise" in doc and 'mueser-review:start' in doc


def test_citations_without_sep_or_summary():
    node = {"id": "Q9", "label": "Nobody", "ids": {"P1417": "topic/x"}, "wiki": {}}
    cites = citations_for(node, None, None, "2026-11-19")
    assert [c["scheme"] for c in cites] == ["P1417", "wikidata"]
    assert cites[0]["csl"]["container-title"] == "Encyclopædia Britannica"
