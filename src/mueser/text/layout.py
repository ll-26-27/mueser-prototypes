"""The layout pass: a vision-language model maps a page (regions by kind, every line's box, marginalia, later
hands, reading order) without transcribing it, and an overlay page draws those boxes beside Kraken's own
segmentation so the two can be compared by eye and by count.

    uv run python -m mueser.text.layout run --pages <dir> --out <dir> --model google/gemini-3.8-flash
    uv run python -m mueser.text.layout overlay --layouts <out dir> --pages <dir> --out <dir>/layout.html [--kraken]

What this is for: (1) counting lines per page against a backend's line count, (2) finding what is NOT main text
(annotations, stamps, corrections) before transcription, (3) a cheap check on reading order for two-column pages.
Coordinates come back as fractions of the image; they are approximate and the overlay says so.
"""

from __future__ import annotations

import html
import json
import os
import re
import time
from pathlib import Path
from typing import Optional

import typer
from PIL import Image

from mueser.shared import env
from mueser.shared.review import enhance_html
from mueser.shared.cache import sha256_text
from mueser.shared.openrouter import MissingCredential, chat
from mueser.shared.runs import RunManifest, rel, run_id as make_run_id

app = typer.Typer(help="Layout analysis with a vision model, and an overlay viewer.")
PROMPT_PATH = Path(__file__).parent / "backends" / "prompts" / "layout_de.md"
IMG_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}

KINDS = ["main_text", "heading", "column", "page_number", "catchword", "signature_mark", "marginalia", "interlinear", "correction",
         "stamp_or_seal", "date_line", "salutation", "signature", "address", "table", "figure", "ornament", "other"]
BBOX = {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4}
SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["regions", "reading_order", "page_notes"],
    "properties": {
        "regions": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "kind", "bbox", "hand", "script", "later_hand", "note", "lines"],
            "properties": {
                "id": {"type": "string"}, "kind": {"type": "string", "enum": KINDS}, "bbox": BBOX,
                "hand": {"type": "string", "enum": ["print", "handwriting", "mixed"]},
                "script": {"type": "string", "enum": ["fraktur", "antiqua", "kurrent", "suetterlin", "latin_cursive", "mixed", "unknown"]},
                "later_hand": {"type": "boolean"}, "note": {"type": "string"},
                "lines": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["bbox"], "properties": {"bbox": BBOX}}},
            }}},
        "reading_order": {"type": "array", "items": {"type": "string"}},
        "page_notes": {"type": "string"},
    },
}


@app.callback()
def _root():
    """Sub-commands below."""


def load_prompt() -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    m = re.search(r"<!-- PROMPT START -->\s*(.*?)\s*<!-- PROMPT END -->", text, re.S)
    return (m.group(1) if m else text).strip()


@app.command()
def run(pages: Path = typer.Option(..., exists=True), out: Path = typer.Option(...), model: Optional[str] = None, limit: int = 0):
    model = model or env.get("VLM_MODEL_FRONTIER", "google/gemini-2.5-flash")
    system = load_prompt()
    rid = make_run_id()
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in pages.iterdir() if p.suffix.lower() in IMG_EXT)[: limit or None]
    man = RunManifest(run_id=rid, step="layout", params={"model": model, "prompt_sha256": sha256_text(system), "pages": rel(pages)})
    t0 = time.time()
    for p in files:
        try:
            res = chat(model=model, system=system, user_text="Map the layout of this page. Return JSON only.", image_path=p, schema=SCHEMA,
                       schema_name="layout", max_tokens=8000, step="layout")
        except MissingCredential as e:
            typer.echo(f"skip: {e}")
            raise typer.Exit(1)
        parsed = res.get("parsed") or {"regions": [], "reading_order": [], "page_notes": "no JSON parsed"}
        with Image.open(p) as im:
            w, h = im.size
        doc = {"page_id": p.stem, "image": p.name, "width": w, "height": h, "model": res.get("model") or model, "cached": res.get("cached"),
               "cost_usd": res.get("cost_usd"), "seconds": res.get("seconds"), "prompt_sha256": sha256_text(system), "cache_key": res.get("key"),
               "layout": parsed}
        (out / f"{p.stem}.layout.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        n_lines = sum(len(r.get("lines", [])) for r in parsed.get("regions", []))
        kinds = {}
        for r in parsed.get("regions", []):
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        man.cost_usd += float(res.get("cost_usd") or 0)
        man.outputs.append(rel(out / f"{p.stem}.layout.json"))
        typer.echo(f"{p.stem:42} regions={len(parsed.get('regions', []))} lines={n_lines} {kinds} ${float(res.get('cost_usd') or 0):.4f}{' (cached)' if res.get('cached') else ''}")
    man.seconds = round(time.time() - t0, 1)
    man.write(out / "runs" / rid)
    typer.echo(f"run {rid}: ${man.cost_usd:.4f}")


def kraken_lines(image_path: Path) -> list[list[float]]:
    """Kraken's own line boxes (pixels) for the same page, for the comparison column."""
    from .backends.kraken import KrakenBackend

    seg = KrakenBackend().segment(image_path)
    boxes = []
    lines = seg.lines if hasattr(seg, "lines") else seg.get("lines", [])
    for ln in lines:
        boundary = getattr(ln, "boundary", None) or (ln.get("boundary") if isinstance(ln, dict) else None)
        if not boundary:
            continue
        xs = [p[0] for p in boundary]; ys = [p[1] for p in boundary]
        boxes.append([min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)])
    return boxes


KIND_COLORS = {"main_text": "#2a78d6", "column": "#2a78d6", "heading": "#8e44ad", "marginalia": "#c8102e", "interlinear": "#c8102e", "correction": "#e67e22",
               "stamp_or_seal": "#16a085", "page_number": "#7f8c8d", "catchword": "#7f8c8d", "signature_mark": "#7f8c8d", "date_line": "#27ae60",
               "salutation": "#27ae60", "signature": "#27ae60", "address": "#27ae60", "table": "#d35400", "figure": "#95a5a6", "ornament": "#95a5a6", "other": "#555"}


@app.command()
def overlay(layouts: Path = typer.Option(..., exists=True), pages: Path = typer.Option(..., exists=True), out: Path = typer.Option(...),
            kraken: bool = typer.Option(False, help="also draw Kraken's segmentation (needs --extra htr and the models)"),
            title: str = "Layout: what a vision model sees, beside Kraken's segmentation"):
    docs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(layouts.glob("*.layout.json"))]
    parts = [f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title>
<style>
:root {{ --bg:#fbfaf7; --ink:#1e1c1a; --muted:#6b6660; --line:#e4dfd6; --panel:#fff; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#15151a; --ink:#ecebe6; --muted:#a39f98; --line:#2c2c33; --panel:#1d1d23; }} }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 Georgia, serif; }} header, section {{ padding:16px 24px; max-width:1500px; margin:0 auto; }}
h1 {{ font-size:22px; margin:0 0 6px; }} h2 {{ font-size:17px; margin:20px 0 6px; }} .muted {{ color:var(--muted); }} .mono {{ font-family: ui-monospace, Menlo, monospace; font-size:12.5px; }}
.page {{ display:grid; grid-template-columns: 1fr 1fr; gap:16px; border-top:1px solid var(--line); padding-top:14px; margin-top:14px; }}
.fig {{ position:relative; }} .fig img {{ width:100%; height:auto; display:block; border:1px solid var(--line); }} .fig svg {{ position:absolute; inset:0; width:100%; height:100%; }}
.fig rect {{ fill:none; stroke-width:2; vector-effect:non-scaling-stroke; }} .fig rect.line {{ stroke-dasharray:4 3; stroke-width:1.2; opacity:.9; }}
.leg span {{ display:inline-block; margin:0 10px 4px 0; font-family: ui-sans-serif, system-ui, sans-serif; font-size:12px; }} .leg i {{ display:inline-block; width:10px; height:10px; border:2px solid; margin-right:4px; vertical-align:middle; }}
table {{ border-collapse:collapse; font-size:13px; }} td, th {{ padding:3px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
@media (max-width:900px) {{ .page {{ grid-template-columns:1fr; }} }}
</style></head><body><header><h1>{html.escape(title)}</h1>
<p>Left: regions and lines as the vision model described them (solid = region, dashed = line), coloured by kind. Right: Kraken's line segmentation on the same image, when available. Boxes from the model are fractions of the image it saw and are approximate; counts are the thing to compare.</p>
<p class="leg">""" + "".join(f'<span><i style="border-color:{c}"></i>{k}</span>' for k, c in KIND_COLORS.items()) + "</p></header><section>"]
    for d in docs:
        img = pages / d["image"]
        src = os.path.relpath(img.resolve(), out.parent.resolve())
        regs = d["layout"].get("regions", [])
        svg = [f'<svg viewBox="0 0 {d["width"]} {d["height"]}" preserveAspectRatio="none">']
        for r in regs:
            x, y, w, h = r["bbox"]
            c = KIND_COLORS.get(r["kind"], "#555")
            svg.append(f'<rect x="{x*d["width"]:.0f}" y="{y*d["height"]:.0f}" width="{w*d["width"]:.0f}" height="{h*d["height"]:.0f}" stroke="{c}"><title>{html.escape(r["id"])}: {html.escape(r["kind"])} ({html.escape(r["hand"])}, {html.escape(r["script"])}){" later hand" if r.get("later_hand") else ""} — {html.escape(r.get("note",""))}</title></rect>')
            for ln in r.get("lines", []):
                lx, ly, lw, lh = ln["bbox"]
                svg.append(f'<rect class="line" x="{lx*d["width"]:.0f}" y="{ly*d["height"]:.0f}" width="{lw*d["width"]:.0f}" height="{lh*d["height"]:.0f}" stroke="{c}"/>')
        svg.append("</svg>")
        n_lines = sum(len(r.get("lines", [])) for r in regs)
        kboxes = []
        if kraken:
            try:
                kboxes = kraken_lines(img)
            except Exception as e:  # noqa: BLE001
                typer.echo(f"kraken segmentation failed for {img.name}: {e}")
        ksvg = [f'<svg viewBox="0 0 {d["width"]} {d["height"]}" preserveAspectRatio="none">'] + [f'<rect class="line" x="{b[0]:.0f}" y="{b[1]:.0f}" width="{b[2]:.0f}" height="{b[3]:.0f}" stroke="#1f8a4c"/>' for b in kboxes] + ["</svg>"]
        parts.append(f'<h2>{html.escape(d["page_id"])} <span class="muted mono">{html.escape(d["model"])} · ${float(d.get("cost_usd") or 0):.4f} · {d.get("seconds")}s</span></h2>')
        parts.append(f'<p class="muted">{html.escape(d["layout"].get("page_notes", ""))}</p>')
        parts.append('<div class="page">')
        parts.append(f'<div><p class="mono">vision model: {len(regs)} regions, {n_lines} lines; reading order {html.escape(" → ".join(d["layout"].get("reading_order", [])))}</p><div class="fig"><img src="{src}" alt="{html.escape(d["page_id"])}" loading="lazy">{"".join(svg)}</div></div>')
        parts.append(f'<div><p class="mono">kraken: {len(kboxes)} lines{"" if kraken else " (not run; pass --kraken)"}</p><div class="fig"><img src="{src}" alt="" loading="lazy">{"".join(ksvg)}</div></div>')
        parts.append("</div><table><tr><th>region</th><th>kind</th><th>hand · script</th><th>lines</th><th>later hand</th><th>note</th></tr>")
        for r in regs:
            parts.append(f'<tr><td class="mono">{html.escape(r["id"])}</td><td>{html.escape(r["kind"])}</td><td>{html.escape(r["hand"])} · {html.escape(r["script"])}</td><td>{len(r.get("lines", []))}</td><td>{"yes" if r.get("later_hand") else ""}</td><td>{html.escape(r.get("note", ""))}</td></tr>')
        parts.append("</table>")
    parts.append("</section></body></html>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(enhance_html("".join(parts), out, "layout"), encoding="utf-8")
    typer.echo(f"{len(docs)} pages -> {out}")


if __name__ == "__main__":
    app()
