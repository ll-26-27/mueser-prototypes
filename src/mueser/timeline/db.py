"""Everything into one SQLite database and one JSON file for the page.

``timeline.sqlite`` is the database Ben can query (nodes, external ids, links, texts, citations, edges, and the
sources table that says what each identifier scheme is). ``timeline.json`` is the same content shaped for the
page: nodes with their links, overview text and citations; edges with their status. Both are written fresh by
``db`` from the latest collect run, the fetched sources, the latest proposals run and the log; the run folders
they were built from stay as they were and are named in ``data_id``.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from mueser.shared.runs import RunManifest, rel

from . import case_paths
from .collect import load_graph
from .log import edge_decisions, person_edges, read
from .sources import LINK_SCHEMES, image_url, links_for, load_sources, sep_citation

SCHEMA = """
CREATE TABLE nodes (
  id TEXT PRIMARY KEY, type TEXT NOT NULL, label TEXT NOT NULL, label_lang TEXT, description TEXT, rule TEXT,
  start_year INTEGER, start_label TEXT, start_precision INTEGER, end_year INTEGER, end_label TEXT, end_precision INTEGER,
  point INTEGER, birthplace TEXT, deathplace TEXT, locations TEXT, countries TEXT, occupations TEXT, language TEXT,
  genres TEXT, instances TEXT, sitelinks INTEGER, image TEXT, image_url TEXT, wiki_en TEXT, wiki_de TEXT
);
CREATE TABLE node_ids (node_id TEXT NOT NULL, scheme TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY (node_id, scheme));
CREATE TABLE links (node_id TEXT NOT NULL, scheme TEXT NOT NULL, name TEXT NOT NULL, kind TEXT, id TEXT, url TEXT NOT NULL);
CREATE TABLE texts (node_id TEXT PRIMARY KEY, source TEXT NOT NULL, lang TEXT, title TEXT, text TEXT NOT NULL, url TEXT,
  revision TEXT, timestamp TEXT, licence TEXT);
CREATE TABLE sep_entries (node_id TEXT PRIMARY KEY, entry_id TEXT NOT NULL, title TEXT, authors TEXT, published TEXT,
  pubinfo TEXT, url TEXT, citation TEXT);
CREATE TABLE citations (node_id TEXT NOT NULL, scheme TEXT NOT NULL, plain TEXT NOT NULL, csl_json TEXT);
CREATE TABLE edges (id TEXT PRIMARY KEY, type TEXT NOT NULL, src TEXT NOT NULL, dst TEXT NOT NULL, source TEXT NOT NULL,
  status TEXT NOT NULL, reason TEXT, evidence TEXT, verified INTEGER, work TEXT, model TEXT, decided_by TEXT, decided_at TEXT,
  decision_note TEXT, in_list INTEGER);
CREATE TABLE sources (scheme TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT, url_pattern TEXT);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE INDEX edges_src ON edges (src); CREATE INDEX edges_dst ON edges (dst); CREATE INDEX nodes_type ON nodes (type);
"""

EDGE_TYPES = {
    "influenced_by": {"label": "influenced by", "arrow": "src was influenced by dst", "kind": "recorded"},
    "student_of": {"label": "student of", "kind": "recorded"},
    "teacher_of": {"label": "teacher of", "kind": "recorded"},
    "doctoral_advisor": {"label": "doctoral advisor", "kind": "recorded"},
    "doctoral_student": {"label": "doctoral student", "kind": "recorded"},
    "author": {"label": "author", "kind": "recorded"},
    "notable_work": {"label": "notable work", "kind": "recorded"},
    "member_of_movement": {"label": "movement", "kind": "recorded"},
    "main_subject": {"label": "about", "kind": "recorded"},
    "part_of": {"label": "part of", "kind": "recorded"},
    "follows": {"label": "follows", "kind": "recorded"},
    "followed_by": {"label": "followed by", "kind": "recorded"},
    "has_cause": {"label": "caused by", "kind": "recorded"},
    "has_effect": {"label": "led to", "kind": "recorded"},
    "significant_event": {"label": "significant event", "kind": "recorded"},
    "participant_in": {"label": "took part in", "kind": "recorded"},
    "participant": {"label": "participant", "kind": "recorded"},
    "field_of_work": {"label": "field of work", "kind": "recorded"},
    "lived_through": {"label": "lived through", "kind": "proposed"},
    "took_part_in": {"label": "took part in", "kind": "proposed"},
    "wrote_in_response_to": {"label": "wrote in response to", "kind": "proposed"},
    "suffered_under": {"label": "suffered under", "kind": "proposed"},
    "shaped_by": {"label": "shaped by", "kind": "proposed"},
}


def _years(node: dict, key: str) -> tuple[int | None, str, int | None]:
    d = node.get(key) or {}
    return d.get("year"), d.get("label", ""), d.get("precision")


def _csl_sep(meta: dict, accessed: str) -> dict:
    authors = []
    for a in meta.get("authors") or []:
        parts = [p.strip() for p in a.split(",", 1)]
        authors.append({"family": parts[0], "given": parts[1]} if len(parts) == 2 else {"literal": a})
    y, m, d = (meta.get("published") or "").split("/") + ["", "", ""][: 3 - len((meta.get("published") or "").split("/"))]
    item = {
        "type": "entry-encyclopedia", "title": meta.get("title", ""), "container-title": "The Stanford Encyclopedia of Philosophy",
        "author": authors, "editor": [{"family": "Zalta", "given": "Edward N."}, {"family": "Nodelman", "given": "Uri"}],
        "URL": meta.get("url", ""), "accessed": {"date-parts": [[int(x) for x in accessed.split("-")]]},
    }
    if y:
        item["issued"] = {"date-parts": [[int(p) for p in (y, m, d) if p]]}
    return item


def citations_for(node: dict, sep_meta: dict | None, summary: dict | None, accessed: str) -> list[dict]:
    out: list[dict] = []
    if sep_meta and sep_meta.get("ok"):
        c = sep_citation(sep_meta, accessed)
        out.append({"scheme": "P3123", "name": "Stanford Encyclopedia of Philosophy", "plain": c["plain"], "csl": _csl_sep(sep_meta, accessed)})
    for prop, name in (("P5088", "Internet Encyclopedia of Philosophy"), ("P1417", "Encyclopædia Britannica"),
                       ("P1415", "Oxford Dictionary of National Biography"), ("P12582", "Oxford Reference"),
                       ("P7902", "Deutsche Biographie"), ("P7993", "Treccani, Dizionario di Filosofia")):
        val = node.get("ids", {}).get(prop)
        if val:
            url = LINK_SCHEMES[prop][1].format(val)
            out.append({"scheme": prop, "name": name, "plain": f'"{node["label"]}", {name}, URL = <{url}> (accessed {accessed}).',
                        "csl": {"type": "entry-encyclopedia", "title": node["label"], "container-title": name, "URL": url,
                                "accessed": {"date-parts": [[int(x) for x in accessed.split("-")]]}}})
    if summary and summary.get("url"):
        when = (summary.get("timestamp") or "")[:10]
        out.append({"scheme": f"wikipedia:{summary.get('lang')}", "name": f"Wikipedia ({summary.get('lang')})",
                    "plain": f'"{summary.get("title")}", Wikipedia, revision {summary.get("revision")} ({when}), URL = <{summary["url"]}>, CC BY-SA 4.0.',
                    "csl": {"type": "entry-encyclopedia", "title": summary.get("title"), "container-title": "Wikipedia",
                            "URL": summary["url"], "version": str(summary.get("revision")),
                            "accessed": {"date-parts": [[int(x) for x in accessed.split("-")]]}}})
    out.append({"scheme": "wikidata", "name": "Wikidata",
                "plain": f'Wikidata, item {node["id"]} ("{node["label"]}"), URL = <https://www.wikidata.org/wiki/{node["id"]}> (accessed {accessed}).',
                "csl": {"type": "dataset", "title": f'{node["label"]} ({node["id"]})', "container-title": "Wikidata",
                        "URL": f"https://www.wikidata.org/wiki/{node['id']}", "accessed": {"date-parts": [[int(x) for x in accessed.split("-")]]}}})
    return out


@contextmanager
def _staged_database(paths: dict[str, Path]):
    """Publish complete exports only after both have been generated successfully."""
    with TemporaryDirectory(prefix=".build-", dir=paths["timeline"]) as folder:
        database = Path(folder) / paths["db"].name
        document = Path(folder) / paths["json"].name
        connection = sqlite3.connect(database)
        try:
            yield connection, document
            connection.commit()
        finally:
            connection.close()
        # Stage on the same filesystem so readers never see a half-written file.
        database.replace(paths["db"])
        document.replace(paths["json"])


def build_db(case: Path, run: Path, proposals: Path | None, *, echo=print) -> tuple[Path, Path]:
    P = case_paths(case)
    t0 = time.time()
    nodes, edges = load_graph(run)
    sep, wp = load_sources(case)
    accessed = wp.get("accessed") or sep.get("accessed") or time.strftime("%Y-%m-%d")
    events = read(P["log"])
    decisions = edge_decisions(events)
    node_ids = {n["id"] for n in nodes}

    # proposals -> edges
    prop_run = proposals.name if proposals else None
    model = None
    if proposals:
        results = json.loads((proposals / "proposals.json").read_text(encoding="utf-8"))
        seen = {e["id"] for e in edges}
        for r in results:
            model = r.get("model") or model
            for p in r.get("proposals", []):
                if not p.get("in_list") or p["event"] not in node_ids or r["person"] not in node_ids:
                    continue
                eid = f"{p['type']}:{r['person']}:{p['event']}"
                if eid in seen:
                    continue
                seen.add(eid)
                edges.append({"id": eid, "type": p["type"], "src": r["person"], "dst": p["event"], "source": f"model:{r.get('model', '')}",
                              "status": "proposed", "reason": p.get("reason", ""), "evidence": p.get("evidence", ""),
                              "verified": bool(p.get("verified")), "work": p.get("work", ""), "model": r.get("model"), "in_list": True})
    for e in person_edges(events):
        if e["src"] in node_ids and e["dst"] in node_ids and e["id"] not in {x["id"] for x in edges}:
            edges.append(e)
    for e in edges:
        d = decisions.get(e["id"])
        if d and d.get("choice") in ("accept", "reject"):
            e["status"] = "accepted" if d["choice"] == "accept" else "rejected"
            e["decided_by"], e["decided_at"], e["decision_note"] = d["who"], d["ts"], d.get("note", "")

    data_id = f"{run.name}+{prop_run or 'no-proposals'}+{len(events)}ev"
    P["timeline"].mkdir(parents=True, exist_ok=True)
    with _staged_database(P) as (con, json_path):
        con.executescript(SCHEMA)
        for scheme, (name, pattern, kind) in LINK_SCHEMES.items():
            con.execute("INSERT INTO sources VALUES (?,?,?,?)", (scheme, name, kind, pattern))
        con.execute("INSERT INTO sources VALUES (?,?,?,?)", ("wikidata", "Wikidata", "item", "https://www.wikidata.org/wiki/{}"))

        page_nodes: list[dict] = []
        for n in nodes:
            sy, sl, sp = _years(n, "start")
            ey, el, ep = _years(n, "end")
            links = links_for(n)
            summary = wp["summaries"].get(n["id"])
            sep_meta = sep["entries"].get(n["id"])
            cites = citations_for(n, sep_meta, summary, accessed)
            con.execute("INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                n["id"], n["type"], n["label"], n.get("label_lang"), n.get("description", ""), n.get("rule"), sy, sl, sp, ey, el, ep,
                int(bool(n.get("point"))), n.get("birthplace"), n.get("deathplace"), "|".join(n.get("locations", [])),
                "|".join(n.get("countries", [])), "|".join(n.get("occupations", [])), n.get("language"), "|".join(n.get("genres", [])),
                "|".join(n.get("instances", [])), n.get("sitelinks", 0), n.get("image"), image_url(n), n.get("wiki", {}).get("en"),
                n.get("wiki", {}).get("de")))
            con.executemany("INSERT INTO node_ids VALUES (?,?,?)", [(n["id"], k, v) for k, v in n.get("ids", {}).items()])
            con.executemany("INSERT INTO links VALUES (?,?,?,?,?,?)", [(n["id"], L["scheme"], L["name"], L["kind"], L["id"], L["url"]) for L in links])
            if summary:
                con.execute("INSERT INTO texts VALUES (?,?,?,?,?,?,?,?,?)", (n["id"], "wikipedia", summary.get("lang"), summary.get("title"),
                            summary.get("extract", ""), summary.get("url"), str(summary.get("revision")), summary.get("timestamp"), summary.get("licence")))
            if sep_meta and sep_meta.get("ok"):
                c = sep_citation(sep_meta, accessed)
                con.execute("INSERT INTO sep_entries VALUES (?,?,?,?,?,?,?,?)", (n["id"], sep_meta["id"], sep_meta.get("title"),
                            "|".join(sep_meta.get("authors", [])), sep_meta.get("published"), sep_meta.get("pubinfo"), sep_meta.get("url"), c["plain"]))
            con.executemany("INSERT INTO citations VALUES (?,?,?,?)", [(n["id"], c["scheme"], c["plain"], json.dumps(c["csl"], ensure_ascii=False)) for c in cites])
            page_nodes.append({
                "id": n["id"], "type": n["type"], "label": n["label"], "desc": n.get("description", ""), "rule": n.get("rule"),
                "sy": sy, "sl": sl, "ey": ey, "el": el, "pt": bool(n.get("point")),
                "place": {k: v for k, v in (("birth", n.get("birthplace")), ("death", n.get("deathplace"))) if v} | (
                    {"at": n["locations"]} if n.get("locations") else {}),
                "countries": n.get("countries", []), "occ": n.get("occupations", []), "lang": n.get("language"), "genres": n.get("genres", []),
                "inst": n.get("instances", [])[:3], "img": image_url(n), "sl_n": n.get("sitelinks", 0), "links": links,
                "text": {"t": summary.get("extract", ""), "title": summary.get("title"), "url": summary.get("url"), "lang": summary.get("lang"),
                         "rev": summary.get("revision"), "ts": summary.get("timestamp")} if summary else None,
                "sep": {"title": sep_meta.get("title"), "authors": sep_meta.get("authors"), "pubinfo": sep_meta.get("pubinfo"), "url": sep_meta.get("url")}
                       if sep_meta and sep_meta.get("ok") else None,
                "cite": cites,
            })

        for e in edges:
            con.execute("INSERT INTO edges VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                e["id"], e["type"], e["src"], e["dst"], e["source"], e["status"], e.get("reason"), e.get("evidence"),
                int(bool(e.get("verified"))) if "verified" in e else None, e.get("work"), e.get("model"), e.get("decided_by"),
                e.get("decided_at"), e.get("decision_note"), int(bool(e.get("in_list"))) if "in_list" in e else None))
        for k, v in (("data_id", data_id), ("collect_run", run.name), ("proposals_run", prop_run or ""), ("accessed", accessed),
                     ("built", time.strftime("%Y-%m-%dT%H:%M:%S%z")), ("events", str(len(events)))):
            con.execute("INSERT INTO meta VALUES (?,?)", (k, v))

        page_edges = [{k: v for k, v in e.items() if k in ("id", "type", "src", "dst", "source", "status", "reason", "evidence", "verified", "work",
                                                            "decided_by", "decided_at", "decision_note")} for e in edges]
        data = {"data_id": data_id, "collect_run": run.name, "proposals_run": prop_run, "accessed": accessed, "model": model,
                "built": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "edge_types": EDGE_TYPES, "nodes": page_nodes, "edges": page_edges}
        json_path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    from collections import Counter
    nc, ec, sc = Counter(n["type"] for n in nodes), Counter(e["type"] for e in edges), Counter(e["status"] for e in edges)
    RunManifest(run_id=f"db-{time.strftime('%Y%m%d-%H%M%S')}", step="timeline.db",
                params={"collect_run": run.name, "proposals_run": prop_run, "data_id": data_id},
                inputs=[rel(run), rel(P["sources"]), rel(proposals) if proposals else "", rel(P["log"])],
                outputs=[rel(P["db"]), rel(P["json"])], seconds=round(time.time() - t0, 1),
                notes=[f"nodes {dict(nc)}", f"edges {dict(ec)}", f"status {dict(sc)}"]).write(P["timeline"])
    echo(f"{sum(nc.values())} nodes {dict(nc)}; {sum(ec.values())} edges, status {dict(sc)}; data_id {data_id}")
    return P["db"], P["json"]
