"""journal apply: write the accepted rows of review.csv into a copy of the draft, and prove nothing else moved.

For every paragraph the expected text is computed from the original text and the accepted edits; the
edited copy is read back and must match it exactly, paragraph for paragraph, or the run fails.
"""

from __future__ import annotations

import copy
import html
import json
import time
from pathlib import Path

from mueser.shared.cache import sha256_file
from mueser.shared.runs import RunManifest, rel, run_id
from mueser.style.shared.docx import FOOTNOTES, Docx, apply_edits, replace_span

from .check import paragraphs, read_review

PAGE = """<!doctype html><html lang="en"><meta charset="utf-8"><title>Applied changes</title>
<style>body{{font:15px/1.5 Georgia,serif;max-width:60rem;margin:2rem auto;padding:0 1rem;color:#222}}table{{border-collapse:collapse;width:100%}}
td,th{{border-top:1px solid #ccc;padding:.4rem .5rem;vertical-align:top;text-align:left}}del{{background:#fdd}}ins{{background:#dfd;text-decoration:none}}
small{{color:#666}}</style><h1>Applied changes</h1><p>{summary}</p><table><tr><th>where</th><th>before → after</th><th>rows</th></tr>{rows}</table></html>"""


def _marked(text: str, edits: list[tuple[int, int, str]]) -> str:
    out, pos = "", 0
    for s, e, new in sorted(edits):
        out += html.escape(text[pos:s]) + (f"<del>{html.escape(text[s:e])}</del>" if e > s else "") + (f"<ins>{html.escape(new)}</ins>" if new else "")
        pos = e
    return out + html.escape(text[pos:])


def apply(source: Path, run: Path, out_root: Path, rid: str | None = None, echo=print) -> Path:
    t0 = time.time()
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    sha = sha256_file(source)
    if manifest["params"]["article_sha256"] != sha:
        raise SystemExit(f"{source.name} is not the file this review was made from (sha256 differs). Run `journal check` on it.")
    accepted = [r for r in read_review(run / "review.csv") if r["status"] == "accepted" and r["edits"]]
    doc = Docx(source)
    paras = {p["key"]: p for p in paragraphs(doc)}
    before = {k: p["text"] for k, p in paras.items()}

    by_para: dict[str, list[tuple[dict, list]]] = {}
    for r in accepted:
        key = r["finding_id"].split("-", 1)[0]
        by_para.setdefault(key, []).append((r, [tuple(e) for e in json.loads(r["edits"])]))
    applied, refused, expected, shown = [], [], dict(before), []
    for key, items in by_para.items():
        taken: list[tuple[int, int, str]] = []
        ids = []
        # an accepted restyle of a whole note goes first: it already carries the small changes the rules propose there
        for r, edits in sorted(items, key=lambda x: (x[0]["rule"] != "citation-form", x[0]["finding_id"])):
            if any((s < b and a < e) or (s == e and a <= s <= b) or (a == b and s <= a <= e) for s, e, _ in edits for a, b, _ in taken):
                refused.append((r["finding_id"], "overlaps another accepted change in the same paragraph, which was applied instead"))
                continue
            taken += edits
            ids.append(r["finding_id"])
        el = paras[key]["el"]
        snapshot = (el.getparent(), el.getparent().index(el), copy.deepcopy(el))
        try:
            for s, e, new in sorted(taken, reverse=True):
                replace_span(el, s, e, new)
        except ValueError as err:
            parent, at, original = snapshot
            parent.remove(el)
            parent.insert(at, original)
            paras[key]["el"] = original
            refused += [(i, str(err)) for i in ids]
            continue
        expected[key] = apply_edits(before[key], taken)
        applied += ids
        where = f"note {paras[key]['note']}" if paras[key]["note"] else f"paragraph {paras[key]['para'] + 1}"
        shown.append(f"<tr><td>{where}</td><td>{_marked(before[key], taken)}</td><td><small>{'<br>'.join(ids)}</small></td></tr>")

    rid = rid or run_id("journal-apply-")
    folder = out_root / rid
    if folder.exists():
        raise SystemExit(f"{folder} exists; a run folder is never overwritten")
    doc.touch()
    if doc.footnotes is not None:
        doc.touch(FOOTNOTES)
    target = doc.save(folder / source.name)
    after = {p["key"]: p["text"] for p in paragraphs(Docx(target))}
    wrong = [k for k in expected if after.get(k) != expected[k]] + [k for k in after if k not in expected]
    if wrong:
        target.unlink()
        raise SystemExit(f"check failed: paragraphs {wrong[:10]} do not read as the accepted edits say they should. No copy was kept.")
    untouched = sum(1 for k in before if before[k] == after[k])
    summary = (f"{len(applied)} accepted rows applied to a copy of {html.escape(source.name)}; {len(refused)} refused. "
               f"{len(before) - untouched} paragraphs and notes changed, {untouched} read back identical to the source.")
    (folder / "diff.html").write_text(PAGE.format(summary=summary, rows="".join(shown)), encoding="utf-8")
    RunManifest(run_id=rid, step="style.journal.apply",
                params={"article_sha256": sha, "review_run": manifest["run_id"], "applied": applied,
                        "refused": [{"finding_id": i, "reason": why} for i, why in refused],
                        "paragraphs_changed": len(before) - untouched, "paragraphs_identical": untouched,
                        "output_sha256": sha256_file(target)},
                inputs=[rel(source), rel(run / "review.csv")], outputs=[rel(target), rel(folder / "diff.html")],
                seconds=round(time.time() - t0, 2)).write(folder)
    echo(summary)
    for i, why in refused:
        echo(f"  refused {i}: {why}")
    echo(f"wrote {target}")
    return target
