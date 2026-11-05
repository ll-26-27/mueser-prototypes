"""Consensus without ground truth: align every reading of a page, split readers into the OCR family (Tesseract,
Kraken, eScriptorium) and the vision family (vision models, hybrid, Mistral), and find where they disagree.

    uv run python -m mueser.text.compare run   --bakeoff outputs/bakeoff_<run_id>.json --out outputs/consensus
    uv run python -m mueser.text.compare apply --consensus outputs/consensus --decisions outputs/consensus/checkin.csv --out outputs/consensus/corrected

For each page: a pairwise agreement matrix (1 − normalised CER between two readings); the **medoid** reading per
family and overall (the one closest to all others); and, on the overall medoid, every character span where at
least one other reader differs, with each reader's alternative. Those spans are the human check-in list
(``checkin.csv``). A person writes the right text in ``decision`` (or leaves it blank to keep the medoid), and
``apply`` writes a corrected text per page that can become ground truth for the next run. Ground truth, when it
exists, is scored too, so the report shows whether agreement predicts correctness.
"""

from __future__ import annotations

import csv
import difflib
import html
import json
import os
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import typer

from mueser import REPO_ROOT
from mueser.shared.review import enhance_html
from .evaluate import normalize, score

app = typer.Typer(help="Consensus and disagreement across readings; the human check-in step.")
FAMILY = {"tesseract": "ocr", "kraken": "ocr", "escriptorium": "ocr", "transkribus": "ocr", "churro": "ocr",
          "openrouter": "vision", "hybrid": "vision", "mistral": "vision"}


@app.callback()
def _root():
    """Sub-commands below."""


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def dist(a: str, b: str) -> float:
    """Normalised distance between two readings: CER of b against a after the declared normalisation, symmetrised."""
    na, nb = normalize(a), normalize(b)
    if not na and not nb:
        return 0.0
    sm = difflib.SequenceMatcher(a=na, b=nb, autojunk=False)
    return round(1 - sm.ratio(), 4)


@dataclass
class Reading:
    key: str            # backend:model
    backend: str
    model: str
    family: str
    text: str
    cer_norm: Optional[float] = None
    cost_usd: float = 0.0


@dataclass
class Span:
    start: int
    end: int
    base: str
    alternatives: dict[str, str] = field(default_factory=dict)   # reader key -> what it has instead

    @property
    def n_disagree(self) -> int:
        return len(self.alternatives)


def medoid(readings: list[Reading], D: dict[tuple[str, str], float]) -> Optional[Reading]:
    if not readings:
        return None
    if len(readings) == 1:
        return readings[0]
    return min(readings, key=lambda r: sum(D[(r.key, o.key)] for o in readings if o.key != r.key) / (len(readings) - 1))


def disagreements(base: Reading, others: list[Reading]) -> list[Span]:
    """Character spans of the base text where any other reading differs, with each reader's alternative.

    Computed on the declared normalisation (ſ→s, superscript umlauts, hyphenation, whitespace), so that a reader
    that keeps the long s and one that modernises it are not counted as disagreeing about the word."""
    b = normalize(base.text)
    marks: dict[tuple[int, int], dict[str, str]] = {}
    for o in others:
        t = normalize(o.text)
        sm = difflib.SequenceMatcher(a=b, b=t, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            marks.setdefault((i1, i2), {})[o.key] = t[j1:j2]
    # merge overlapping spans
    spans: list[Span] = []
    for (i1, i2), alts in sorted(marks.items()):
        if spans and i1 <= spans[-1].end:
            s = spans[-1]
            s.end = max(s.end, i2)
            s.base = b[s.start:s.end]
            for k, v in alts.items():
                s.alternatives[k] = (s.alternatives.get(k, "") + v) if k in s.alternatives else v
        else:
            spans.append(Span(i1, i2, b[i1:i2], dict(alts)))
    # widen each span to word boundaries for readability, then merge any that now overlap
    for s in spans:
        while s.start > 0 and b[s.start - 1] != " ":
            s.start -= 1
        while s.end < len(b) and b[s.end] != " ":
            s.end += 1
    merged: list[Span] = []
    for s in spans:
        if merged and s.start <= merged[-1].end:
            m = merged[-1]
            m.end = max(m.end, s.end)
            for k, v in s.alternatives.items():
                m.alternatives[k] = (m.alternatives[k] + " " + v).strip() if k in m.alternatives else v
        else:
            merged.append(s)
    for s in merged:
        s.base = b[s.start:s.end]
    return merged


def gt_for(page_id: str, gt_dir: Optional[Path]) -> Optional[str]:
    if not gt_dir:
        return None
    for ext in (".txt", ".gt.txt"):
        p = gt_dir / f"{page_id}{ext}"
        if p.exists():
            return p.read_text(encoding="utf-8")
    return None


@app.command()
def run(bakeoff: Path = typer.Option(..., exists=True), out: Path = typer.Option(...), gt: Optional[Path] = None, pages_dir: Optional[Path] = None,
        title: str = "Consensus and check-in",
        min_weight: float = typer.Option(0.25, help="a span goes on the check-in list when the readers that differ from the medoid carry at least this share of the total reliability (a reader's reliability is its mean agreement with all others); all spans stay in consensus.json")):
    data = json.loads(bakeoff.read_text(encoding="utf-8"))
    rows = [r for r in data["rows"] if not r.get("error")]
    out.mkdir(parents=True, exist_ok=True)
    pages = sorted({r["page_id"] for r in rows})
    result = {"run_id": data["run_id"], "min_weight": min_weight, "pages": {}}
    checkin: list[dict] = []
    for pid in pages:
        readings: list[Reading] = []
        for r in rows:
            if r["page_id"] != pid:
                continue
            p = REPO_ROOT / r["output"] / f"{pid}.txt"
            if not p.exists():
                continue
            readings.append(Reading(key=f"{r['backend']}:{r['model']}", backend=r["backend"], model=r["model"], family=FAMILY.get(r["backend"], "other"),
                                    text=p.read_text(encoding="utf-8"), cer_norm=r.get("cer_norm"), cost_usd=float(r.get("cost_usd") or 0)))
        if len(readings) < 2:
            continue
        D = {}
        for a in readings:
            for b in readings:
                D[(a.key, b.key)] = 0.0 if a is b else dist(a.text, b.text)
        # Reliability without ground truth: how much each reader agrees with everyone else on this page.
        reliability = {r.key: round(1 - sum(D[(r.key, o.key)] for o in readings if o is not r) / (len(readings) - 1), 4) for r in readings}
        fam = {f: [r for r in readings if r.family == f] for f in ("ocr", "vision")}
        med = {f: medoid(rs, D) for f, rs in fam.items()}
        overall = medoid(readings, D)
        spans = disagreements(overall, [r for r in readings if r is not overall])
        total_rel = sum(reliability[r.key] for r in readings if r is not overall) or 1.0
        weights = [round(sum(reliability[k] for k in sp.alternatives) / total_rel, 3) for sp in spans]
        gt_text = gt_for(pid, gt)
        agreement_score = round(1 - sum(D[(overall.key, o.key)] for o in readings if o is not overall) / (len(readings) - 1), 4)
        result["pages"][pid] = {
            "readers": [{"key": r.key, "family": r.family, "cer_norm": r.cer_norm, "cost_usd": r.cost_usd} for r in readings],
            "matrix": {a.key: {b.key: D[(a.key, b.key)] for b in readings} for a in readings},
            "medoid": {"overall": overall.key, "ocr": med["ocr"].key if med["ocr"] else None, "vision": med["vision"].key if med["vision"] else None},
            "family_gap": (D[(med["ocr"].key, med["vision"].key)] if med["ocr"] and med["vision"] else None),
            "agreement": agreement_score,
            "medoid_cer_norm": (score(gt_text, overall.text).cer_norm if gt_text else None),
            "reliability": reliability,
            "spans": [{"start": s.start, "end": s.end, "base": s.base, "alternatives": s.alternatives, "weight": w} for s, w in zip(spans, weights)],
            "base_text": normalize(overall.text),
        }
        for i, (s, w) in enumerate(zip(spans, weights)):
            if w < min_weight:
                continue
            checkin.append({"page_id": pid, "span": i, "start": s.start, "end": s.end, "medoid": overall.key, "base": s.base,
                            "n_disagree": s.n_disagree, "of": len(readings) - 1, "weight": w,
                            "alternatives": " | ".join(f"{k}: {v!r}" for k, v in s.alternatives.items()), "decision": ""})
        n_check = sum(1 for w in weights if w >= min_weight)
        result["pages"][pid]["check_in"] = n_check
        typer.echo(f"{pid:42} readers={len(readings)} medoid={overall.key} agreement={agreement_score:.3f} spans={len(spans)} check-in={n_check}" + (f" medoid CERn={result['pages'][pid]['medoid_cer_norm']:.3f}" if gt_text else ""))
    (out / "consensus.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    with (out / "checkin.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(checkin[0].keys()) if checkin else ["page_id"])
        w.writeheader()
        w.writerows(checkin)
    build_html(result, out / "index.html", pages_dir, title)
    typer.echo(f"{len(checkin)} spans for check-in -> {out / 'checkin.csv'}; report -> {out / 'index.html'}")


def build_html(result: dict, out: Path, pages_dir: Optional[Path], title: str) -> None:
    parts = [f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title>
<style>
:root {{ --bg:#fbfaf7; --ink:#1e1c1a; --muted:#6b6660; --line:#e4dfd6; --panel:#fff; --accent:#c8102e; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#15151a; --ink:#ecebe6; --muted:#a39f98; --line:#2c2c33; --panel:#1d1d23; }} }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.55 Georgia, serif; }} header, section {{ padding:16px 24px; max-width:1500px; margin:0 auto; }}
h1 {{ font-size:22px; margin:0 0 6px; }} h2 {{ font-size:18px; margin:26px 0 6px; }} h3 {{ font-size:15px; margin:12px 0 4px; }} .muted {{ color:var(--muted); }} .mono {{ font-family: ui-monospace, Menlo, monospace; font-size:12.5px; }}
table {{ border-collapse:collapse; font-size:13px; }} td, th {{ padding:3px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }} td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.matrix td.c {{ text-align:center; width:48px; }} .page {{ display:grid; grid-template-columns: minmax(260px, 36%) 1fr; gap:18px; border-top:1px solid var(--line); padding-top:14px; margin-top:16px; }} .page img {{ width:100%; height:auto; border:1px solid var(--line); }}
.text {{ background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:10px 12px; font-size:14.5px; line-height:1.7; white-space:pre-wrap; }}
mark {{ background:rgba(200,16,46,.18); border-bottom:2px solid rgba(200,16,46,.6); color:inherit; cursor:help; }} mark.strong {{ background:rgba(200,16,46,.38); }}
.chip {{ display:inline-block; font-family: ui-sans-serif, system-ui, sans-serif; font-size:11px; padding:1px 7px; border-radius:10px; background:var(--line); margin-right:4px; }}
@media (max-width:900px) {{ .page {{ grid-template-columns:1fr; }} }}
</style></head><body><header><h1>{html.escape(title)}</h1>
<p>No ground truth is needed for this page. Every reading of a page is compared with every other; the <b>medoid</b> is the reading closest to all the rest and is shown as the base text, in the declared normalisation (ſ folded to s, so that is not counted as a disagreement). Every span where at least one other reader differs is marked; darker means more readers disagree. Hover a mark for each reader's alternative. Spans where the dissenting readers carry at least {result["min_weight"]:.0%} of the page's total reliability (a reader's reliability is its mean agreement with the others, so four weak OCR models dissenting together count for less than one strong model) are the <b>check-in list</b> (<span class="mono">checkin.csv</span>) for a person to settle; where ground truth exists the medoid's own error rate is shown, so you can see whether agreement predicted correctness.</p>
<p class="muted">Readers are grouped into the <b>OCR family</b> (Tesseract, Kraken, eScriptorium: segment, then recognise, no language sense beyond their training) and the <b>vision family</b> (vision-language models and the hybrid mode: read the image as a whole, with a language sense that can both fix and invent). The family gap is the distance between the two families' medoids.</p></header><section>"""]
    for pid, pg in result["pages"].items():
        readers = pg["readers"]; keys = [r["key"] for r in readers]
        parts.append(f'<div class="page" id="{html.escape(pid)}"><div><h2>{html.escape(pid)}</h2>')
        if pages_dir:
            for ext in (".png", ".jpg", ".jpeg"):
                img = pages_dir / f"{pid}{ext}"
                if img.exists():
                    parts.append(f'<a href="{os.path.relpath(img.resolve(), out.parent.resolve())}" target="_blank"><img src="{os.path.relpath(img.resolve(), out.parent.resolve())}" alt="{html.escape(pid)}" loading="lazy"></a>')
                    break
        parts.append(f'<p class="mono">medoid {html.escape(pg["medoid"]["overall"])}<br>agreement {pg["agreement"]:.3f} · family gap {"" if pg["family_gap"] is None else f"{pg['family_gap']:.3f}"}' + (f' · medoid CER norm {pg["medoid_cer_norm"]:.3f}' if pg.get("medoid_cer_norm") is not None else "") + f' · {len(pg["spans"])} spans marked, {pg.get("check_in", 0)} on the check-in list</p>')
        parts.append('<table class="matrix"><tr><th></th>' + "".join(f'<th class="c" title="{html.escape(k)}">{html.escape(k.split(":")[0][:3])}<br>{html.escape(k.split(":")[-1].split("/")[-1][:10])}</th>' for k in keys) + "<th>family</th><th>reliability</th><th>CER n</th></tr>")
        for r in readers:
            parts.append(f'<tr><th class="mono" title="{html.escape(r["key"])}">{html.escape(r["key"].split(":")[-1].split("/")[-1][:22])}</th>' + "".join(
                f'<td class="c num" style="background:rgba(42,120,214,{max(0, 1 - pg["matrix"][r["key"]][k]) * 0.45:.2f})">{"" if k == r["key"] else f"{1 - pg['matrix'][r['key']][k]:.2f}"}</td>' for k in keys)
                + f'<td>{r["family"]}</td><td class="num">{pg["reliability"][r["key"]]:.3f}</td><td class="num">{"" if r.get("cer_norm") is None else f"{r['cer_norm']:.3f}"}</td></tr>')
        parts.append("</table><p class='muted mono'>cells: agreement between two readings (1 − normalised distance)</p></div><div>")
        if pg["agreement"] < 0.6:
            parts.append(f'<p style="border-left:3px solid var(--accent); padding:6px 10px"><b>Readers disagree too much for a span-level check-in</b> (agreement {pg["agreement"]:.2f}). The marked spans below merge into most of the page. Treat the medoid as a draft to read against the image, or add a stronger reader, rather than settling spans one by one.</p>')
        b = pg["base_text"]; n = max(1, len(readers) - 1)
        pos = 0; out_html = []
        for s in sorted(pg["spans"], key=lambda x: x["start"]):
            out_html.append(html.escape(b[pos:s["start"]]))
            strong = " strong" if s.get("weight", 0) >= result["min_weight"] else ""
            tip = " / ".join(f'{k.split(":")[-1].split("/")[-1]}: {v!r}' for k, v in s["alternatives"].items())
            out_html.append(f'<mark class="{strong}" title="{html.escape(tip)}">{html.escape(b[s["start"]:s["end"]])}</mark>')
            pos = s["end"]
        out_html.append(html.escape(b[pos:]))
        parts.append(f'<h3>Base text (medoid) with disagreements</h3><div class="text">{"".join(out_html)}</div>')
        parts.append(f"<h3>Check-in list (dissent weight ≥ {result['min_weight']:.0%})</h3><table><tr><th>#</th><th>base</th><th>weight</th><th>disagree</th><th>alternatives</th></tr>")
        for i, s in enumerate(pg["spans"]):
            if s.get("weight", 0) < result["min_weight"]:
                continue
            parts.append(f'<tr><td class="num">{i}</td><td>{html.escape(s["base"])}</td><td class="num">{s["weight"]:.2f}</td><td class="num">{len(s["alternatives"])}/{n}</td><td class="mono">' + "<br>".join(f'<span class="chip">{html.escape(k.split(":")[-1].split("/")[-1][:18])}</span>{html.escape(v) if v else "<i>(nothing)</i>"}' for k, v in s["alternatives"].items()) + "</td></tr>")
        parts.append("</table></div></div>")
    parts.append("</section></body></html>")
    out.write_text(enhance_html("".join(parts), out, "consensus"), encoding="utf-8")


@app.command()
def apply(consensus: Path = typer.Option(..., exists=True), decisions: Path = typer.Option(..., exists=True), out: Path = typer.Option(...)):
    """Write corrected page texts: the medoid with each span replaced by the person's decision (blank = keep)."""
    result = json.loads((consensus / "consensus.json").read_text(encoding="utf-8"))
    dec: dict[tuple[str, int], str] = {}
    with decisions.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("decision") or "").strip():
                dec[(row["page_id"], int(row["span"]))] = row["decision"]
    out.mkdir(parents=True, exist_ok=True)
    for pid, pg in result["pages"].items():
        b = pg["base_text"]; pieces = []; pos = 0   # normalised text: ſ already folded to s
        for i, s in enumerate(sorted(pg["spans"], key=lambda x: x["start"])):
            pieces.append(b[pos:s["start"]])
            pieces.append(dec.get((pid, i), b[s["start"]:s["end"]]))
            pos = s["end"]
        pieces.append(b[pos:])
        (out / f"{pid}.txt").write_text("".join(pieces) + "\n", encoding="utf-8")
        n = sum(1 for (p, _) in dec if p == pid)
        typer.echo(f"{pid}: {n} decisions applied -> {out / (pid + '.txt')}")
    (out / "README.md").write_text("# Corrected texts\n\nMedoid readings with a person's decisions from checkin.csv applied. Line breaks are not preserved (the consensus is computed on flattened text); these are candidate ground truth for scoring, not diplomatic transcriptions.\n", encoding="utf-8")


if __name__ == "__main__":
    app()
