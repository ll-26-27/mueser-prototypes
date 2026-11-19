"""Collect the node set and the recorded edges from Wikidata, by written rules.

The rules live in ``inputs/rules.json`` and are copied into the run folder, so a node can always be traced to
the rule that admitted it (``node["rule"]``). Nothing here is model judgment: every node is a Wikidata item
that matched a rule, every edge a Wikidata statement between two such items, and each carries the property
it came from (``edge["source"] == "wikidata:P737"``).

Rules, as shipped:

- **people**: every human with a Stanford Encyclopedia of Philosophy ID (P3123) or an Internet Encyclopedia of
  Philosophy ID (P5088) is a *seed*; everyone a seed influenced or was influenced by (P737), taught or was taught
  by (P1066/P802), supervised or was supervised by (P184/P185) joins if the item has at least ``min_sitelinks``
  Wikipedia articles (a coverage threshold, recorded, not a judgment of importance).
- **works**: every notable work (P800) of a person in the set, and every work whose author (P50) is in the set
  with at least ``min_sitelinks`` articles.
- **events and periods**: every item that is an instance of (a subclass of) one of the listed classes (wars,
  revolutions, treaties, historical periods, …) with at least the class's ``min_sitelinks`` articles and a date
  inside ``year_range``; plus every event a person in the set took part in (P1344) or is recorded as a
  significant event of (P793), whatever its coverage.
- **concepts**: every non-human item with an SEP or IEP ID, and every movement (P135) a person in the set
  belongs to.

Queries never use DISTINCT over a VALUES list: on the live endpoint that shape ran into the 60-second limit
and returned hundreds of megabytes of partial output, where the same query without it answered in under a
second. Duplicates are removed here instead.

Output: one run folder ``outputs/timeline/runs/collect-<id>/`` with ``nodes.json``, ``edges.json``, the rules
used and ``run.json``.
"""

from __future__ import annotations

import json
import shutil
import time
from collections import Counter
from pathlib import Path

from mueser.shared.runs import RunManifest, rel, run_id

from . import case_paths
from .wikidata import batched, date_label, qid, sparql, split_multi, values, year_of

SEP = "␟"  # the separator GROUP_CONCAT uses; it never occurs in labels

# External identifiers kept on every node, with the reference work each one names. The URL patterns live in
# sources.py; here only the property list, so the collect run records exactly what was asked for.
ID_PROPS = {
    "P3123": "Stanford Encyclopedia of Philosophy",
    "P5088": "Internet Encyclopedia of Philosophy",
    "P1417": "Encyclopædia Britannica Online",
    "P1415": "Oxford Dictionary of National Biography",
    "P12582": "Oxford Reference",
    "P8410": "Oxford Bibliographies",
    "P5275": "Oxford English Dictionary (entry, pre-2023)",
    "P12510": "Oxford English Dictionary (object)",
    "P9106": "Oxford Classical Dictionary",
    "P7902": "Deutsche Biographie",
    "P7993": "Treccani, Dizionario di Filosofia",
    "P3365": "Treccani",
    "P11802": "Zeno.org",
    "P1938": "Project Gutenberg (author)",
    "P2034": "Project Gutenberg (ebook)",
    "P724": "Internet Archive",
    "P648": "Open Library",
    "P243": "OCLC",
    "P214": "VIAF",
    "P244": "Library of Congress",
    "P227": "GND",
    "P3732": "PhilPapers record",
    "P1296": "Gran Enciclopèdia Catalana",
}

DEFAULT_RULES = {
    "written": "2026-11-19",
    "people": {
        "seed": "instance of human (Q5) with a Stanford Encyclopedia of Philosophy ID (P3123) or an Internet Encyclopedia of Philosophy ID (P5088)",
        "expand": {
            "properties": {"P737": "influenced by", "P737^": "influenced", "P1066": "student of", "P802": "student",
                            "P184": "doctoral advisor", "P185": "doctoral student"},
            "min_sitelinks": 20,
            "note": "one hop from the seed; the sitelink count is Wikipedia coverage, used as a threshold and recorded on the node",
        },
    },
    "works": {
        "notable": "P800 (notable work) of every person in the set",
        "authored": {"property": "P50", "min_sitelinks": 8},
    },
    "events": {
        "classes": {
            "Q198": {"label": "war", "min_sitelinks": 25},
            "Q8465": {"label": "civil war", "min_sitelinks": 25},
            "Q10931": {"label": "revolution", "min_sitelinks": 20},
            "Q124734": {"label": "rebellion", "min_sitelinks": 30},
            "Q131569": {"label": "treaty", "min_sitelinks": 30},
            "Q178561": {"label": "battle", "min_sitelinks": 50},
            "Q45382": {"label": "coup d'état", "min_sitelinks": 40},
            "Q3199915": {"label": "massacre", "min_sitelinks": 40},
            "Q12184": {"label": "pandemic", "min_sitelinks": 40},
            "Q168247": {"label": "famine", "min_sitelinks": 40},
            "Q13418847": {"label": "historical event", "min_sitelinks": 40},
            "Q7755": {"label": "constitution", "min_sitelinks": 40},
        },
        "periods": {
            "Q11514315": {"label": "historical period", "min_sitelinks": 30},
            "Q6428674": {"label": "era", "min_sitelinks": 30},
        },
        "year_range": [-800, 2030],
        "linked": {"P793": "significant event", "P1344": "participant in"},
        "note": "an instance of a subclass is included (P31/P279*); an item with no usable date is dropped and counted",
    },
    "concepts": {
        "seed": "items that are not humans, with a Stanford Encyclopedia of Philosophy ID (P3123) or an Internet Encyclopedia of Philosophy ID (P5088)",
        "movements": "P135 (movement) of every person in the set",
    },
    "edges": {
        "P737": "influenced_by", "P1066": "student_of", "P802": "teacher_of", "P184": "doctoral_advisor",
        "P185": "doctoral_student", "P50": "author", "P800": "notable_work", "P135": "member_of_movement",
        "P921": "main_subject", "P361": "part_of", "P155": "follows", "P156": "followed_by", "P828": "has_cause",
        "P1542": "has_effect", "P793": "significant_event", "P1344": "participant_in", "P710": "participant",
        "P101": "field_of_work", "P1066^": None,
    },
    "external_ids": ID_PROPS,
}


# ----------------------------------------------------------------------------------------------- queries

def seed_people() -> dict[str, str]:
    rows = sparql("""SELECT ?x ?sep ?iep WHERE {
      { ?x wdt:P3123 ?sep } UNION { ?x wdt:P5088 ?iep }
      ?x wdt:P31 wd:Q5 . }""")
    out: dict[str, str] = {}
    for r in rows:
        q = qid(r["x"])
        rule = out.get(q, "")
        if r.get("sep"):
            rule = "seed:sep"
        elif not rule:
            rule = "seed:iep"
        out[q] = rule
    return out


def seed_concepts() -> dict[str, str]:
    rows = sparql("""SELECT ?x ?sep ?iep WHERE {
      { ?x wdt:P3123 ?sep } UNION { ?x wdt:P5088 ?iep }
      FILTER NOT EXISTS { ?x wdt:P31 wd:Q5 } }""")
    out: dict[str, str] = {}
    for q, r in ((qid(r["x"]), r) for r in rows):
        out[q] = "seed:sep" if r.get("sep") else out.get(q, "seed:iep")
    return out


def expand_people(seed: list[str], min_sitelinks: int) -> dict[str, str]:
    """One hop from the seed along each expansion property; one plain query per property and chunk."""
    found: dict[str, tuple[int, str]] = {}
    patterns = {"P737": "?x wdt:P737 ?y", "P737^": "?y wdt:P737 ?x", "P1066": "?x wdt:P1066 ?y",
                "P802": "?x wdt:P802 ?y", "P184": "?x wdt:P184 ?y", "P185": "?x wdt:P185 ?y"}
    for chunk in batched(seed, 200):
        for via, pattern in patterns.items():
            rows = sparql(f"""SELECT ?y ?n WHERE {{ VALUES ?x {{ {values(chunk)} }}
              {pattern} . ?y wdt:P31 wd:Q5 ; wikibase:sitelinks ?n . }}""")
            for r in rows:
                n = int(r["n"])
                if n >= min_sitelinks:
                    q = qid(r["y"])
                    if q not in found or found[q][0] < n:
                        found[q] = (n, f"expand:{via}")
    return {q: rule for q, (_, rule) in found.items()}


def works_of(people: list[str], min_sitelinks: int) -> dict[str, str]:
    out: dict[str, str] = {}
    for chunk in batched(people, 200):
        for r in sparql(f"""SELECT ?w WHERE {{ VALUES ?x {{ {values(chunk)} }} ?x wdt:P800 ?w . }}"""):
            out[qid(r["w"])] = "work:P800"
        for r in sparql(f"""SELECT ?w WHERE {{ VALUES ?x {{ {values(chunk)} }}
            ?w wdt:P50 ?x ; wikibase:sitelinks ?n . FILTER(?n >= {min_sitelinks}) }}"""):
            out.setdefault(qid(r["w"]), "work:P50")
    return out


def events_by_class(classes: dict[str, dict], kind: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for cls, spec in classes.items():
        rows = sparql(f"""SELECT ?e WHERE {{
          ?e wdt:P31/wdt:P279* wd:{cls} ; wikibase:sitelinks ?n . FILTER(?n >= {int(spec['min_sitelinks'])}) }}""")
        for r in rows:
            out.setdefault(qid(r["e"]), f"{kind}:{cls}")
    return out


def events_linked(people: list[str], props: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for chunk in batched(people, 200):
        for p in props:
            for r in sparql(f"""SELECT ?e WHERE {{ VALUES ?x {{ {values(chunk)} }} ?x wdt:{p} ?e .
                FILTER NOT EXISTS {{ ?e wdt:P31 wd:Q5 }} }}"""):
                out.setdefault(qid(r["e"]), f"event:{p}")
    return out


def movements_of(people: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for chunk in batched(people, 200):
        for r in sparql(f"""SELECT ?m WHERE {{ VALUES ?x {{ {values(chunk)} }} ?x wdt:P135 ?m . }}"""):
            out[qid(r["m"])] = "concept:P135"
    return out


def common_fields(ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for chunk in batched(ids, 250):
        rows = sparql(f"""SELECT ?x (SAMPLE(?labelEn) AS ?len) (SAMPLE(?labelDe) AS ?lde) (SAMPLE(?labelFr) AS ?lfr)
            (SAMPLE(?desc) AS ?description) (SAMPLE(?n) AS ?sitelinks) (SAMPLE(?img) AS ?image)
            (SAMPLE(?enwiki) AS ?en) (SAMPLE(?dewiki) AS ?de)
            (GROUP_CONCAT(DISTINCT ?instLabel; separator="{SEP}") AS ?instances)
          WHERE {{ VALUES ?x {{ {values(chunk)} }}
            OPTIONAL {{ ?x rdfs:label ?labelEn FILTER(LANG(?labelEn)="en") }}
            OPTIONAL {{ ?x rdfs:label ?labelDe FILTER(LANG(?labelDe)="de") }}
            OPTIONAL {{ ?x rdfs:label ?labelFr FILTER(LANG(?labelFr)="fr") }}
            OPTIONAL {{ ?x schema:description ?desc FILTER(LANG(?desc)="en") }}
            OPTIONAL {{ ?x wikibase:sitelinks ?n }}
            OPTIONAL {{ ?x wdt:P18 ?img }}
            OPTIONAL {{ ?a schema:about ?x ; schema:isPartOf <https://en.wikipedia.org/> ; schema:name ?enwiki }}
            OPTIONAL {{ ?b schema:about ?x ; schema:isPartOf <https://de.wikipedia.org/> ; schema:name ?dewiki }}
            OPTIONAL {{ ?x wdt:P31 ?inst . ?inst rdfs:label ?instLabel FILTER(LANG(?instLabel)="en") }}
          }} GROUP BY ?x""")
        for r in rows:
            q = qid(r["x"])
            out[q] = {
                "label": r.get("len") or r.get("lde") or r.get("lfr") or q,
                "label_lang": "en" if r.get("len") else "de" if r.get("lde") else "fr" if r.get("lfr") else None,
                "description": r.get("description") or "",
                "sitelinks": int(r["sitelinks"]) if r.get("sitelinks") else 0,
                "image": r.get("image"),
                "wiki": {k: v for k, v in (("en", r.get("en")), ("de", r.get("de"))) if v},
                "instances": split_multi(r.get("instances")),
            }
    return out


def external_ids(ids: list[str]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    props = list(ID_PROPS)
    for chunk in batched(ids, 250):
        sel = " ".join(f"(SAMPLE(?v{p}) AS ?{p})" for p in props)
        opts = " ".join(f"OPTIONAL {{ ?x wdt:{p} ?v{p} }}" for p in props)
        rows = sparql(f"SELECT ?x {sel} WHERE {{ VALUES ?x {{ {values(chunk)} }} {opts} }} GROUP BY ?x")
        for r in rows:
            out[qid(r["x"])] = {p: r[p] for p in props if r.get(p)}
    return out


def person_fields(ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for chunk in batched(ids, 250):
        rows = sparql(f"""SELECT ?x (SAMPLE(?b) AS ?birth) (SAMPLE(?bp) AS ?birthPrec) (SAMPLE(?d) AS ?death)
            (SAMPLE(?dp) AS ?deathPrec) (SAMPLE(?pobL) AS ?birthplace) (SAMPLE(?podL) AS ?deathplace)
            (GROUP_CONCAT(DISTINCT ?cL; separator="{SEP}") AS ?countries)
            (GROUP_CONCAT(DISTINCT ?oL; separator="{SEP}") AS ?occupations)
          WHERE {{ VALUES ?x {{ {values(chunk)} }}
            OPTIONAL {{ ?x p:P569 ?bs . ?bs a wikibase:BestRank ; psv:P569 [ wikibase:timeValue ?b ; wikibase:timePrecision ?bp ] }}
            OPTIONAL {{ ?x p:P570 ?ds . ?ds a wikibase:BestRank ; psv:P570 [ wikibase:timeValue ?d ; wikibase:timePrecision ?dp ] }}
            OPTIONAL {{ ?x wdt:P19 ?pob . ?pob rdfs:label ?pobL FILTER(LANG(?pobL)="en") }}
            OPTIONAL {{ ?x wdt:P20 ?pod . ?pod rdfs:label ?podL FILTER(LANG(?podL)="en") }}
            OPTIONAL {{ ?x wdt:P27 ?c . ?c rdfs:label ?cL FILTER(LANG(?cL)="en") }}
            OPTIONAL {{ ?x wdt:P106 ?o . ?o rdfs:label ?oL FILTER(LANG(?oL)="en") }}
          }} GROUP BY ?x""")
        for r in rows:
            out[qid(r["x"])] = {
                "start": _date(r.get("birth"), r.get("birthPrec")),
                "end": _date(r.get("death"), r.get("deathPrec")),
                "birthplace": r.get("birthplace"),
                "deathplace": r.get("deathplace"),
                "countries": split_multi(r.get("countries")),
                "occupations": split_multi(r.get("occupations"))[:6],
            }
    return out


def span_fields(ids: list[str]) -> dict[str, dict]:
    """Start, end, point in time, inception and location for events, periods, movements and concepts."""
    out: dict[str, dict] = {}
    for chunk in batched(ids, 250):
        rows = sparql(f"""SELECT ?x (SAMPLE(?s) AS ?start) (SAMPLE(?sp) AS ?startPrec) (SAMPLE(?e) AS ?end)
            (SAMPLE(?ep) AS ?endPrec) (SAMPLE(?t) AS ?point) (SAMPLE(?tp) AS ?pointPrec)
            (SAMPLE(?i) AS ?inception) (SAMPLE(?ip) AS ?inceptionPrec)
            (GROUP_CONCAT(DISTINCT ?locL; separator="{SEP}") AS ?locations)
            (GROUP_CONCAT(DISTINCT ?cL; separator="{SEP}") AS ?countries)
          WHERE {{ VALUES ?x {{ {values(chunk)} }}
            OPTIONAL {{ ?x p:P580 ?ss . ?ss a wikibase:BestRank ; psv:P580 [ wikibase:timeValue ?s ; wikibase:timePrecision ?sp ] }}
            OPTIONAL {{ ?x p:P582 ?es . ?es a wikibase:BestRank ; psv:P582 [ wikibase:timeValue ?e ; wikibase:timePrecision ?ep ] }}
            OPTIONAL {{ ?x p:P585 ?ts . ?ts a wikibase:BestRank ; psv:P585 [ wikibase:timeValue ?t ; wikibase:timePrecision ?tp ] }}
            OPTIONAL {{ ?x p:P571 ?is . ?is a wikibase:BestRank ; psv:P571 [ wikibase:timeValue ?i ; wikibase:timePrecision ?ip ] }}
            OPTIONAL {{ ?x wdt:P276 ?loc . ?loc rdfs:label ?locL FILTER(LANG(?locL)="en") }}
            OPTIONAL {{ ?x wdt:P17 ?c . ?c rdfs:label ?cL FILTER(LANG(?cL)="en") }}
          }} GROUP BY ?x""")
        for r in rows:
            start = _date(r.get("start"), r.get("startPrec")) or _date(r.get("point"), r.get("pointPrec")) \
                or _date(r.get("inception"), r.get("inceptionPrec"))
            end = _date(r.get("end"), r.get("endPrec")) or (_date(r.get("point"), r.get("pointPrec")) if not r.get("start") else None)
            out[qid(r["x"])] = {
                "start": start, "end": end,
                "point": bool(r.get("point")) and not r.get("start"),
                "locations": split_multi(r.get("locations"))[:4],
                "countries": split_multi(r.get("countries"))[:4],
            }
    return out


def work_fields(ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for chunk in batched(ids, 250):
        rows = sparql(f"""SELECT ?x (SAMPLE(?p) AS ?published) (SAMPLE(?pp) AS ?publishedPrec)
            (SAMPLE(?langL) AS ?language) (SAMPLE(?title) AS ?title)
            (GROUP_CONCAT(DISTINCT ?genreL; separator="{SEP}") AS ?genres)
          WHERE {{ VALUES ?x {{ {values(chunk)} }}
            OPTIONAL {{ ?x p:P577 ?ps . ?ps a wikibase:BestRank ; psv:P577 [ wikibase:timeValue ?p ; wikibase:timePrecision ?pp ] }}
            OPTIONAL {{ ?x wdt:P407 ?lang . ?lang rdfs:label ?langL FILTER(LANG(?langL)="en") }}
            OPTIONAL {{ ?x wdt:P1476 ?title }}
            OPTIONAL {{ ?x wdt:P136 ?genre . ?genre rdfs:label ?genreL FILTER(LANG(?genreL)="en") }}
          }} GROUP BY ?x""")
        for r in rows:
            out[qid(r["x"])] = {
                "start": _date(r.get("published"), r.get("publishedPrec")),
                "language": r.get("language"),
                "title": r.get("title"),
                "genres": split_multi(r.get("genres"))[:3],
            }
    return out


def relation_pairs(ids: list[str], prop: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for chunk in batched(ids, 200):
        for r in sparql(f"SELECT ?x ?y WHERE {{ VALUES ?x {{ {values(chunk)} }} ?x wdt:{prop} ?y . }}"):
            pair = (qid(r["x"]), qid(r["y"]))
            if pair not in seen:
                seen.add(pair)
                pairs.append(pair)
    return pairs


def _date(value: str | None, prec: str | None) -> dict | None:
    if not value:
        return None
    y = year_of(value)
    if y is None:
        return None
    p = int(prec) if prec else 9
    return {"value": value, "year": y, "precision": p, "label": date_label(value, p)}


# ----------------------------------------------------------------------------------------------- the run

def collect(case: Path, *, rules: dict | None = None, rid: str | None = None, echo=print) -> Path:
    P = case_paths(case)
    rules = rules or (json.loads(P["rules"].read_text(encoding="utf-8")) if P["rules"].exists() else DEFAULT_RULES)
    rid = rid or run_id("collect-")
    folder = P["runs"] / rid
    folder.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    notes: list[str] = []

    echo("people: seed …")
    people = seed_people()
    n_seed = len(people)
    echo(f"  {n_seed} with an SEP or IEP entry")
    exp = expand_people(list(people), int(rules["people"]["expand"]["min_sitelinks"]))
    for q, rule in exp.items():
        people.setdefault(q, rule)
    echo(f"  +{len(people) - n_seed} one hop away with ≥{rules['people']['expand']['min_sitelinks']} sitelinks")

    echo("works …")
    works = works_of(list(people), int(rules["works"]["authored"]["min_sitelinks"]))
    echo(f"  {len(works)}")

    echo("events and periods …")
    events = events_by_class(rules["events"]["classes"], "event")
    periods = events_by_class(rules["events"]["periods"], "period")
    linked = events_linked(list(people), rules["events"]["linked"])
    for q, rule in linked.items():
        if q not in events and q not in periods:
            events[q] = rule
    echo(f"  {len(events)} events, {len(periods)} periods (before the date filter)")

    echo("concepts and movements …")
    concepts = seed_concepts()
    for q, rule in movements_of(list(people)).items():
        concepts.setdefault(q, rule)
    echo(f"  {len(concepts)}")

    # A Wikidata item can match more than one rule; the first type below wins and the others are dropped
    # from the later sets so an id appears once.
    typed: dict[str, tuple[str, str]] = {}
    for kind, items in (("person", people), ("work", works), ("period", periods), ("event", events), ("concept", concepts)):
        for q, rule in items.items():
            typed.setdefault(q, (kind, rule))
    ids = list(typed)
    echo(f"fields for {len(ids)} items …")
    common = common_fields(ids)
    ext = external_ids(ids)
    by_kind: dict[str, list[str]] = {}
    for q, (kind, _) in typed.items():
        by_kind.setdefault(kind, []).append(q)
    pf = person_fields(by_kind.get("person", []))
    wf = work_fields(by_kind.get("work", []))
    sf = span_fields(by_kind.get("event", []) + by_kind.get("period", []) + by_kind.get("concept", []))

    lo, hi = rules["events"]["year_range"]
    nodes: dict[str, dict] = {}
    dropped = Counter()
    for q, (kind, rule) in typed.items():
        base = common.get(q)
        if not base:
            dropped[f"{kind}:no-fields"] += 1
            continue
        node = {"id": q, "type": kind, "rule": rule, **base, "ids": ext.get(q, {})}
        if kind == "person":
            node.update(pf.get(q, {}))
        elif kind == "work":
            node.update(wf.get(q, {}))
        else:
            node.update(sf.get(q, {}))
        if kind in ("event", "period"):
            y = (node.get("start") or {}).get("year")
            if y is None:
                y = (node.get("end") or {}).get("year")
            if y is None:
                dropped[f"{kind}:no-date"] += 1
                continue
            if not (lo <= y <= hi):
                dropped[f"{kind}:outside-range"] += 1
                continue
        if kind == "period" and not node.get("start"):
            dropped["period:no-start"] += 1
            continue
        nodes[q] = node
    for k, v in sorted(dropped.items()):
        notes.append(f"dropped {v} {k}")
        echo(f"  dropped {v} {k}")

    echo("edges …")
    edges: list[dict] = []
    seen: set[str] = set()
    for prop, etype in rules["edges"].items():
        if not etype or prop.endswith("^"):
            continue
        for x, y in relation_pairs(list(nodes), prop):
            if y in nodes and x != y:
                eid = f"{etype}:{x}:{y}"
                if eid not in seen:
                    seen.add(eid)
                    edges.append({"id": eid, "type": etype, "src": x, "dst": y, "source": f"wikidata:{prop}", "status": "recorded"})
    # P800 says "notable work" from the person's side; keep the author's edge so the work side is uniform.
    for e in list(edges):
        if e["type"] == "notable_work":
            eid = f"author:{e['dst']}:{e['src']}"
            if eid not in seen:
                seen.add(eid)
                edges.append({"id": eid, "type": "author", "src": e["dst"], "dst": e["src"], "source": "wikidata:P800 (inverted)", "status": "recorded"})
    echo(f"  {len(edges)} edges among {len(nodes)} nodes")

    (folder / "nodes.json").write_text(json.dumps(list(nodes.values()), ensure_ascii=False, indent=1), encoding="utf-8")
    (folder / "edges.json").write_text(json.dumps(edges, ensure_ascii=False, indent=1), encoding="utf-8")
    (folder / "rules.json").write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
    if not P["rules"].exists():
        P["rules"].parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(folder / "rules.json", P["rules"])
    counts = Counter(n["type"] for n in nodes.values())
    rule_counts = Counter(n["rule"] for n in nodes.values())
    edge_counts = Counter(e["type"] for e in edges)
    summary = {"nodes": dict(counts), "rules": dict(rule_counts), "edges": dict(edge_counts), "dropped": dict(dropped)}
    (folder / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    RunManifest(run_id=rid, step="timeline.collect", params={"rules": rel(P["rules"])}, inputs=["https://query.wikidata.org/sparql"],
                outputs=[rel(folder / "nodes.json"), rel(folder / "edges.json")], seconds=round(time.time() - t0, 1),
                notes=notes + [f"{k}: {v}" for k, v in counts.items()]).write(folder)
    echo(f"run {rid}: {dict(counts)} in {time.time() - t0:.0f}s")
    return folder


def latest_run(case: Path, prefix: str) -> Path | None:
    P = case_paths(case)
    if not P["runs"].exists():
        return None
    runs = sorted(p for p in P["runs"].iterdir() if p.is_dir() and p.name.startswith(prefix) and (p / "run.json").exists())
    return runs[-1] if runs else None


def load_graph(run: Path) -> tuple[list[dict], list[dict]]:
    nodes = json.loads((run / "nodes.json").read_text(encoding="utf-8"))
    edges = json.loads((run / "edges.json").read_text(encoding="utf-8"))
    return nodes, edges
