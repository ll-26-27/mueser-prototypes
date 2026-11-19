"""The settled layer: the medoid reading's diplomatic lines, with the consensus spans remapped onto them and, once a
person has decided, the decisions applied.

``compare run`` works on normalised, flattened text (ſ→s, hyphenated line ends joined, line breaks gone), so its
spans are offsets into ``base_text``. The lines a person should read are the medoid's raw lines, which survive in
its run JSON. ``settle`` puts the two together: for each raw line it computes where its normalised form sits in
``base_text`` (``line_offsets``) and a per-character map from normalised to raw offsets (``norm_cum``), then cuts
every span into per-line pieces in raw coordinates. The ``diplomatic`` text of a line is never changed; decisions
produce ``settled`` beside it. A build is immutable: ``apply`` writes a new one.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import time
from pathlib import Path

from PIL import Image

from mueser.shared.runs import RunManifest, git_sha, rel
from mueser.text.evaluate import normalize

from . import case_paths
from .anchor import align_lines, seg_lines_from_reading
from .log import Event, latest_decisions
from .log import read as read_log

DASHES = "-‐‑‒–—"


def normalize_sha256() -> str:
    return hashlib.sha256(inspect.getsource(normalize).encode("utf-8")).hexdigest()


def norm_cum(line: str) -> list[int]:
    """cum[i] = length of normalize(line[:i+1]); raw char i covers normalised [cum[i-1], cum[i])."""
    return [len(normalize(line[: i + 1])) for i in range(len(line))]


def line_offsets(lines: list[str]) -> list[dict]:
    """Where each raw line's normalised text sits in normalize("\\n".join(lines)).

    Returns one dict per line: start, end (offsets in the base text), joined (its trailing hyphen was removed and
    the next line follows directly), ok (the expected text was found where it should be)."""
    base = normalize("\n".join(lines))
    out: list[dict] = []
    pos = 0
    for i, raw in enumerate(lines):
        n = normalize(raw)
        joined = False
        if i + 1 < len(lines) and raw and raw[-1] in DASHES and n.endswith("-"):
            n = n[:-1]
            joined = True
        if not n:
            out.append({"start": pos, "end": pos, "joined": joined, "ok": True})
            continue
        start = pos
        if base[start:start + len(n)] != n:
            if base[start:start + 1] == " " and base[start + 1:start + 1 + len(n)] == n:
                start += 1
            else:
                found = base.find(n, pos)
                if found < 0:
                    out.append({"start": pos, "end": pos, "joined": joined, "ok": False})
                    continue
                start = found
        end = start + len(n)
        out.append({"start": start, "end": end, "joined": joined, "ok": True})
        pos = end
    return out


def map_local(cum: list[int], n_start: int, n_end: int) -> tuple[int, int]:
    """Normalised offsets within one line -> raw offsets [start, end)."""
    if not cum:
        return 0, 0
    raw_start = next((i for i, c in enumerate(cum) if c > n_start), len(cum))
    if n_end <= n_start:
        return raw_start, raw_start
    raw_end = next((i for i, c in enumerate(cum) if c >= n_end), len(cum) - 1) + 1
    return raw_start, max(raw_end, raw_start)


def spans_to_lines(lines: list[str], spans: list[dict]) -> list[list[dict]]:
    """Cut each consensus span (normalised offsets) into per-line pieces in raw offsets."""
    offs = line_offsets(lines)
    cums = [norm_cum(l) for l in lines]
    per_line: list[list[dict]] = [[] for _ in lines]
    for sid, sp in enumerate(spans):
        s, e = sp["start"], sp["end"]
        pieces: list[tuple[int, int, int]] = []
        if s >= e:   # an insertion other readers have: pin it to the line it falls in
            for i, o in enumerate(offs):
                if o["ok"] and o["start"] <= s <= o["end"]:
                    rs, _ = map_local(cums[i], s - o["start"], s - o["start"])
                    pieces.append((i, rs, rs))
                    break
        else:
            for i, o in enumerate(offs):
                if not o["ok"] or o["end"] <= o["start"] or e <= o["start"] or s >= o["end"]:
                    continue
                ls, le = max(s, o["start"]) - o["start"], min(e, o["end"]) - o["start"]
                rs, re_ = map_local(cums[i], ls, le)
                raw = lines[i]
                if o["joined"] and le == o["end"] - o["start"]:
                    re_ = len(raw)          # the piece reaches the joined hyphen: show it with the hyphen
                while rs < re_ and raw[rs].isspace():
                    rs += 1
                while re_ > rs and raw[re_ - 1].isspace():
                    re_ -= 1
                pieces.append((i, rs, re_))
        for k, (i, rs, re_) in enumerate(pieces):
            per_line[i].append({"span_id": str(sid), "piece": k, "of": len(pieces), "start": rs, "end": re_,
                                "base": sp["base"], "alternatives": sp["alternatives"], "weight": sp.get("weight", 0),
                                "status": "open", "decision_event": None})
    for pl in per_line:
        pl.sort(key=lambda p: (p["start"], p["end"]))
    return per_line


def find_image(pages_dir: Path, pid: str) -> Path | None:
    for ext in (".jpg", ".jpeg", ".png", ".tif", ".tiff"):
        p = pages_dir / f"{pid}{ext}"
        if p.exists():
            return p
    return None


def doc_for(meta: dict, pid: str) -> str | None:
    for doc_id, doc in (meta.get("docs") or {}).items():
        if pid in (doc.get("pages") or {}):
            return doc_id
    return None


def build_settled(case: Path, *, pages: list[str] | None = None, build_id: str | None = None,
                  max_dist: float = 0.55, anchor: bool = True) -> Path:
    """Write ``outputs/reading/builds/<build_id>/`` with settled.json, transcription/<page>.txt and run.json."""
    P = case_paths(case)
    meta = json.loads(P["metadata"].read_text(encoding="utf-8")) if P["metadata"].exists() else {"docs": {}}
    build_id = build_id or time.strftime("b-%Y%m%d-%H%M%S")
    out = P["builds"] / build_id
    if out.exists():
        raise FileExistsError(f"build {build_id} exists; builds are immutable, choose another id")
    t0 = time.time()
    settled: dict = {"build_id": build_id, "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "parent_build": None,
                     "normalize_sha256": normalize_sha256(), "git": git_sha(), "pages": {}, "decisions_applied": []}
    notes: list[str] = []
    inputs: list[str] = []
    for cf in sorted(P["consensus"].glob("*.consensus.json")):
        c = json.loads(cf.read_text(encoding="utf-8"))
        pid = c["page_id"]
        if pages and pid not in pages:
            continue
        pg = c["page"]
        med_path = P["medoid"] / f"{pid}.json"
        med = json.loads(med_path.read_text(encoding="utf-8"))
        inputs += [rel(cf), rel(med_path)]
        lines_raw = [l["text"] for l in med["lines"]]
        base_ok = normalize("\n".join(lines_raw)) == pg["base_text"]
        if not base_ok:
            notes.append(f"{pid}: medoid run text does not normalise to the consensus base_text; spans located by search")
        per_line = spans_to_lines(lines_raw, pg["spans"])
        image = find_image(P["pages"], pid)
        if image is None:
            raise FileNotFoundError(f"no page image for {pid} in {P['pages']}")
        W, H = Image.open(image).size
        lines = [{"line_id": f"l{i + 1}", "diplomatic": t, "settled": t, "anchor": None, "spans": per_line[i]}
                 for i, t in enumerate(lines_raw)]
        anchors_summary = None
        seg_path = P["segmentation"] / f"{pid}.json"
        if anchor and seg_path.exists():
            seg_reading = json.loads(seg_path.read_text(encoding="utf-8"))
            seg = seg_lines_from_reading(seg_reading)
            anchors, anchors_summary = align_lines(lines_raw, seg, max_dist=max_dist)
            for ln, a in zip(lines, anchors):
                ln["anchor"] = a.to_dict()
            anchors_summary["segmentation"] = {"reader": f"{seg_reading.get('backend')}:{seg_reading.get('model')}",
                                               "path": rel(seg_path), "polygons": len(seg)}
            inputs.append(rel(seg_path))
        elif anchor:
            notes.append(f"{pid}: no segmentation reading in inputs/readings/segmentation; lines are unanchored")
        settled["pages"][pid] = {
            "doc_id": doc_for(meta, pid) or pid,
            "image": str(image.relative_to(P["case"])), "width": W, "height": H,
            "consensus": {"run_id": c["run_id"], "min_weight": c["min_weight"], "agreement": pg["agreement"],
                          "readers": [r["key"] for r in pg["readers"]], "spans": len(pg["spans"]),
                          "check_in": pg.get("check_in"), "base_text_matches_medoid": base_ok,
                          "medoid_cer_norm": pg.get("medoid_cer_norm")},
            "diplomatic": {"reader": pg["medoid"]["overall"], "backend": med.get("backend"), "model": med.get("model"),
                           "run_id": c["run_id"], "path": rel(med_path), "prompt_sha256": med.get("prompt_sha256"),
                           "cost_usd": med.get("cost_usd")},
            "lines": lines,
            "anchors": anchors_summary,
            "translation": None,
        }
    if not settled["pages"]:
        raise RuntimeError(f"no pages settled from {P['consensus']}")
    write_build(out, settled)
    RunManifest(run_id=build_id, step="reading.settle", params={"max_dist": max_dist, "anchor": anchor, "pages": pages},
                inputs=inputs, outputs=[rel(out / "settled.json")], seconds=round(time.time() - t0, 2), notes=notes).write(out)
    return out


def write_build(out: Path, settled: dict) -> None:
    out.mkdir(parents=True, exist_ok=False)
    (out / "settled.json").write_text(json.dumps(settled, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "transcription").mkdir()
    for pid, pg in settled["pages"].items():
        (out / "transcription" / f"{pid}.txt").write_text("\n".join(l["settled"] for l in pg["lines"]) + "\n", encoding="utf-8")
    if any(pg.get("translation") for pg in settled["pages"].values()):
        (out / "translation").mkdir(exist_ok=True)
        for pid, pg in settled["pages"].items():
            tr = pg.get("translation")
            if tr and tr.get("settled"):
                (out / "translation" / f"{pid}.txt").write_text("\n".join(tr["settled"]) + "\n", encoding="utf-8")


def load_build(case: Path, build_id: str | None = None) -> tuple[Path, dict]:
    P = case_paths(case)
    if build_id is None:
        builds = sorted(p for p in P["builds"].glob("b-*") if (p / "settled.json").exists())
        if not builds:
            raise FileNotFoundError(f"no builds under {P['builds']}; run settle first")
        folder = builds[-1]
    else:
        folder = P["builds"] / build_id
    return folder, json.loads((folder / "settled.json").read_text(encoding="utf-8"))


def apply_edits(text: str, edits: list[tuple[int, int, str]]) -> str:
    for s, e, rep in sorted(edits, key=lambda t: t[0], reverse=True):
        text = text[:s] + rep + text[e:]
    return text


def apply_decisions(settled: dict, events: list[Event], translation: dict | None = None) -> tuple[dict, list[dict]]:
    """Return a new settled dict with the latest decision per target applied, and the list of what was applied.

    ``translation`` is the blocks file of a translation run ({page_id: blocks.json dict}); block decisions and the
    default (model A) produce the settled translation lines."""
    dec = latest_decisions(events)
    new = json.loads(json.dumps(settled))
    applied: list[dict] = []
    for pid, pg in new["pages"].items():
        for ln in pg["lines"]:
            text = ln["diplomatic"]
            line_target = f"line:{pid}:{ln['line_id']}"
            if line_target in dec:
                ev = dec[line_target]
                text = ev.body.get("text", text)
                for sp in ln["spans"]:
                    sp["status"], sp["decision_event"] = "decided", ev.id
                applied.append({"target": line_target, "event": ev.id, "who": ev.who, "ts": ev.ts})
                ln["settled"] = text
                continue
            edits: list[tuple[int, int, str]] = []
            for sp in ln["spans"]:
                t = f"span:{pid}:{sp['span_id']}"
                if t not in dec:
                    continue
                ev = dec[t]
                choice = ev.body.get("choice", "keep")
                rep: str | None
                if choice == "keep":
                    rep = None
                elif choice == "alt":
                    rep = sp["alternatives"].get(ev.body.get("reader") or "", None)
                    if rep is None:
                        rep = ev.body.get("text", "")
                else:
                    rep = ev.body.get("text", "")
                if rep is not None and sp["piece"] > 0:
                    rep = ""        # a span across a line break: the decision text lands on its first piece
                sp["status"], sp["decision_event"] = "decided", ev.id
                sp["decision"] = {"choice": choice, "text": rep, "reader": ev.body.get("reader"), "who": ev.who, "ts": ev.ts}
                if rep is not None:
                    edits.append((sp["start"], sp["end"], rep))
                if sp["piece"] == 0:
                    applied.append({"target": t, "event": ev.id, "who": ev.who, "ts": ev.ts})
            ln["settled"] = apply_edits(text, edits)
        if translation and pid in translation:
            blocks = translation[pid]
            out_lines: list[str] = []
            resolved = []
            for b in blocks["blocks"]:
                t = f"block:{pid}:{b['block_id']}"
                choice, txt = "a", (b.get("a") or {}).get("text", "")
                if t in dec:
                    ev = dec[t]
                    choice = ev.body.get("choice", "a")
                    if choice == "b":
                        txt = (b.get("b") or {}).get("text", "")
                    elif choice == "custom":
                        txt = ev.body.get("text", "")
                    applied.append({"target": t, "event": ev.id, "who": ev.who, "ts": ev.ts})
                    resolved.append({"block_id": b["block_id"], "choice": choice, "event": ev.id})
                out_lines.append(txt)
            pg["translation"] = {"run_id": blocks.get("run_id"), "models": blocks.get("models"), "settled": out_lines,
                                 "resolved": resolved, "stale": blocks.get("layer_sha256") != layer_sha256(pg)}
    new["decisions_applied"] = applied
    return new, applied


def layer_sha256(pg: dict) -> str:
    return hashlib.sha256("\n".join(l["settled"] for l in pg["lines"]).encode("utf-8")).hexdigest()


def apply_build(case: Path, *, build_id: str | None = None, translation_run: str | None = None,
                new_build_id: str | None = None) -> Path:
    """Read the log, apply the latest decisions to a build, write a new build."""
    P = case_paths(case)
    src, settled = load_build(case, build_id)
    events = read_log(P["log"])
    translation = None
    if translation_run:
        translation = {}
        for bf in sorted((P["runs"] / translation_run / "translation").glob("*.blocks.json")):
            d = json.loads(bf.read_text(encoding="utf-8"))
            translation[d["page_id"]] = d
    new, applied = apply_decisions(settled, events, translation)
    new_id = new_build_id or time.strftime("b-%Y%m%d-%H%M%S")
    if new_id == settled["build_id"]:
        new_id = new_id + "-1"
    new["build_id"] = new_id
    new["parent_build"] = settled["build_id"]
    new["created"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    new["translation_run"] = translation_run
    out = P["builds"] / new_id
    write_build(out, new)
    RunManifest(run_id=new_id, step="reading.apply",
                params={"parent_build": settled["build_id"], "translation_run": translation_run, "events_read": len(events)},
                inputs=[rel(src / "settled.json"), rel(P["log"])], outputs=[rel(out / "settled.json")],
                notes=[f"{len(applied)} decisions applied"]).write(out)
    return out
