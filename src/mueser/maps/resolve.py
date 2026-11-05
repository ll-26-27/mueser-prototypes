"""Resolve the place names in a records file against the gazetteers and write back the decisions.

    uv run python -m mueser.maps.resolve run --records records.jsonl --out <dir> [--sources gov,wikidata,whg,geonames]
        [--accept-min 0.9] [--margin 0.15] [--review <dir>/review.csv]

Writes <out>/records_resolved.jsonl (+ .csv), <out>/review.csv (every candidate for every name, with a column
for a person's choice), <out>/decisions.json (the same, for the map), and run.json. If a review.csv with
`your_choice` filled in exists, those choices are applied as status ``reviewed``. Rerunning is free: every
gazetteer response is cached.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import typer

from mueser.shared.record import read_csv, read_jsonl, write_csv, write_jsonl
from mueser.shared.runs import RunManifest, rel, run_id
from . import reconcile

app = typer.Typer(help="Resolve place names with historical gazetteers.")


@app.callback()
def _root():
    """Sub-commands below."""


@app.command()
def run(records: Path = typer.Option(..., exists=True), out: Path = typer.Option(...), sources: str = "gov,wikidata,whg,geonames",
        accept_min: float = 0.9, margin: float = 0.15, review: Optional[Path] = None,
        populous_tiebreak: bool = typer.Option(True, help="break same-name ties by population (≥5,000 and ≥10× the runner-up), recorded in the reason")):
    recs = read_jsonl(records) if records.suffix == ".jsonl" else read_csv(records)
    names = sorted({(r.normalized or r.surface_form) for r in recs if r.type == "place"})
    review_path = review or out / "review.csv"
    manual = reconcile.read_manual_choices(review_path)
    t0 = time.time()
    decisions = reconcile.resolve_names(names, sources=[s for s in sources.split(",") if s], accept_min=accept_min, margin=margin, manual=manual, populous_tiebreak=populous_tiebreak, log=typer.echo)
    recs = reconcile.apply_to_records(recs, decisions)
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(recs, out / "records_resolved.jsonl")
    write_csv(recs, out / "records_resolved.csv")
    # Keep a person's choices when rewriting the review table.
    if manual:
        reconcile.write_review(decisions, out / "review_regenerated.csv")
    else:
        reconcile.write_review(decisions, review_path)
    reconcile.save_decisions(decisions, out / "decisions.json")
    counts = {s: sum(1 for d in decisions.values() if d.status == s) for s in ("auto", "reviewed", "unresolved")}
    m = RunManifest(run_id=run_id(), step="resolve", params={"sources": sources, "accept_min": accept_min, "margin": margin, "manual_choices": len(manual), "populous_tiebreak": populous_tiebreak},
                    inputs=[rel(records)], outputs=[rel(out / "records_resolved.jsonl"), rel(review_path), rel(out / "decisions.json")],
                    seconds=round(time.time() - t0, 1), notes=[f"{len(names)} distinct names: {counts}"])
    m.write(out)
    typer.echo(f"{len(names)} names: {counts}. Review table: {review_path}")


if __name__ == "__main__":
    app()
