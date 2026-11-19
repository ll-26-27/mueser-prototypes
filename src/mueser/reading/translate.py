"""Translate the settled lines of a page into English, sentence by sentence, with each segment naming its lines.

Two models get the same numbered lines and the same prompt, so their replies differ only by model. Each reply is
verified against the lines it names (``first_words`` must occur in the first line, ``last_words`` in the last),
corrected to a neighbouring line when it can be, and flagged when it cannot. The two models' segments are then
aligned into blocks whose line ranges coincide; a block whose two translations are far apart (normalised distance
at or above ``min_divergence``) is on the translation check-in list.

Every call goes through ``shared.openrouter.chat``: the raw reply is cached, the cost logged. A translation
records the sha256 of the page's settled text it was made from; a later build whose text differs marks it stale.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

from mueser.shared.openrouter import JSONReplyError, MissingCredential, chat
from mueser.shared.runs import RunManifest, rel
from mueser.text.compare import Reading, disagreements, dist
from mueser.text.evaluate import normalize

from . import case_paths
from .settle import load_build

PROMPT_PATH = Path(__file__).resolve().parents[1] / "text" / "backends" / "prompts" / "translate_de_en.md"
DEFAULT_MODELS = ["google/gemini-3.8-flash", "anthropic/claude-sonnet-5.5"]

SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["segments", "notes"],
    "properties": {
        "segments": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["line_start", "line_end", "first_words", "last_words", "translation", "note"],
            "properties": {"line_start": {"type": "string"}, "line_end": {"type": "string"},
                           "first_words": {"type": "string"}, "last_words": {"type": "string"},
                           "translation": {"type": "string"}, "note": {"type": "string"}}}},
        "notes": {"type": "string"},
    },
}


def load_prompt() -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    m = re.search(r"<!-- PROMPT START -->\s*(.*?)\s*<!-- PROMPT END -->", text, re.DOTALL)
    return (m.group(1) if m else text).strip()


def numbered(lines: list[dict]) -> str:
    return "\n".join(f"{l['line_id']}: {l['settled']}" for l in lines)


def layer_sha256(lines: list[dict]) -> str:
    return hashlib.sha256("\n".join(l["settled"] for l in lines).encode("utf-8")).hexdigest()


def slug(model: str) -> str:
    return model.replace("/", "_")


def _idx(line_ids: list[str], lid: str) -> int | None:
    try:
        return line_ids.index(lid)
    except ValueError:
        return None


def _squash(text: str) -> str:
    """normalise, then drop hyphens and spaces, so 'Aschen- puttel' and 'Aschen-\\nputtel' and 'Aschenputtel' agree."""
    return re.sub(r"[-\s]", "", normalize(text)).lower()


def _contains(line_text: str, words: str) -> bool:
    w = _squash(words)
    return bool(w) and w in _squash(line_text)


def _window(texts: list[str], i: int, forward: bool) -> str:
    """The line plus its neighbour in the reading direction, joined as the page joins them (so a trailing hyphen
    disappears and three words that straddle the line break still match)."""
    pair = texts[i:i + 2] if forward else texts[max(0, i - 1):i + 1]
    return "\n".join(pair)


def verify_segments(segments: list[dict], lines: list[dict]) -> tuple[list[dict], list[str]]:
    """Check each segment's line range against the lines it names; correct to a neighbour when possible.

    ``first_words`` must occur in the first line (or in it joined with the next: the three words may straddle a
    line break), ``last_words`` in the last line (or in it joined with the one before).
    verified: True (both anchors found where named), "corrected" (range moved to where the words are),
    False (words not found within two lines; kept and flagged). Also reports uncovered lines."""
    ids = [l["line_id"] for l in lines]
    text = {l["line_id"]: l["settled"] for l in lines}
    texts = [l["settled"] for l in lines]
    out: list[dict] = []
    for k, s in enumerate(segments):
        seg = dict(s)
        seg["segment_id"] = f"s{k + 1:02d}"
        a, b = _idx(ids, seg.get("line_start", "")), _idx(ids, seg.get("line_end", ""))
        status: object = True
        if a is None or b is None:
            status = False
        else:
            if b < a:
                a, b = b, a
                status = "corrected"
            first, last = seg.get("first_words", ""), seg.get("last_words", "")
            if not _contains(_window(texts, a, True), first):
                near = [i for i in range(max(0, a - 2), min(len(ids), a + 3)) if _contains(_window(texts, i, True), first)]
                if near:
                    a, status = min(near, key=lambda i: abs(i - a)), "corrected"
                else:
                    status = False
            if status is not False and not _contains(_window(texts, b, False), last):
                near = [i for i in range(max(0, b - 2), min(len(ids), b + 3)) if _contains(_window(texts, i, False), last)]
                if near:
                    b, status = min(near, key=lambda i: abs(i - b)), "corrected"
                else:
                    status = False
            if b < a:
                a, b = b, a
            seg["line_start"], seg["line_end"] = ids[a], ids[b]
        seg["verified"] = status
        seg["lines"] = ids[a:b + 1] if (a is not None and b is not None) else []
        out.append(seg)
    covered = {lid for s in out for lid in s["lines"]}
    uncovered = [lid for lid in ids if lid not in covered and text[lid].strip()]
    return out, uncovered


def translate_page(lines: list[dict], *, model: str, page_id: str, build_id: str) -> dict:
    """One model, one page. Returns the per-page translation record (segments verified) or an error record."""
    system = load_prompt()
    user = f"Page {page_id}. Lines:\n\n{numbered(lines)}"
    rec: dict = {"page_id": page_id, "model": model, "build_id": build_id, "layer_sha256": layer_sha256(lines),
                 "prompt_sha256": hashlib.sha256(system.encode("utf-8")).hexdigest(), "segments": [], "notes": "",
                 "uncovered": [], "cost_usd": 0.0, "cached": None, "cache_key": None, "error": None}
    try:
        r = chat(model=model, system=system, user_text=user, schema=SCHEMA, schema_name="translation",
                 temperature=0.0, max_tokens=6000, step="reading.translate")
    except MissingCredential as e:
        rec["error"] = f"skipped: {e}"
        return rec
    except JSONReplyError as e:
        rec["error"] = f"no JSON in reply: {e}"
        return rec
    rec.update({"cost_usd": r.get("cost_usd") or 0.0, "cached": r.get("cached"), "cache_key": r.get("key"),
                "model_reported": r.get("model"), "seconds": r.get("seconds")})
    parsed = r.get("parsed") or {}
    segs, uncovered = verify_segments(parsed.get("segments") or [], lines)
    rec["segments"], rec["uncovered"], rec["notes"] = segs, uncovered, parsed.get("notes", "")
    return rec


def align_segments(a: list[dict], b: list[dict] | None, line_ids: list[str]) -> list[dict]:
    """Group two models' segments into blocks whose line ranges coincide (greedy walk on the last line index)."""
    pos = {lid: i for i, lid in enumerate(line_ids)}

    def rng(s: dict) -> tuple[int, int]:
        ls = [pos[x] for x in s.get("lines", []) if x in pos]
        return (min(ls), max(ls)) if ls else (-1, -1)

    A = sorted([s for s in a if s.get("lines")], key=rng)
    if not b:
        return [{"block_id": f"b{k + 1:02d}", "lines": s["lines"], "a": {"segments": [s["segment_id"]], "text": s["translation"]},
                 "b": None, "dist": None, "divergent": False} for k, s in enumerate(A)]
    B = sorted([s for s in b if s.get("lines")], key=rng)
    blocks: list[dict] = []
    i = j = 0
    while i < len(A) or j < len(B):
        ga, gb = [], []
        if i < len(A):
            ga.append(A[i]); i += 1
        if j < len(B):
            gb.append(B[j]); j += 1
        while ga and gb:
            ea, eb = rng(ga[-1])[1], rng(gb[-1])[1]
            if ea == eb:
                break
            if ea < eb and i < len(A):
                ga.append(A[i]); i += 1
            elif eb < ea and j < len(B):
                gb.append(B[j]); j += 1
            else:
                break
        lo = min([rng(s)[0] for s in ga + gb]); hi = max([rng(s)[1] for s in ga + gb])
        ta = " ".join(s["translation"].strip() for s in ga); tb = " ".join(s["translation"].strip() for s in gb)
        blocks.append({"block_id": f"b{len(blocks) + 1:02d}", "lines": line_ids[lo:hi + 1],
                       "a": {"segments": [s["segment_id"] for s in ga], "text": ta} if ga else None,
                       "b": {"segments": [s["segment_id"] for s in gb], "text": tb} if gb else None,
                       "dist": (dist(ta, tb) if ga and gb else None), "divergent": False})
    return blocks


def mark_divergence(blocks: list[dict], min_divergence: float) -> None:
    for blk in blocks:
        if blk["dist"] is None:
            blk["divergent"] = blk["a"] is None or blk["b"] is None
            continue
        blk["divergent"] = blk["dist"] >= min_divergence
        if blk["divergent"]:
            spans = disagreements(Reading("a", "a", "a", "x", blk["a"]["text"]), [Reading("b", "b", "b", "x", blk["b"]["text"])])
            blk["diff"] = [{"start": s.start, "end": s.end, "base": s.base, "alt": s.alternatives.get("b", "")} for s in spans]


def run_translation(case: Path, *, build_id: str | None = None, models: list[str] | None = None,
                    min_divergence: float = 0.35, pages: list[str] | None = None, run_id: str | None = None) -> Path:
    P = case_paths(case)
    folder, settled = load_build(case, build_id)
    models = models or DEFAULT_MODELS
    run_id = run_id or time.strftime("%Y%m%d-%H%M%S")
    out = P["runs"] / run_id / "translation"
    out.mkdir(parents=True, exist_ok=False)
    t0 = time.time(); cost = 0.0; notes: list[str] = []; outputs: list[str] = []
    for pid, pg in settled["pages"].items():
        if pages and pid not in pages:
            continue
        lines = pg["lines"]
        recs: dict[str, dict] = {}
        for m in models:
            rec = translate_page(lines, model=m, page_id=pid, build_id=settled["build_id"])
            (out / slug(m)).mkdir(exist_ok=True)
            p = out / slug(m) / f"{pid}.json"
            p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            outputs.append(rel(p))
            cost += rec.get("cost_usd") or 0.0
            if rec.get("error"):
                notes.append(f"{pid} {m}: {rec['error']}")
            else:
                recs[m] = rec
                bad = sum(1 for s in rec["segments"] if s["verified"] is False)
                corr = sum(1 for s in rec["segments"] if s["verified"] == "corrected")
                print(f"{pid:42} {m:34} segments={len(rec['segments'])} corrected={corr} unverified={bad} uncovered={len(rec['uncovered'])} ${rec.get('cost_usd') or 0:.4f}{' cached' if rec.get('cached') else ''}")
        ok = [m for m in models if m in recs]
        if not ok:
            continue
        a = recs[ok[0]]["segments"]; b = recs[ok[1]]["segments"] if len(ok) > 1 else None
        blocks = align_segments(a, b, [l["line_id"] for l in lines])
        mark_divergence(blocks, min_divergence)
        bf = out / f"{pid}.blocks.json"
        bf.write_text(json.dumps({"page_id": pid, "run_id": run_id, "build_id": settled["build_id"], "layer_sha256": layer_sha256(lines),
                                  "models": ok, "min_divergence": min_divergence, "blocks": blocks,
                                  "segments": {m: recs[m]["segments"] for m in ok}, "uncovered": {m: recs[m]["uncovered"] for m in ok},
                                  "notes": {m: recs[m]["notes"] for m in ok}}, ensure_ascii=False, indent=1), encoding="utf-8")
        outputs.append(rel(bf))
        print(f"{pid:42} blocks={len(blocks)} divergent={sum(1 for x in blocks if x['divergent'])}")
    RunManifest(run_id=run_id, step="reading.translate",
                params={"build_id": settled["build_id"], "models": models, "min_divergence": min_divergence, "pages": pages,
                        "prompt_sha256": hashlib.sha256(load_prompt().encode("utf-8")).hexdigest(), "prompt": rel(PROMPT_PATH)},
                inputs=[rel(folder / "settled.json")], outputs=outputs, cost_usd=round(cost, 6),
                seconds=round(time.time() - t0, 2), notes=notes).write(out.parent)
    return out.parent


def latest_translation_run(case: Path) -> Path | None:
    P = case_paths(case)
    runs = sorted(p for p in P["runs"].glob("*") if (p / "translation").is_dir())
    return runs[-1] if runs else None
