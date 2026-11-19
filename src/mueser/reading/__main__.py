"""python -m mueser.reading: the reading room's commands. Run from the repository root."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from . import case_paths
from .build import build as build_page
from .cite import citation
from .log import ingest as ingest_logs
from .log import read as read_log
from .settle import apply_build, build_settled, load_build
from .translate import DEFAULT_MODELS, run_translation

app = typer.Typer(help="The reading room: scan, settled transcription and translation on one page, with a log.", no_args_is_help=True)
CASE = typer.Option(..., "--case", exists=True, file_okay=False, help="the use-case folder (inputs/, operations/, outputs/)")


@app.callback()
def _root():
    """Sub-commands below."""


@app.command()
def settle(case: Path = CASE, build_id: str | None = typer.Option(None, help="default b-<timestamp>"),
           pages: str | None = typer.Option(None, help="comma-separated page ids; default all in inputs/readings/consensus"),
           max_dist: float = typer.Option(0.55, help="a line pairing above this normalised distance is left unanchored"),
           anchor: bool = typer.Option(True, help="align lines to inputs/readings/segmentation/<page>.json when present")):
    """Medoid lines + remapped consensus spans + anchors -> an immutable build under outputs/reading/builds/."""
    out = build_settled(case, pages=pages.split(",") if pages else None, build_id=build_id, max_dist=max_dist, anchor=anchor)
    settled = json.loads((out / "settled.json").read_text(encoding="utf-8"))
    for pid, pg in settled["pages"].items():
        a = pg.get("anchors") or {}
        n_sp = sum(len(l["spans"]) for l in pg["lines"])
        typer.echo(f"{pid:42} lines={len(pg['lines']):3} spans={n_sp:3} medoid={pg['diplomatic']['reader']}"
                   + (f" anchored={a.get('matched', 0) + a.get('merged', 0) + a.get('split', 0)}/{len(pg['lines'])} unanchored={a.get('unanchored')} conf={a.get('mean_confidence')}" if a else " (no segmentation)"))
    typer.echo(f"build {settled['build_id']} -> {out}")


@app.command()
def translate(case: Path = CASE, build_id: str | None = typer.Option(None, help="default: latest build"),
              models: str = typer.Option(",".join(DEFAULT_MODELS), help="two OpenRouter model ids, comma-separated"),
              min_divergence: float = typer.Option(0.35, help="a block whose two translations are at least this far apart is on the check-in list"),
              pages: str | None = typer.Option(None), run_id: str | None = typer.Option(None)):
    """Translate the settled lines of each page with two models; align into blocks; mark divergence. Needs OPENROUTER_API_KEY."""
    out = run_translation(case, build_id=build_id, models=[m.strip() for m in models.split(",") if m.strip()],
                          min_divergence=min_divergence, pages=pages.split(",") if pages else None, run_id=run_id)
    man = json.loads((out / "run.json").read_text(encoding="utf-8"))
    typer.echo(f"run {man['run_id']}: ${man['cost_usd']:.4f}, {man['seconds']}s" + (f"; notes: {man['notes']}" if man["notes"] else ""))


@app.command()
def build(case: Path = CASE, build_id: str | None = typer.Option(None, help="default: latest build"),
          translation: str | None = typer.Option(None, help="translation run id; default latest; 'none' for no translation"),
          title: str = typer.Option("Reading room")):
    """Build + translation + log -> outputs/index.html (self-contained) and outputs/reading/reading.json."""
    out = build_page(case, build_id=build_id, translation_run=translation, title=title)
    typer.echo(f"-> {out}")


@app.command()
def serve(case: Path = CASE, port: int = typer.Option(8765), host: str = typer.Option("127.0.0.1"),
          who: str = typer.Option("", help="default author written on events made in the page"),
          no_browser: bool = typer.Option(False, "--no-browser"), verbose: bool = typer.Option(False, "--verbose")):
    """Serve the case folder on 127.0.0.1 and append events POSTed by the page to outputs/reading/log.jsonl."""
    from .serve import run_forever
    run_forever(case, host=host, port=port, who=who, open_browser=not no_browser, quiet=not verbose)


@app.command()
def apply(case: Path = CASE, build_id: str | None = typer.Option(None, help="the build to apply decisions to; default latest"),
          translation: str | None = typer.Option(None, help="translation run whose block decisions to resolve; default latest"),
          new_build_id: str | None = typer.Option(None)):
    """Read the log, apply the latest decision per target, write a new build. Then run build."""
    from .translate import latest_translation_run
    if translation is None:
        t = latest_translation_run(case)
        translation = t.name if t else None
    out = apply_build(case, build_id=build_id, translation_run=translation, new_build_id=new_build_id)
    settled = json.loads((out / "settled.json").read_text(encoding="utf-8"))
    typer.echo(f"{len(settled['decisions_applied'])} decisions applied -> build {settled['build_id']} ({out})")
    for d in settled["decisions_applied"]:
        typer.echo(f"  {d['target']}  by {d['who'] or '?'} at {d['ts']}")


@app.command()
def ingest(case: Path = CASE):
    """Append events from exported browser logs in outputs/reading/inbox/ that are not yet in the log."""
    P = case_paths(case)
    P["inbox"].mkdir(parents=True, exist_ok=True)
    rep = ingest_logs(P["inbox"], P["log"])
    if not rep:
        typer.echo(f"nothing in {P['inbox']}")
    for f, c in rep.items():
        typer.echo(f"{f}: {c['added']} added, {c['duplicate']} already present, {c['invalid']} invalid")


@app.command("log")
def log_show(case: Path = CASE, type: str | None = typer.Option(None, help="filter by event type")):
    """Print the log, one event per line."""
    P = case_paths(case)
    for e in read_log(P["log"]):
        if type and e.type != type:
            continue
        a = e.anchor
        where = f"{a.page} {' '.join(a.lines)}" if a else ""
        typer.echo(f"{e.ts} {e.type:9} {e.who or '-':10} {where:60} {json.dumps(e.body, ensure_ascii=False)[:140]}")


@app.command()
def cite(case: Path = CASE, page: str = typer.Option(...), lines: str = typer.Option(..., help="e.g. l2-l4 or l2,l3"),
         format: str = typer.Option("plain", help="plain | markdown | csl"), build_id: str | None = None):
    """A citation for a line range of a page, as the page produces it."""
    P = case_paths(case)
    _, settled = load_build(case, build_id)
    meta = json.loads(P["metadata"].read_text(encoding="utf-8")) if P["metadata"].exists() else {"docs": {}}
    pg = settled["pages"][page]
    if "-" in lines:
        a, b = lines.split("-", 1)
        ids = [f"l{i}" for i in range(int(a[1:]), int(b[1:]) + 1)]
    else:
        ids = [x.strip() for x in lines.split(",")]
    quote = "\n".join(l["settled"] for l in pg["lines"] if l["line_id"] in ids)
    prov = {"transcription": {"reader": pg["diplomatic"]["reader"], "run_id": pg["diplomatic"]["run_id"], "build_id": settled["build_id"],
                              "decisions": sum(1 for l in pg["lines"] if l["line_id"] in ids for sp in l["spans"] if sp.get("status") == "decided" and sp["piece"] == 0)}}
    c = citation(meta, pg["doc_id"], page, ids, quote=quote, provenance=prov)
    typer.echo(c["csl_json"] if format == "csl" else c[format])


@app.command()
def collect(case: Path = CASE, consensus: Path = typer.Option(..., exists=True, help="a consensus.json written by mueser.text.compare run"),
            runs: Path = typer.Option(..., exists=True, help="the outputs/runs/<run_id> folder those readings came from"),
            pages: Path = typer.Option(..., exists=True, help="the folder with the page images"),
            segmentation: str = typer.Option("hybrid:*", help="reader key (backend:model) whose lines carry boxes; 'hybrid:*' or 'kraken:*' take the first found"),
            only: str | None = typer.Option(None, help="comma-separated page ids; default every page in the consensus")):
    """Bring a consensus, its medoid readings, a boxed reading and the page images into this case's inputs/, with provenance."""
    import hashlib
    import shutil
    import time

    from mueser.shared.runs import rel
    P = case_paths(case)
    cons = json.loads(consensus.read_text(encoding="utf-8"))
    for d in ("pages", "consensus", "medoid", "segmentation"):
        (P[d] if d != "pages" else P["pages"]).mkdir(parents=True, exist_ok=True)
    prov_path = P["case"] / "inputs" / "readings" / "provenance.json"
    prov = json.loads(prov_path.read_text(encoding="utf-8")) if prov_path.exists() else {"files": {}}
    prov["collected_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    wanted = set(only.split(",")) if only else set(cons["pages"])
    for pid, pg in cons["pages"].items():
        if pid not in wanted:
            continue
        img = next((p for p in pages.glob(f"{pid}.*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".tif", ".tiff")), None)
        if img is None:
            typer.echo(f"{pid}: no image in {pages}, skipped"); continue
        shutil.copy2(img, P["pages"] / img.name)
        prov["files"][f"inputs/pages/{img.name}"] = {"role": "page image", "from": rel(img), "sha256": sha(img)}
        slice_ = {"page_id": pid, "run_id": cons["run_id"], "min_weight": cons["min_weight"], "page": pg, "from": rel(consensus), "from_sha256": sha(consensus)}
        (P["consensus"] / f"{pid}.consensus.json").write_text(json.dumps(slice_, ensure_ascii=False, indent=1), encoding="utf-8")
        prov["files"][f"inputs/readings/consensus/{pid}.consensus.json"] = {"role": "consensus (per-page slice)", "from": rel(consensus), "sha256": sha(consensus)}
        backend, model = pg["medoid"]["overall"].split(":", 1)
        med = runs / backend / model.replace("/", "_") / f"{pid}.json"
        if not med.exists():
            typer.echo(f"{pid}: medoid run JSON missing at {med}, skipped"); continue
        shutil.copy2(med, P["medoid"] / f"{pid}.json")
        prov["files"][f"inputs/readings/medoid/{pid}.json"] = {"role": f"medoid reading {pg['medoid']['overall']}", "from": rel(med), "sha256": sha(med)}
        sb, sm = segmentation.split(":", 1)
        cands = sorted((runs / sb).glob(f"*/{pid}.json")) if sm == "*" else [runs / sb / sm.replace("/", "_") / f"{pid}.json"]
        seg = next((c for c in cands if c.exists()), None)
        if seg:
            shutil.copy2(seg, P["segmentation"] / f"{pid}.json")
            prov["files"][f"inputs/readings/segmentation/{pid}.json"] = {"role": f"segmentation with boxes {sb}:{seg.parent.name}", "from": rel(seg), "sha256": sha(seg)}
        typer.echo(f"{pid}: medoid {pg['medoid']['overall']}, {len(pg['spans'])} spans, segmentation {'from ' + rel(seg) if seg else 'none (lines will be unanchored)'}")
    prov_path.parent.mkdir(parents=True, exist_ok=True)
    prov_path.write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
    typer.echo(f"provenance -> {prov_path}")


@app.command("init-doc")
def init_doc(pages: Path = typer.Option(..., exists=True, help="a folder written by mueser.text.ingest (has pages.json)"),
             out: Path = typer.Option(..., help="inputs/metadata.json to create or extend"),
             doc_type: str = typer.Option("book", help="CSL type: book, manuscript, personal_communication, article-newspaper")):
    """A metadata.json skeleton for a document ingested with mueser.text.ingest; fill the bibliographic fields by hand."""
    pj = json.loads((pages / "pages.json").read_text(encoding="utf-8"))
    meta = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"docs": {}}
    doc_id = pj.get("doc_id") or pages.name
    entry = meta["docs"].get(doc_id) or {"type": doc_type, "title": "", "author": [], "date": "", "place": None, "publisher": None,
                                         "archive": None, "shelfmark": None, "url": None, "iiif_manifest": None, "licence": None,
                                         "language": "de", "synthetic": False, "pages": {}}
    src = pj.get("source") or {}
    if isinstance(src, dict) and src.get("manifest"):
        entry["iiif_manifest"] = src["manifest"]
    for p in pj.get("pages", []):
        entry["pages"].setdefault(p["page_id"], {"label": p.get("label") or p["page_id"], "iiif_canvas": p.get("iiif_canvas"), "image_sha256": p.get("sha256")})
    meta["docs"][doc_id] = entry
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    typer.echo(f"{doc_id}: {len(entry['pages'])} pages -> {out} (fill title, author, date, place, publisher, archive, licence)")


if __name__ == "__main__":
    app()
