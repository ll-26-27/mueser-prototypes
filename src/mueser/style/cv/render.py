"""cv render: a copy of the CV with the new entries from cv.yml, each a clone of a neighbouring entry.

Nothing but the new and the reworded entries changes. After writing, every other paragraph and table
row is compared with the source as canonical XML, and the run fails if one differs.
"""

from __future__ import annotations

import copy
import time
from pathlib import Path

import yaml

from mueser.shared.cache import sha256_file
from mueser.shared.runs import RunManifest, rel, run_id
from mueser.style.shared.docx import Docx, c14n, q, set_runs

from . import cells, unit_markup, unit_text, units


def _is_spacer(el) -> bool:
    return el is not None and el.tag == q("p") and not unit_text({"kind": "paragraph", "el": el}).strip() \
        and el.find(".//" + q("drawing")) is None and el.find(".//" + q("sectPr")) is None


def _fill(el, kind: str, markup: str) -> None:
    if kind == "paragraph":
        set_runs(el, markup)
        return
    tcs, parts = cells(el), markup.split("\t")
    if len(parts) != len(tcs):
        raise ValueError(f"this row has {len(tcs)} cells; the text has {len(parts)} tab-separated parts")
    for tc, part in zip(tcs, parts):
        ps = tc.findall(q("p"))
        for extra in ps[1:]:
            tc.remove(extra)
        set_runs(ps[0], part)


def render(cv_yml: Path, source: Path, out_root: Path, rid: str | None = None, echo=print) -> Path:
    t0 = time.time()
    data = yaml.safe_load(cv_yml.read_text(encoding="utf-8"))
    sha = sha256_file(source)
    if data["source"]["sha256"] != sha:
        raise SystemExit(f"{cv_yml.name} was extracted from a different file than {source.name} "
                         f"(sha256 {data['source']['sha256'][:12]} vs {sha[:12]}). Run `cv extract` on this file.")
    doc = Docx(source)
    us = units(doc)
    before = {u["index"]: c14n(u["el"]) for u in us}
    listed: set[int] = set()
    added, changed, refused = [], [], []
    tail: dict[int, object] = {}  # anchor unit -> the element after which the next new entry goes

    for section in data["sections"]:
        entries = section.get("entries") or []
        by_id = {e["id"]: e for s in data["sections"] for e in (s.get("entries") or []) if e.get("id")}
        prev = None
        for pos, e in enumerate(entries):
            if e.get("source_index") is not None:
                u = us[e["source_index"]]
                listed.add(u["index"])
                if e["text"] != unit_markup(u):
                    try:
                        _fill(u["el"], u["kind"], e["text"])
                        changed.append({"id": e["id"], "section": section["title"], "text": e["text"]})
                    except ValueError as err:
                        refused.append({"section": section["title"], "text": e["text"], "reason": str(err)})
                prev = u
                continue
            following = next((us[x["source_index"]] for x in entries[pos + 1:] if x.get("source_index") is not None), None)
            anchor = prev or following
            if anchor is None:
                refused.append({"section": section["title"], "text": e["text"],
                                "reason": "the section has no existing entry to copy the format from"})
                continue
            like = us[by_id[e["like"]]["source_index"]] if e.get("like") in by_id else anchor
            if e.get("like") and e["like"] not in by_id:
                refused.append({"section": section["title"], "text": e["text"], "reason": f"no entry with id {e['like']}"})
                continue
            if like["kind"] != anchor["kind"]:
                refused.append({"section": section["title"], "text": e["text"],
                                "reason": f"`like: {e['like']}` is a {like['kind']} but the neighbouring entry is a {anchor['kind']}"})
                continue
            new = copy.deepcopy(like["el"])
            try:
                _fill(new, like["kind"], e["text"])
            except ValueError as err:
                refused.append({"section": section["title"], "text": e["text"], "reason": str(err)})
                continue
            a = anchor["el"]
            if prev is not None:  # goes after the entry above; where a blank paragraph follows that entry, keep the rhythm
                spacer = a.getnext() if anchor["kind"] == "paragraph" and _is_spacer(a.getnext()) else None
                after = tail.get(anchor["index"], spacer if spacer is not None else a)
                after.addnext(new)
                if spacer is not None:
                    gap = copy.deepcopy(spacer)
                    new.addnext(gap)
                    tail[anchor["index"]] = gap
                else:
                    tail[anchor["index"]] = new
            else:  # first in its section: goes before the entry below
                a.addprevious(new)
                if anchor["kind"] == "paragraph" and _is_spacer(a.getnext()):
                    new.addnext(copy.deepcopy(a.getnext()))
            added.append({"section": section["title"], "text": e["text"], "copied_from": f"u{like['index']:03d}",
                          "placed": ("after" if prev is not None else "before") + f" u{anchor['index']:03d}"})

    changed_idx = {int(c["id"][1:]) for c in changed}
    altered = [i for i, x in before.items() if i not in changed_idx and c14n(us[i]["el"]) != x]
    if altered:
        raise SystemExit(f"internal check failed: units {altered} differ from the source but were not edited. Nothing written.")
    unlisted = [f"u{u['index']:03d}" for u in us if unit_text(u).strip() and u["index"] not in listed
                and not any(s.get("source_index") == u["index"] for s in data["sections"])]

    rid = rid or run_id("cv-")
    folder = out_root / rid
    if folder.exists():
        raise SystemExit(f"{folder} exists; a run folder is never overwritten")
    doc.touch()
    target = doc.save(folder / "cv.docx")
    lines = [f"source    {source.name}  sha256 {sha}", f"output    {target.name}  sha256 {sha256_file(target)}",
             f"added     {len(added)}", f"reworded  {len(changed)}", f"refused   {len(refused)}",
             f"unchanged {len(before) - len(changed)} paragraphs and rows, compared with the source as canonical XML: identical", ""]
    lines += [f"+ [{a['section']}] {a['text']!r}\n    format copied from {a['copied_from']}, placed {a['placed']}" for a in added]
    lines += [f"~ [{c['section']}] {c['id']} now reads {c['text']!r}" for c in changed]
    lines += [f"! REFUSED [{r['section']}] {r['text']!r}: {r['reason']}" for r in refused]
    if unlisted:
        lines.append(f"note: {', '.join(unlisted)} are in the document but no longer in cv.yml; they were left in place (nothing is ever deleted)")
    (folder / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    RunManifest(run_id=rid, step="style.cv.render", params={"added": len(added), "reworded": len(changed), "refused": len(refused),
                                                             "source_sha256": sha, "cv_yml_sha256": sha256_file(cv_yml)},
                inputs=[rel(source), rel(cv_yml)], outputs=[rel(target), rel(folder / "report.txt")],
                seconds=round(time.time() - t0, 2), notes=[r["reason"] for r in refused]).write(folder)
    echo("\n".join(lines))
    echo(f"wrote {target}")
    return target
