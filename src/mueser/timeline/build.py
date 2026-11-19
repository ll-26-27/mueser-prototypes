"""Render the page: ``timeline.json`` and the log into one self-contained ``outputs/index.html``.

The page carries all its data in a JSON block and draws itself; without JavaScript it lists every node with
its dates and its first link. The shared review bar is injected so the top links to the home page work.
"""

from __future__ import annotations

import html
import json
import time
from pathlib import Path

from mueser.shared.review import enhance_html
from mueser.shared.runs import RunManifest, rel

from . import WEB, case_paths
from .log import read

TYPE_ORDER = ["person", "work", "event", "period", "concept"]
TYPE_NAMES = {"person": "People", "work": "Works", "event": "Events", "period": "Periods", "concept": "Concepts and movements"}


def noscript_block(data: dict) -> str:
    by_type: dict[str, list[dict]] = {t: [] for t in TYPE_ORDER}
    for n in data["nodes"]:
        by_type.setdefault(n["type"], []).append(n)
    parts = ["<p>This page needs JavaScript to draw the timeline. Every node, with its dates and first reference:</p>"]
    for t in TYPE_ORDER:
        items = sorted(by_type.get(t, []), key=lambda n: (n.get("sy") if n.get("sy") is not None else 99999, n["label"]))
        if not items:
            continue
        parts.append(f"<h2>{TYPE_NAMES.get(t, t)} ({len(items)})</h2><ul>")
        for n in items:
            years = n.get("sl") or ""
            if n.get("el") and n.get("el") != n.get("sl"):
                years = f"{years}–{n['el']}"
            first = n["links"][0] if n.get("links") else None
            link = f' <a href="{html.escape(first["url"])}">{html.escape(first["name"])}</a>' if first else ""
            parts.append(f"<li>{html.escape(n['label'])} ({html.escape(years)}){link}</li>")
        parts.append("</ul>")
    return "\n".join(parts)


def render(data: dict, events: list[dict], *, title: str) -> str:
    template = (WEB / "timeline.html").read_text(encoding="utf-8")
    css = (WEB / "timeline.css").read_text(encoding="utf-8")
    js = (WEB / "timeline.js").read_text(encoding="utf-8")
    payload = {**data, "log": events}
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return (template.replace("{{title}}", html.escape(title)).replace("{{css}}", css)
            .replace("{{noscript}}", noscript_block(data)).replace("{{data}}", blob).replace("{{js}}", js))


def build(case: Path, *, title: str = "Thinkers and events", echo=print) -> Path:
    P = case_paths(case)
    t0 = time.time()
    data = json.loads(P["json"].read_text(encoding="utf-8"))
    events = [e.model_dump(exclude_none=True) for e in read(P["log"])]
    doc = render(data, events, title=title)
    doc = enhance_html(doc, P["index"], "timeline")
    P["index"].write_text(doc, encoding="utf-8")
    RunManifest(run_id=f"build-{time.strftime('%Y%m%d-%H%M%S')}", step="timeline.build",
                params={"data_id": data.get("data_id"), "events": len(events)}, inputs=[rel(P["json"]), rel(P["log"])],
                outputs=[rel(P["index"])], seconds=round(time.time() - t0, 1)).write(P["timeline"] / "builds" / data.get("data_id", "x"))
    size = P["index"].stat().st_size
    echo(f"{P['index']} ({size / 1e6:.1f} MB, {len(data['nodes'])} nodes, {len(data['edges'])} edges, {len(events)} log events)")
    return P["index"]
