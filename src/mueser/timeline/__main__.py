"""Command line for the timeline: ``python -m mueser.timeline <command> --case <folder>``."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from . import case_paths

app = typer.Typer(add_completion=False, help=__doc__)
CASE = typer.Option(Path("01-use-cases/timeline/01-thinkers-and-events"), "--case", help="the use-case folder")


def _collect_run(case: Path, run: str | None) -> Path:
    from .collect import latest_run
    P = case_paths(case)
    if run:
        return P["runs"] / run
    r = latest_run(case, "collect-")
    if not r:
        raise typer.BadParameter("no collect run yet; run `collect` first")
    return r


@app.command()
def collect(case: Path = CASE, run_id: str | None = typer.Option(None, "--run-id", help="reuse an id only to redo that run after a fix")):
    """Wikidata -> nodes and recorded edges, by the rules in inputs/rules.json (written on first run)."""
    from .collect import collect as _collect
    _collect(case, rid=run_id, echo=typer.echo)


@app.command()
def sources(case: Path = CASE, run: str | None = typer.Option(None, "--run"), workers: int = typer.Option(4, "--workers")):
    """Stanford Encyclopedia entry metadata and Wikipedia summaries for every node of a collect run."""
    from .sources import fetch_sources
    fetch_sources(case, _collect_run(case, run), workers=workers, echo=typer.echo)


@app.command()
def connect(case: Path = CASE, run: str | None = typer.Option(None, "--run"),
            model: str = typer.Option("google/gemini-3.8-flash", "--model"),
            all_people: bool = typer.Option(False, "--all", help="every person, not only those with an SEP/IEP entry"),
            limit: int | None = typer.Option(None, "--limit"), workers: int = typer.Option(6, "--workers"),
            run_id: str | None = typer.Option(None, "--run-id")):
    """A model proposes typed person-to-event connections from each person's extract; skips without OPENROUTER_API_KEY."""
    from .connect import run_connect
    run_connect(case, _collect_run(case, run), model=model, only_seed=not all_people, limit=limit, workers=workers, rid=run_id,
                echo=typer.echo)


@app.command()
def db(case: Path = CASE, run: str | None = typer.Option(None, "--run"), proposals: str | None = typer.Option(None, "--proposals")):
    """Collect run + sources + latest proposals + log -> timeline.sqlite and timeline.json."""
    from .connect import latest_proposals
    from .db import build_db
    P = case_paths(case)
    prop = (P["proposals"] / proposals) if proposals else latest_proposals(case)
    build_db(case, _collect_run(case, run), prop, echo=typer.echo)


@app.command()
def build(case: Path = CASE, title: str = typer.Option("Thinkers and events", "--title")):
    """timeline.json + the log -> outputs/index.html."""
    from .build import build as _build
    _build(case, title=title, echo=typer.echo)


@app.command()
def serve(case: Path = CASE, host: str = typer.Option("127.0.0.1", "--host"), port: int = typer.Option(8767, "--port"),
          who: str = typer.Option("", "--who", help="name written on every event"), no_open: bool = typer.Option(False, "--no-open"),
          verbose: bool = typer.Option(False, "--verbose")):
    """Serve the page locally; POST /api/log appends to outputs/timeline/log.jsonl."""
    from .serve import run_forever
    from .serve import serve as _serve
    httpd, _ = _serve(case, host=host, port=port, who=who, open_browser=not no_open, quiet=not verbose)
    run_forever(httpd)


@app.command()
def ingest(case: Path = CASE):
    """Append events exported from a browser (outputs/timeline/inbox/*.jsonl) that are not yet in the log."""
    from .log import ingest as _ingest
    P = case_paths(case)
    typer.echo(json.dumps(_ingest(P["inbox"], P["log"])))


@app.command()
def log(case: Path = CASE, type: str | None = typer.Option(None, "--type")):
    """Print the log, one event per line."""
    from .log import read
    for e in read(case_paths(case)["log"]):
        if type and e.type != type:
            continue
        a = e.anchor
        where = (a.node or a.edge or "") if a else ""
        typer.echo(f"{e.ts}  {e.who:<10} {e.type:<9} {where:<40} {json.dumps(e.body, ensure_ascii=False)[:100]}")


@app.command()
def query(case: Path = CASE, sql: str = typer.Argument(..., help="a SELECT against timeline.sqlite")):
    """Run one SQL query against the database and print the rows."""
    import sqlite3
    con = sqlite3.connect(case_paths(case)["db"])
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    typer.echo("\t".join(cols))
    for row in cur.fetchall():
        typer.echo("\t".join("" if v is None else str(v) for v in row))


if __name__ == "__main__":
    app()
