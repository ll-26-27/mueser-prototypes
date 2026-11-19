"""Assemble one JSON for the page and render ``outputs/index.html`` from it.

The viewer must map selections to line ids and character offsets, redraw boxes, switch modes and keep rows in
register, all of which is a render from data, so the page renders itself client-side from a single embedded blob
(``<script type="application/json" id="reading-data">``). Everything the page needs at open time is in the file:
``fetch()`` of sibling files is blocked under ``file://``. A ``<noscript>`` block lists every line with its id.
"""

from __future__ import annotations

import html
import json
import os
from pathlib import Path

from mueser.shared.review import enhance_html
from mueser.shared.runs import git_sha, rel

from . import WEB, case_paths
from .log import read as read_log
from .settle import load_build
from .translate import latest_translation_run, layer_sha256


def load_translation(case: Path, run: str | None) -> dict[str, dict]:
    """{page_id: blocks.json} for a translation run (``None`` = latest, ``"none"`` = no translation)."""
    P = case_paths(case)
    if run == "none":
        return {}
    folder = (P["runs"] / run) if run else latest_translation_run(case)
    if not folder or not (folder / "translation").is_dir():
        return {}
    out = {}
    for bf in sorted((folder / "translation").glob("*.blocks.json")):
        d = json.loads(bf.read_text(encoding="utf-8"))
        out[d["page_id"]] = d
    return out


def assemble(case: Path, *, build_id: str | None = None, translation_run: str | None = None) -> dict:
    P = case_paths(case)
    folder, settled = load_build(case, build_id)
    meta = json.loads(P["metadata"].read_text(encoding="utf-8")) if P["metadata"].exists() else {"docs": {}}
    translation = load_translation(case, translation_run)
    events = [e.model_dump() for e in read_log(P["log"])]
    pages = []
    for pid, pg in settled["pages"].items():
        image_rel = os.path.relpath((P["case"] / pg["image"]).resolve(), P["index"].resolve().parent)
        tr = None
        if pid in translation:
            t = translation[pid]
            tr = {"run_id": t.get("run_id"), "build_id": t.get("build_id"), "models": t.get("models"), "min_divergence": t.get("min_divergence"),
                  "blocks": t.get("blocks"), "segments": t.get("segments"), "uncovered": t.get("uncovered"), "notes": t.get("notes"),
                  "stale": t.get("layer_sha256") != layer_sha256(pg["lines"]),
                  "resolved": (pg.get("translation") or {}).get("resolved") or []}
        pages.append({**{k: v for k, v in pg.items() if k != "translation"}, "page_id": pid, "image": image_rel.replace(os.sep, "/"),
                      "translation": tr})
    return {
        "build_id": settled["build_id"], "parent_build": settled.get("parent_build"), "created": settled.get("created"),
        "normalize_sha256": settled.get("normalize_sha256"), "decisions_applied": settled.get("decisions_applied", []),
        "case": rel(P["case"]), "client": f"reading-room@{git_sha() or 'nogit'}",
        "paths": {"log": rel(P["log"]), "inbox": rel(P["inbox"]) + "/", "build": rel(folder)},
        "metadata": meta, "pages": pages, "log": events,
    }


def noscript_block(data: dict) -> str:
    parts = []
    for pg in data["pages"]:
        doc = (data["metadata"].get("docs") or {}).get(pg["doc_id"], {})
        parts.append(f'<h2>{html.escape(doc.get("title") or pg["doc_id"])} · {html.escape(pg["page_id"])}</h2><ol>')
        for l in pg["lines"]:
            parts.append(f'<li id="{html.escape(pg["page_id"])}-{l["line_id"]}" value="{l["line_id"][1:]}">{html.escape(l["settled"])}</li>')
        parts.append("</ol>")
        if pg.get("translation"):
            parts.append("<h3>Translation</h3><ol>")
            for b in pg["translation"]["blocks"]:
                parts.append(f'<li>[{html.escape(" ".join(b["lines"]))}] {html.escape((b.get("a") or b.get("b") or {}).get("text", ""))}</li>')
            parts.append("</ol>")
    return "\n".join(parts)


def render(data: dict, out: Path, title: str) -> Path:
    tpl = (WEB / "reading.html").read_text(encoding="utf-8")
    css = (WEB / "reading.css").read_text(encoding="utf-8")
    js = (WEB / "reading.js").read_text(encoding="utf-8")
    blob = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    doc = (tpl.replace("{{title}}", html.escape(title)).replace("{{css}}", css).replace("{{noscript}}", noscript_block(data))
           .replace("{{data}}", blob).replace("{{js}}", js))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(enhance_html(doc, out, "reading"), encoding="utf-8")
    return out


def build(case: Path, *, build_id: str | None = None, translation_run: str | None = None,
          title: str = "Reading room") -> Path:
    P = case_paths(case)
    data = assemble(case, build_id=build_id, translation_run=translation_run)
    P["reading"].mkdir(parents=True, exist_ok=True)
    (P["reading"] / "reading.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return render(data, P["index"], title)
