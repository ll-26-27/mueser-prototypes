"""Command line for the style tools: ``python -m mueser.style {cv,journal} <command>``. Run from the repository root."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(add_completion=False, help=__doc__)
cv = typer.Typer(add_completion=False, help="Add entries to a CV without disturbing its layout.")
journal = typer.Typer(add_completion=False, help="Bring an article to a journal's house style, one decided change at a time.")
app.add_typer(cv, name="cv")
app.add_typer(journal, name="journal")

CV_CASE = Path("01-use-cases/style/02-cv")
J_CASE = Path("01-use-cases/style/04-journal-style")
RUN_ID = typer.Option(None, "--run-id", help="reuse an id only to redo that run after a fix")


@cv.command("extract")
def cv_extract(source: Path = typer.Argument(..., help="the CV as .docx"),
               out: Path = typer.Option(CV_CASE / "inputs/config/cv.yml", "--out")):
    """Write the CV as data (sections, entries, format fingerprints) and report its page geometry."""
    from .cv.extract import extract
    extract(source, out, echo=typer.echo)


@cv.command("render")
def cv_render(cv_yml: Path = typer.Option(CV_CASE / "inputs/config/cv.yml", "--cv"), source: Path = typer.Option(..., "--source"),
              out: Path = typer.Option(CV_CASE / "outputs/out", "--out"), run_id: str | None = RUN_ID):
    """Write a copy of the CV with the entries added or reworded in cv.yml."""
    from .cv.render import render
    render(cv_yml, source, out, rid=run_id, echo=typer.echo)


@cv.command("check")
def cv_check(before: Path = typer.Option(..., "--before"), after: Path = typer.Option(..., "--after")):
    """Page count before and after, and the first page that differs. Exits with status 2 if the CV grew."""
    from .cv.check import check
    raise typer.Exit(check(before, after, echo=typer.echo))


@journal.command("profile")
def journal_profile(samples: list[Path] = typer.Argument(..., help="recent articles from the journal: .pdf, .docx or .txt"),
                    name: str = typer.Option(..., "--name", help="the journal's name"),
                    out: Path = typer.Option(None, "--out", help="default: inputs/config/<name>.yml in the case folder"),
                    threshold: float = typer.Option(0.8, "--threshold", help="share of hits a variant needs to count as the journal's"),
                    citations: bool = typer.Option(False, "--citations", help="ask a model for example citations (needs OPENROUTER_API_KEY)"),
                    model: str = typer.Option(None, "--model")):
    """Count the journal's conventions in sample articles and write them as a profile."""
    from .journal import MODEL
    from .journal.profile import profile
    slug = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    profile(samples, out or J_CASE / "inputs/config" / f"{slug}.yml", name, threshold, citations, model or MODEL, echo=typer.echo)


@journal.command("check")
def journal_check(article: Path = typer.Argument(..., help="the draft as .docx"), profile: Path = typer.Option(..., "--profile"),
                  out: Path = typer.Option(J_CASE / "outputs/out", "--out"),
                  citations: bool = typer.Option(False, "--citations", help="have a model restyle the footnotes after the journal's examples"),
                  model: str = typer.Option(None, "--model"), run_id: str | None = RUN_ID):
    """List every place the draft departs from the profile (review.csv and report.html). Changes nothing."""
    from .journal import MODEL
    from .journal.check import check
    from .journal.report import report
    folder = check(article, profile, out, citations, model or MODEL, rid=run_id, echo=typer.echo)
    report(folder, echo=typer.echo)


@journal.command("decide")
def journal_decide(run: Path = typer.Option(..., "--run", help="the check run folder"), who: str = typer.Option(..., "--who"),
                   rule: list[str] = typer.Option([], "--rule"), finding: list[str] = typer.Option([], "--id"),
                   accept: bool = typer.Option(None, "--accept/--reject")):
    """Record a decision on all proposals of a rule, or on single findings, then refresh the report."""
    from .journal.check import decide
    from .journal.report import report
    if accept is None or not (rule or finding):
        raise typer.BadParameter("give --accept or --reject, and at least one --rule or --id")
    decide(run, who, accept, rule, finding, echo=typer.echo)
    report(run, echo=typer.echo)


@journal.command("report")
def journal_report(run: Path = typer.Option(..., "--run")):
    """Rebuild report.html from review.csv."""
    from .journal.report import report
    report(run, echo=typer.echo)


@journal.command("apply")
def journal_apply(source: Path = typer.Option(..., "--source", help="the same draft the check was run on"),
                  run: Path = typer.Option(..., "--run", help="the check run folder"),
                  out: Path = typer.Option(J_CASE / "outputs/out", "--out"), run_id: str | None = RUN_ID):
    """Write the accepted rows into a copy of the draft, with a diff."""
    from .journal.apply import apply
    apply(source, run, out, rid=run_id, echo=typer.echo)


if __name__ == "__main__":
    app()
