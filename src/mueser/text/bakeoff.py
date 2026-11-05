"""Run N backends on the same pages, score each against ground truth, and write a comparison.

    uv run python -m mueser.text.bakeoff run --pages <dir> --gt <dir> --backends tesseract,openrouter --out <dir>

Every backend/page result goes to <out>/runs/<run_id>/<backend>/<model>/<page_id>.{txt,xml,json}; the summary to
<out>/bakeoff_<run_id>.csv and .json; run.json records models, prompt hash, cost and timings. Backends that cannot
run are listed as skipped with the reason, never silently dropped. Reruns hit the response cache, so they are free.
"""

from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path
from typing import Optional

import typer
from PIL import Image
from rich.console import Console
from rich.table import Table

from mueser.shared.runs import RunManifest, rel, run_id as make_run_id
from . import formats
from .backends import make
from .backends.base import Mode, PageResult
from .evaluate import score

app = typer.Typer(help="Bake off several OCR/HTR backends on the same pages.")


@app.callback()
def _root():
    """Sub-commands below."""
console = Console()

IMG_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def list_pages(pages: Path) -> list[Path]:
    return sorted(p for p in pages.iterdir() if p.suffix.lower() in IMG_EXT)


def gt_for(page: Path, gt_dir: Optional[Path]) -> Optional[str]:
    if not gt_dir:
        return None
    for ext in (".txt", ".gt.txt"):
        p = gt_dir / (page.stem + ext)
        if p.exists():
            return p.read_text(encoding="utf-8")
    xml = gt_dir / (page.stem + ".xml")
    if xml.exists():
        return "\n".join(l.text for l in formats.from_page_xml(xml))
    return None


def parse_backend_spec(spec: str) -> tuple[str, dict]:
    """'openrouter:qwen/qwen3-vl-8b-instruct' -> ('openrouter', {'model': ...}); 'tesseract' -> ('tesseract', {})."""
    if ":" in spec:
        name, model = spec.split(":", 1)
        return name, {"model": model}
    return spec, {}


def save_result(res: PageResult, page: Path, run_dir: Path) -> dict:
    model_slug = re.sub(r"[^A-Za-z0-9._-]+", "_", res.model)
    folder = run_dir / res.backend / model_slug
    folder.mkdir(parents=True, exist_ok=True)
    with Image.open(page) as im:
        w, h = im.size
    (folder / f"{res.page_id}.txt").write_text(formats.to_text(res), encoding="utf-8")
    (folder / f"{res.page_id}.xml").write_text(formats.to_page_xml(res, page.name, w, h), encoding="utf-8")
    meta = {k: v for k, v in res.to_dict().items() if k != "raw"}
    meta["raw_ref"] = res.raw.get("cache_key") if isinstance(res.raw, dict) else None
    (folder / f"{res.page_id}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"folder": rel(folder), "model_slug": model_slug}


@app.command()
def run(
    pages: Path = typer.Option(..., exists=True, file_okay=False),
    out: Path = typer.Option(..., help="output folder; runs/<run_id>/ and bakeoff_<run_id>.csv go here"),
    backends: str = typer.Option("tesseract", help="comma list; 'openrouter:<model id>' picks a model"),
    gt: Optional[Path] = typer.Option(None, help="folder of <page>.txt or <page>.xml ground truth"),
    mode: Mode = typer.Option("print"),
    lang: str = "de",
    limit: int = typer.Option(0, help="only the first N pages"),
    run_id: Optional[str] = typer.Option(None, help="reuse a run id (default: timestamp)"),
):
    rid = run_id or make_run_id()
    run_dir = out / "runs" / rid
    run_dir.mkdir(parents=True, exist_ok=True)
    page_files = list_pages(pages)[: limit or None]
    specs = [parse_backend_spec(s.strip()) for s in backends.split(",") if s.strip()]
    manifest = RunManifest(run_id=rid, step="bakeoff", params={"backends": backends, "mode": mode, "lang": lang, "pages": rel(pages), "gt": rel(gt) if gt else None})
    rows: list[dict] = []
    skipped: list[dict] = []
    t_start = time.time()
    for name, kw in specs:
        backend = make(name, **kw)
        reason = backend.check()
        if reason:
            skipped.append({"backend": name, "model": getattr(backend, "model", ""), "reason": reason})
            console.print(f"[yellow]skip[/] {name}: {reason}")
            continue
        for page in page_files:
            try:
                res = backend.transcribe(page, mode=mode, lang=lang)
            except Exception as e:  # noqa: BLE001
                rows.append({"run_id": rid, "backend": name, "model": getattr(backend, "model", ""), "page_id": page.stem, "error": str(e)[:300]})
                console.print(f"[red]error[/] {name} {page.name}: {e}")
                continue
            saved = save_result(res, page, run_dir)
            row = {"run_id": rid, "backend": res.backend, "model": res.model, "page_id": res.page_id, "lines": len(res.lines),
                   "cost_usd": res.cost_usd, "seconds": res.seconds, "cached": res.cached, "prompt_sha256": res.prompt_sha256,
                   "output": saved["folder"], "error": ""}
            gt_text = gt_for(page, gt)
            if gt_text is not None:
                s = score(gt_text, res.text)
                row.update({"cer": s.cer, "wer": s.wer, "cer_norm": s.cer_norm, "wer_norm": s.wer_norm, "gt_chars": s.gt_chars, "gt_lines": s.gt_lines})
            rows.append(row)
            manifest.cost_usd += float(res.cost_usd or 0)
            console.print(f"{res.backend:<11} {res.model:<36} {res.page_id:<8} lines={len(res.lines):<3} "
                          + (f"CER={row['cer']:.3f} CERn={row['cer_norm']:.3f} " if "cer" in row else "")
                          + f"${(res.cost_usd or 0):.4f} {res.seconds}s{' (cached)' if res.cached else ''}")
    manifest.seconds = round(time.time() - t_start, 1)
    cols = ["run_id", "backend", "model", "page_id", "lines", "cer", "wer", "cer_norm", "wer_norm", "gt_chars", "gt_lines", "cost_usd", "seconds", "cached", "prompt_sha256", "output", "error"]
    csv_path = out / f"bakeoff_{rid}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    summary = summarize(rows)
    (out / f"bakeoff_{rid}.json").write_text(json.dumps({"run_id": rid, "rows": rows, "skipped": skipped, "summary": summary, "manifest": manifest.__dict__}, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    manifest.outputs = [rel(csv_path), rel(run_dir)]
    manifest.inputs = [rel(p) for p in page_files]
    manifest.notes = [f"skipped {s['backend']}: {s['reason']}" for s in skipped]
    manifest.write(run_dir)
    print_summary(summary, skipped)
    console.print(f"\nwrote {csv_path}")


def summarize(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        if r.get("error"):
            continue
        groups.setdefault((r["backend"], r["model"]), []).append(r)
    out = []
    for (b, m), rs in groups.items():
        n = len(rs)
        scored = [r for r in rs if "cer" in r]
        mean = lambda k: round(sum(float(r[k]) for r in scored) / len(scored), 4) if scored else None  # noqa: E731
        out.append({"backend": b, "model": m, "pages": n, "scored_pages": len(scored), "cer": mean("cer"), "wer": mean("wer"),
                    "cer_norm": mean("cer_norm"), "wer_norm": mean("wer_norm"),
                    "cost_per_page": round(sum(float(r.get("cost_usd") or 0) for r in rs) / n, 5),
                    "seconds_per_page": round(sum(float(r.get("seconds") or 0) for r in rs) / n, 2)})
    return sorted(out, key=lambda x: (x["cer"] is None, x["cer"] or 0))


def print_summary(summary: list[dict], skipped: list[dict]) -> None:
    t = Table(title="Bake-off (mean over pages)")
    for c in ("backend", "model", "pages", "CER", "WER", "CER norm", "WER norm", "$/page", "s/page"):
        t.add_column(c)
    for s in summary:
        f = lambda v: "" if v is None else f"{v:.3f}"  # noqa: E731
        t.add_row(s["backend"], s["model"], str(s["pages"]), f(s["cer"]), f(s["wer"]), f(s["cer_norm"]), f(s["wer_norm"]), f"{s['cost_per_page']:.4f}", f"{s['seconds_per_page']:.1f}")
    console.print(t)
    for s in skipped:
        console.print(f"[yellow]skipped[/] {s['backend']}: {s['reason']}")


if __name__ == "__main__":
    app()
