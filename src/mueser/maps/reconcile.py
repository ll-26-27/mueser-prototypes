"""Turn gazetteer candidates into a decision you can audit.

For each distinct place name: ask the resolvers in priority order (GOV, Wikidata, WHG, GeoNames), keep EVERY
candidate in a review table, and accept one automatically only when (a) its score is at least ``accept_min``
and (b) it is ahead of the next-best candidate by at least ``margin``. Otherwise the name is ``unresolved`` and
all its candidates wait in ``review.csv`` for a person, who writes the chosen URI back (status ``reviewed``).

Nothing is silently placed. The threshold and margin are recorded in run.json.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from mueser.shared.record import Record
from .gazetteer import Candidate, resolvers

PRIORITY = {"gov": 0, "wikidata": 1, "whg": 2, "geonames": 3}

# Default lookup context for this project: the historical German-speaking world and its neighbours. Resolvers that
# can filter by country use it (WHG, GeoNames); the scoring bonus below rewards candidates inside it. Override with
# --ccodes on the command line.
DEFAULT_CONTEXT = {"ccodes": ["DE", "PL", "CZ", "AT", "CH", "FR", "RU", "LT", "LV", "EE", "DK", "NL", "BE", "LU", "IT", "SI", "HU", "SK", "UA", "BY", "RO", "HR"],
                   "bbox": [-5.0, 42.0, 40.0, 60.0]}   # lon_min, lat_min, lon_max, lat_max


def in_bbox(c: Candidate, bbox: list[float] | None) -> bool:
    if not bbox or c.lat is None or c.lon is None:
        return True
    return bbox[0] <= c.lon <= bbox[2] and bbox[1] <= c.lat <= bbox[3]


@dataclass
class Decision:
    name: str
    status: str                      # auto | unresolved | reviewed
    chosen: Optional[Candidate]
    candidates: list[Candidate]
    reason: str


def _rank_key(c: Candidate) -> tuple:
    has_coords = c.lat is not None and c.lon is not None
    return (-(c.score if has_coords else 0), PRIORITY.get(c.source, 9), c.label)


def decide(name: str, cands: list[Candidate], *, accept_min: float = 0.9, margin: float = 0.15,
           manual: dict[str, str] | None = None, context: dict | None = None, populous_tiebreak: bool = True) -> Decision:
    manual = manual or {}
    bbox = (context or DEFAULT_CONTEXT).get("bbox")
    for c in cands:
        if not in_bbox(c, bbox) and c.score > 0:
            c.score = round(c.score - 0.3, 3)
            c.note = (c.note + "; " if c.note else "") + "outside the project's region: score lowered by 0.3"
    if name in manual:
        uri = manual[name]
        chosen = next((c for c in cands if c.uri == uri), None)
        return Decision(name, "reviewed", chosen, cands, f"manual choice from review.csv: {uri}")
    usable = [c for c in cands if c.lat is not None and c.lon is not None and c.uri]
    if not usable:
        return Decision(name, "unresolved", None, cands, "no candidate with coordinates")
    ranked = sorted(usable, key=_rank_key)
    best = ranked[0]
    second_score = max((c.score for c in ranked[1:] if c.uri != best.uri), default=0.0)
    if best.score >= accept_min and best.score - second_score >= margin:
        return Decision(name, "auto", best, cands, f"score {best.score:.2f} ≥ {accept_min} and margin {best.score - second_score:.2f} ≥ {margin}")
    if best.score >= accept_min:
        high = [c for c in ranked if c.score >= accept_min]
        # Same-score candidates from different sources that agree on location are not a conflict.
        agree = [c for c in high if abs(c.lat - best.lat) < 0.05 and abs(c.lon - best.lon) < 0.05]
        if len(agree) == len(high):
            return Decision(name, "auto", best, cands, f"{len(agree)} high-scoring candidates agree on location (within ~5 km)")
        # Several places share the name. Prefer the one that is far more populous, if the gazetteers say so, and say so.
        if populous_tiebreak:
            groups: dict[tuple[int, int], list[Candidate]] = {}
            for c in high:
                groups.setdefault((round(c.lat * 20), round(c.lon * 20)), []).append(c)
            pops = sorted(((max((x.population or 0) for x in g), g) for g in groups.values()), key=lambda t: -t[0])
            if len(pops) >= 2 and pops[0][0] >= 5000 and pops[0][0] >= 10 * pops[1][0]:
                winner = max(pops[0][1], key=lambda c: (PRIORITY.get(c.source, 9) == 0, c.score))
                return Decision(name, "auto", winner, cands,
                                f"{len(groups)} distinct places share the name; chose the most populous ({pops[0][0]:,} vs next {pops[1][0]:,}). Check if the source could mean a smaller place.")
    return Decision(name, "unresolved", None, cands, f"best {best.score:.2f} from {best.source}; next {second_score:.2f}; below threshold or margin")


def resolve_names(names: list[str], *, sources: list[str] | None = None, accept_min: float = 0.9, margin: float = 0.15,
                  manual: dict[str, str] | None = None, context: dict | None = None, populous_tiebreak: bool = True, log=print) -> dict[str, Decision]:
    context = context or DEFAULT_CONTEXT
    rs = resolvers(sources)
    active = []
    for r in rs:
        why = r.check()
        if why:
            log(f"skip resolver {r.name}: {why}")
        else:
            active.append(r)
    out: dict[str, Decision] = {}
    for i, name in enumerate(names, 1):
        cands: list[Candidate] = []
        for r in active:
            got = r.resolve(name, context)
            cands.extend(got)
        d = decide(name, cands, accept_min=accept_min, margin=margin, manual=manual, context=context, populous_tiebreak=populous_tiebreak)
        # A normalized name may carry a descriptor for the reader, "Katzbach (river)" or "Königsberg (Preußen)".
        # If the full string does not resolve, look the bare name up too, mark those candidates, and decide again.
        bare = re.sub(r"\s*\([^)]*\)", "", name).split(",")[0].strip()
        if d.status == "unresolved" and bare and bare != name:
            for r in active:
                for c in r.resolve(bare, context):
                    c.note = (c.note + "; " if c.note else "") + f"found with bare name {bare!r}"
                    cands.append(c)
            d2 = decide(name, cands, accept_min=accept_min, margin=margin, manual=manual, context=context, populous_tiebreak=populous_tiebreak)
            if d2.status != "unresolved":
                d2.reason = f"bare name {bare!r}: " + d2.reason
            d = d2
        out[name] = d
        log(f"[{i}/{len(names)}] {name!r}: {d.status} ({d.reason})" + (f" -> {d.chosen.label} [{d.chosen.source}]" if d.chosen else ""))
    return out


REVIEW_COLUMNS = ["name", "status", "reason", "chosen_uri", "candidate_rank", "source", "uri", "label", "score", "lat", "lon",
                  "feature_type", "admin", "population", "valid_from", "valid_to", "alt_names", "your_choice"]


def write_review(decisions: dict[str, Decision], path: Path) -> None:
    """One row per candidate, grouped by name. A person fills `your_choice` with the chosen URI (or 'none')."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REVIEW_COLUMNS)
        w.writeheader()
        for name, d in decisions.items():
            ranked = sorted(d.candidates, key=_rank_key)
            if not ranked:
                w.writerow({"name": name, "status": d.status, "reason": d.reason, "chosen_uri": "", "candidate_rank": 0})
            for i, c in enumerate(ranked, 1):
                w.writerow({"name": name, "status": d.status, "reason": d.reason, "chosen_uri": d.chosen.uri if d.chosen else "",
                            "candidate_rank": i, "source": c.source, "uri": c.uri, "label": c.label, "score": c.score, "lat": c.lat, "lon": c.lon,
                            "feature_type": c.feature_type or "", "admin": c.admin or "", "population": c.population if c.population is not None else "",
                            "valid_from": c.valid_from or "", "valid_to": c.valid_to or "",
                            "alt_names": "; ".join(c.alt_names[:8]), "your_choice": ""})


def read_manual_choices(path: Path) -> dict[str, str]:
    """Collect `your_choice` URIs from a review.csv a person has edited. 'none' means leave unresolved."""
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            v = (row.get("your_choice") or "").strip()
            if v:
                out[row["name"]] = v
    return out


def apply_to_records(records: list[Record], decisions: dict[str, Decision]) -> list[Record]:
    for r in records:
        if r.type != "place":
            continue
        key = r.normalized or r.surface_form
        d = decisions.get(key) or decisions.get(r.surface_form)
        if not d:
            continue
        if d.chosen and d.status in ("auto", "reviewed"):
            r.place_uri, r.lat, r.lon = d.chosen.uri, d.chosen.lat, d.chosen.lon
            r.resolution_status = d.status  # type: ignore[assignment]
            r.resolution_source = d.chosen.source
            r.confidence = d.chosen.score
        else:
            r.resolution_status = "unresolved"
            r.place_uri = r.lat = r.lon = None
        r.notes = (r.notes + " | " if r.notes else "") + f"reconcile: {d.reason}"
    return records


def decisions_to_json(decisions: dict[str, Decision]) -> dict:
    return {name: {"status": d.status, "reason": d.reason, "chosen": d.chosen.to_dict() if d.chosen else None,
                   "candidates": [c.to_dict() for c in sorted(d.candidates, key=_rank_key)]} for name, d in decisions.items()}


def save_decisions(decisions: dict[str, Decision], path: Path) -> None:
    path.write_text(json.dumps(decisions_to_json(decisions), indent=1, ensure_ascii=False), encoding="utf-8")
