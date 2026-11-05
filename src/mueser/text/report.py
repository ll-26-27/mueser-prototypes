"""The bake-off explorer: one HTML page that shows, for every page and backend, the image beside the reading,
the character-level diff against ground truth, the scores, cost and time, and the exact prompt that was sent.
It is the page a reader opens to see HOW each number was produced, not just the number.

    uv run python -m mueser.text.report build --bakeoff out/bakeoff_<run_id>.json --pages <dir> --out outputs/index.html
"""

from __future__ import annotations

import base64
import html
import json
import mimetypes
import os
from pathlib import Path
from typing import Optional

import typer

from mueser import REPO_ROOT
from mueser.shared.review import enhance_html
from .backends.openrouter import PROMPT_PATH, load_prompt
from .evaluate import char_diff, normalize

app = typer.Typer(help="Build the bake-off HTML explorer.")


@app.callback()
def _root():
    """Sub-commands below."""


def img_src(path: Path, embed: bool, out_dir: Path | None = None) -> str:
    if embed:
        mime = mimetypes.guess_type(str(path))[0] or "image/png"
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"
    # Relative link from the explorer's folder to the page image, so the page works from the repository folder.
    return os.path.relpath(path.resolve(), (out_dir or Path(".")).resolve())


def diff_html(gt: str, hyp: str) -> str:
    out = []
    for tag, text in char_diff(gt, hyp):
        t = html.escape(text)
        if tag == "equal":
            out.append(t)
        elif tag == "delete":
            out.append(f'<del title="in ground truth, not in output">{t}</del>')
        else:
            out.append(f'<ins title="in output, not in ground truth">{t}</ins>')
    return "".join(out)


@app.command()
def build(bakeoff: Path = typer.Option(..., exists=True), pages: Path = typer.Option(..., exists=True),
          out: Path = typer.Option(...), gt: Optional[Path] = None, title: str = "Transcription bake-off",
          intro: str = "", embed_images: bool = typer.Option(False, help="inline images as base64 (one self-contained file, ~10 MB); default links to inputs/pages relatively"),
          page_notes: Optional[Path] = typer.Option(None, help="JSON {page_id: note} with provenance per page")):
    data = json.loads(bakeoff.read_text(encoding="utf-8"))
    rows = [r for r in data["rows"] if not r.get("error")]
    errors = [r for r in data["rows"] if r.get("error")]
    notes = json.loads(page_notes.read_text(encoding="utf-8")) if page_notes else {}
    page_ids = sorted({r["page_id"] for r in rows})
    backends = []
    for r in rows:
        k = (r["backend"], r["model"])
        if k not in backends:
            backends.append(k)
    prompt = load_prompt()

    def read_out(r: dict) -> str:
        p = REPO_ROOT / r["output"] / f"{r['page_id']}.txt"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def read_gt(pid: str) -> str:
        d = gt or pages
        for ext in (".txt", ".gt.txt"):
            p = d / f"{pid}{ext}"
            if p.exists():
                return p.read_text(encoding="utf-8")
        return ""

    def find_img(pid: str) -> Optional[Path]:
        for ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
            p = pages / f"{pid}{ext}"
            if p.exists():
                return p
        return None

    parts = [f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root {{ --bg:#fbfaf7; --ink:#1e1c1a; --muted:#6b6660; --line:#e4dfd6; --panel:#fff; --accent:#c8102e; --del:#ffd6d6; --ins:#d6f0dd; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#15151a; --ink:#ecebe6; --muted:#a39f98; --line:#2c2c33; --panel:#1d1d23; --del:#5a2222; --ins:#1f4a2c; }} }}
:root[data-theme="dark"] {{ --bg:#15151a; --ink:#ecebe6; --muted:#a39f98; --line:#2c2c33; --panel:#1d1d23; --del:#5a2222; --ins:#1f4a2c; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 Georgia, "Source Serif 4", serif; }}
header, section {{ padding:16px 24px; max-width:1500px; margin:0 auto; }}
h1 {{ font-size:24px; margin:0 0 6px; }} h2 {{ font-size:18px; margin:24px 0 8px; }} h3 {{ font-size:15px; margin:12px 0 4px; }}
.muted {{ color:var(--muted); }} .mono {{ font-family: ui-monospace, Menlo, monospace; font-size:12.5px; }}
table {{ border-collapse:collapse; font-size:14px; }} td, th {{ padding:4px 10px; border-bottom:1px solid var(--line); text-align:left; }} td.num {{ text-align:right; font-variant-numeric: tabular-nums; }}
.page {{ display:grid; grid-template-columns: minmax(280px, 42%) 1fr; gap:18px; border-top:1px solid var(--line); padding-top:14px; margin-top:14px; }}
.page img {{ width:100%; height:auto; border:1px solid var(--line); background:#fff; }}
.tabs {{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px; font-family: ui-sans-serif, system-ui, sans-serif; font-size:13px; }}
.tabs button {{ border:1px solid var(--line); background:var(--panel); color:var(--ink); border-radius:14px; padding:3px 10px; cursor:pointer; }}
.tabs button[aria-pressed="true"] {{ border-color:var(--accent); color:var(--accent); font-weight:600; }}
pre {{ white-space:pre-wrap; word-break:break-word; background:var(--panel); border:1px solid var(--line); padding:10px; border-radius:6px; font-size:13.5px; line-height:1.55; }}
del {{ background:var(--del); text-decoration:line-through; }} ins {{ background:var(--ins); text-decoration:none; }}
details {{ margin:8px 0; }} summary {{ cursor:pointer; }}
.stat {{ display:inline-block; margin-right:14px; }}
@media (max-width:900px) {{ .page {{ grid-template-columns:1fr; }} }}
</style></head><body>
<header><h1>{html.escape(title)}</h1><p>{intro}</p>
<p class="muted">Run <span class="mono">{html.escape(data['run_id'])}</span>. CER = character error rate against the ground truth (0.05 = one wrong character in twenty); "norm" = after the declared normalisation (ſ→s, superscript umlauts, hyphenation, whitespace). Costs are what the provider reported, or list price per page for Mistral OCR; cached calls cost nothing to rerun.</p></header>
<section><h2>Summary (mean over pages)</h2><table><tr><th>backend</th><th>model</th><th>pages</th><th>CER</th><th>WER</th><th>CER norm</th><th>WER norm</th><th>$ / page</th><th>s / page</th></tr>"""]
    for s in data["summary"]:
        f = lambda v: "" if v is None else f"{v:.3f}"  # noqa: E731
        parts.append(f"<tr><td>{html.escape(s['backend'])}</td><td class='mono'>{html.escape(s['model'])}</td><td class='num'>{s['pages']}</td><td class='num'>{f(s['cer'])}</td><td class='num'>{f(s['wer'])}</td><td class='num'>{f(s['cer_norm'])}</td><td class='num'>{f(s['wer_norm'])}</td><td class='num'>{s['cost_per_page']:.4f}</td><td class='num'>{s['seconds_per_page']:.1f}</td></tr>")
    parts.append("</table>")
    if data.get("skipped"):
        parts.append("<h3>Skipped</h3><ul>" + "".join(f"<li><b>{html.escape(s['backend'])}</b>: {html.escape(s['reason'])}</li>" for s in data["skipped"]) + "</ul>")
    if errors:
        parts.append("<h3>Errors</h3><ul>" + "".join(f"<li><b>{html.escape(e['backend'])}</b> {html.escape(e['page_id'])}: {html.escape(e['error'])}</li>" for e in errors) + "</ul>")
    parts.append(f"<details><summary>The prompt sent to every vision-language model (<span class='mono'>{html.escape(str(PROMPT_PATH.relative_to(REPO_ROOT)))}</span>)</summary><pre>{html.escape(prompt)}</pre></details>")
    parts.append(f"<details><summary>The normalisation used for the “norm” columns</summary><pre>{html.escape(normalize.__doc__ or '')}\n\n" + html.escape("ſ→s · aͤ oͤ uͤ → ä ö ü · ꝛ→r · quotation marks and dashes unified · end-of-line hyphenation joined · whitespace collapsed") + "</pre></details></section>")
    parts.append("<section><h2>Every page, every backend</h2>")
    for pid in page_ids:
        img = find_img(pid)
        gt_text = read_gt(pid)
        parts.append(f'<div class="page" id="{html.escape(pid)}"><div><h3>{html.escape(pid)}</h3>')
        if notes.get(pid):
            parts.append(f'<p class="muted">{html.escape(notes[pid])}</p>')
        if img:
            src = img_src(img, embed_images, out.parent)
            parts.append(f'<a href="{src}" target="_blank"><img src="{src}" alt="page {html.escape(pid)}" loading="lazy"></a>')
        parts.append("</div><div>")
        prs = [r for r in rows if r["page_id"] == pid]
        parts.append('<div class="tabs">' + "".join(f'<button aria-pressed="{"true" if i == 0 else "false"}" data-target="{html.escape(pid)}-{i}">{html.escape(r["backend"])} · {html.escape(r["model"])}</button>' for i, r in enumerate(prs)) + (f'<button aria-pressed="false" data-target="{html.escape(pid)}-gt">ground truth</button>' if gt_text else "") + "</div>")
        for i, r in enumerate(prs):
            hyp = read_out(r)
            stats = "".join(f'<span class="stat"><b>{k}</b> {r[k]:.3f}</span>' for k in ("cer", "wer", "cer_norm", "wer_norm") if r.get(k) not in (None, ""))
            stats += f'<span class="stat"><b>lines</b> {r.get("lines", "")}</span><span class="stat"><b>$</b> {float(r.get("cost_usd") or 0):.4f}</span><span class="stat"><b>s</b> {r.get("seconds", "")}</span>' + (' <span class="stat muted">cached</span>' if r.get("cached") else "")
            parts.append(f'<div class="pane" id="{html.escape(pid)}-{i}" style="display:{"block" if i == 0 else "none"}"><p class="mono">{stats}</p>')
            if gt_text:
                parts.append(f'<p class="muted">Diff against ground truth: <del>missing or wrong</del> <ins>extra or substituted</ins></p><pre>{diff_html(gt_text.strip(), hyp.strip())}</pre><details><summary>Output as written</summary><pre>{html.escape(hyp)}</pre></details>')
            else:
                parts.append(f"<pre>{html.escape(hyp)}</pre>")
            parts.append(f'<p class="mono muted">output: {html.escape(r["output"])}/{html.escape(pid)}.txt · PAGE-XML beside it' + (f' · prompt sha256 {html.escape(str(r.get("prompt_sha256"))[:12])}…' if r.get("prompt_sha256") else "") + "</p></div>")
        if gt_text:
            parts.append(f'<div class="pane" id="{html.escape(pid)}-gt" style="display:none"><pre>{html.escape(gt_text)}</pre></div>')
        parts.append("</div></div>")
    parts.append("""</section>
<script>
document.querySelectorAll('.tabs').forEach(t => t.addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  t.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
  const page = t.parentElement; page.querySelectorAll('.pane').forEach(p => p.style.display = p.id === b.dataset.target ? 'block' : 'none');
}));
</script></body></html>""")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(enhance_html("".join(parts), out, "report"), encoding="utf-8")
    typer.echo(f"{len(page_ids)} pages × {len(backends)} backends -> {out}")


if __name__ == "__main__":
    app()
