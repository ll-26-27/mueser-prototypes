"""Proposed connections between thinkers and events, from a model, verified against the text it was given.

Wikidata records who influenced whom and who wrote what, but it rarely says which wars, revolutions or
settlements a thinker lived through, answered in writing, took part in or suffered under. This step asks a
model exactly that, one person at a time, with only two things in front of it: the person's Wikipedia extract
(the same text the page shows) and the list of events in the node set whose dates overlap the person's life.
It must pick from that list and, for each pick, quote the sentence of the extract that supports it. The quote
is checked verbatim here: a proposal whose evidence is not in the extract is kept, marked ``unverified``, and
shown as such. Every proposal has status ``proposed`` until a person accepts or rejects it in the page.

Types, chosen from a closed list (the model may not invent one):

- ``lived_through``        the event fell within the person's life and the extract mentions it
- ``took_part_in``         the person acted in it (fought, sat in the assembly, signed, negotiated)
- ``wrote_in_response_to`` a named work or body of writing answers the event
- ``suffered_under``       exile, imprisonment, censorship, dismissal or death because of it
- ``shaped_by``            the extract says the event formed the person's thought without naming a work
"""

from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from mueser.shared.cache import sha256_text
from mueser.shared.openrouter import MissingCredential, chat
from mueser.shared.runs import RunManifest, rel

from . import case_paths

DEFAULT_MODEL = "google/gemini-3.8-flash"
TYPES = ["lived_through", "took_part_in", "wrote_in_response_to", "suffered_under", "shaped_by"]
PROMPT_PATH = Path(__file__).resolve().parents[1] / "text" / "backends" / "prompts" / "timeline_connect.md"

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "connections": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "event": {"type": "string", "description": "the event's id from the list, e.g. Q12345"},
                    "type": {"type": "string", "enum": TYPES},
                    "reason": {"type": "string", "description": "one sentence, in your words"},
                    "evidence": {"type": "string", "description": "the sentence of the extract that supports it, copied exactly"},
                    "work": {"type": "string", "description": "the work's title if the type is wrote_in_response_to, else empty"},
                },
                "required": ["event", "type", "reason", "evidence", "work"],
            },
        }
    },
    "required": ["connections"],
}


def load_prompt() -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    m = re.search(r"<!-- PROMPT START -->(.*)<!-- PROMPT END -->", text, re.DOTALL)
    return (m.group(1) if m else text).strip()


def _squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def candidates(person: dict, events: list[dict], *, margin: int = 0) -> list[dict]:
    b = (person.get("start") or {}).get("year")
    d = (person.get("end") or {}).get("year")
    if b is None:
        return []
    d = d if d is not None else b + 80
    out = []
    for e in events:
        s = (e.get("start") or {}).get("year")
        t = (e.get("end") or {}).get("year", s)
        if s is None:
            continue
        t = t if t is not None else s
        if s <= d + margin and t >= b - margin:
            out.append(e)
    return out


def user_text(person: dict, extract: str, cands: list[dict]) -> str:
    def span(e):
        s = (e.get("start") or {}).get("year")
        t = (e.get("end") or {}).get("year")
        return f"{s}" if t in (None, s) else f"{s}–{t}"
    lines = [f"{e['id']}  {e['label']} ({span(e)})" + (f" — {e['description']}" if e.get("description") else "") for e in cands]
    life = f"{(person.get('start') or {}).get('label', '?')}–{(person.get('end') or {}).get('label', '?')}"
    return (f"PERSON: {person['label']} ({life}). {person.get('description', '')}\n\n"
            f"EXTRACT:\n{extract}\n\nEVENTS (id, name, years):\n" + "\n".join(lines))


def verify(proposal: dict, extract: str, cand_ids: set[str]) -> dict:
    p = dict(proposal)
    p["in_list"] = p.get("event") in cand_ids
    ev = p.get("evidence") or ""
    p["verified"] = bool(ev) and _squash(ev) in _squash(extract)
    p["status"] = "proposed"
    return p


def connect_person(person: dict, extract: str, cands: list[dict], *, model: str, system: str) -> dict:
    text = user_text(person, extract, cands)
    reply = chat(model=model, system=system, user_text=text, schema=SCHEMA, schema_name="connections",
                 step="timeline.connect", max_tokens=8000)
    parsed = reply.get("parsed") or {"connections": []}
    cand_ids = {c["id"] for c in cands}
    props = [verify(p, extract, cand_ids) for p in parsed.get("connections", [])]
    return {"person": person["id"], "model": reply.get("model", model), "cached": reply.get("cached", False),
            "cost_usd": reply.get("cost_usd", 0.0), "proposals": props, "cache_key": reply.get("key")}


def run_connect(case: Path, run: Path, *, model: str = DEFAULT_MODEL, only_seed: bool = True, limit: int | None = None,
                workers: int = 6, rid: str | None = None, echo=print) -> Path | None:
    from .collect import load_graph
    from .sources import load_sources
    P = case_paths(case)
    nodes, _ = load_graph(run)
    _, wp = load_sources(case)
    summaries = wp.get("summaries", {})
    events = [n for n in nodes if n["type"] in ("event", "period")]
    people = [n for n in nodes if n["type"] == "person" and (not only_seed or n["rule"].startswith("seed:"))]
    people = [p for p in people if p["id"] in summaries and p.get("start")]
    if limit:
        people = people[:limit]
    system = load_prompt()
    rid = rid or f"connect-{time.strftime('%Y%m%d-%H%M%S')}"
    folder = P["proposals"] / rid
    folder.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    echo(f"{len(people)} people, {len(events)} events, model {model}")

    def one(person):
        cands = candidates(person, events)
        if not cands:
            return {"person": person["id"], "proposals": [], "skipped": "no overlapping events"}
        try:
            return connect_person(person, summaries[person["id"]]["extract"], cands, model=model, system=system)
        except MissingCredential:
            raise
        except Exception as e:  # noqa: BLE001
            return {"person": person["id"], "proposals": [], "error": str(e)[:300]}

    results: list[dict] = []
    try:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for i, r in enumerate(ex.map(one, people)):
                results.append(r)
                if (i + 1) % 50 == 0:
                    echo(f"  {i + 1}/{len(people)}")
    except MissingCredential as e:
        echo(f"skipped: {e}")
        return None
    cost = sum(r.get("cost_usd", 0.0) for r in results)
    n_props = sum(len(r["proposals"]) for r in results)
    n_ver = sum(1 for r in results for p in r["proposals"] if p["verified"])
    n_list = sum(1 for r in results for p in r["proposals"] if p["in_list"])
    errors = sum(1 for r in results if r.get("error"))
    (folder / "proposals.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    RunManifest(run_id=rid, step="timeline.connect",
                params={"model": model, "only_seed": only_seed, "prompt_sha256": sha256_text(system), "workers": workers,
                        "collect_run": run.name, "types": TYPES},
                inputs=[rel(run / "nodes.json"), rel(P["sources"] / "wikipedia.json"), rel(PROMPT_PATH)],
                outputs=[rel(folder / "proposals.json")], cost_usd=round(cost, 4), seconds=round(time.time() - t0, 1),
                notes=[f"{len(people)} people asked", f"{n_props} proposals, {n_ver} with evidence found verbatim in the extract, "
                       f"{n_props - n_list} naming an event outside the list", f"{errors} errors"]).write(folder)
    echo(f"{n_props} proposals ({n_ver} verified) for {len(people)} people, ${cost:.3f}, {time.time() - t0:.0f}s")
    return folder


def latest_proposals(case: Path) -> Path | None:
    P = case_paths(case)
    if not P["proposals"].exists():
        return None
    runs = sorted(p for p in P["proposals"].iterdir() if p.is_dir() and (p / "proposals.json").exists())
    return runs[-1] if runs else None
