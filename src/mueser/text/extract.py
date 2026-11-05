"""From transcription to records: find place / person / date / organisation mentions and emit shared Records.

Two methods, both keeping the verbatim surface form and the line it came from:
  - ``llm``: a model through OpenRouter, constrained to a JSON schema, one page at a time (default).
  - ``ner``: a historical-German NER model (dbmdz hmBERT / Flair) if installed (``uv sync --extra ner``).

    uv run python -m mueser.text.extract run --transcripts <dir of page .txt> --doc-id <id> --out records.jsonl

Each record's ``source.transcription_backend`` is read from the sidecar <page>.json the bake-off wrote, if present.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import typer

from mueser.shared import env
from mueser.shared.cache import sha256_text
from mueser.shared.openrouter import MissingCredential, chat
from mueser.shared.record import Record, Source, write_csv, write_jsonl

app = typer.Typer(help="Extract place/person/date/org mentions from transcriptions as shared Records.")


@app.callback()
def _root():
    """Sub-commands below."""

PROMPT_PATH = Path(__file__).parent / "backends" / "prompts" / "extract_de.md"

SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["mentions"],
    "properties": {"mentions": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["surface_form", "normalized", "type", "line_index", "date_start", "date_end", "note"],
        "properties": {
            "surface_form": {"type": "string"},
            "normalized": {"type": ["string", "null"]},
            "type": {"type": "string", "enum": ["place", "person", "event", "org", "other"]},
            "line_index": {"type": "integer"},
            "date_start": {"type": ["string", "null"]},
            "date_end": {"type": ["string", "null"]},
            "note": {"type": "string"},
        }}}},
}


def load_prompt() -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    m = re.search(r"<!-- PROMPT START -->\s*(.*?)\s*<!-- PROMPT END -->", text, re.S)
    return (m.group(1) if m else text).strip()


def numbered(lines: list[str]) -> str:
    return "\n".join(f"{i}: {l}" for i, l in enumerate(lines))


def verify_surface(lines: list[str], m: dict) -> tuple[bool, Optional[int]]:
    """A mention counts only if its surface_form occurs verbatim on the page; fix the line index if the model's is off."""
    sf = m["surface_form"]
    li = m.get("line_index")
    if isinstance(li, int) and 0 <= li < len(lines) and sf in lines[li]:
        return True, li
    for i, l in enumerate(lines):
        if sf in l:
            return True, i
    return False, None


def extract_page_llm(lines: list[str], *, model: str, doc_id: str, page_id: str, backend_tag: Optional[str], page_date: Optional[str]) -> tuple[list[Record], list[dict]]:
    system = load_prompt()
    user = f"Document: {doc_id}, page {page_id}." + (f" The page's own date context: {page_date}." if page_date else "") + "\n\nLines:\n" + numbered(lines)
    res = chat(model=model, system=system, user_text=user, schema=SCHEMA, schema_name="mentions", step="extract", max_tokens=6000)
    mentions = (res.get("parsed") or {}).get("mentions", [])
    out, rejected = [], []
    for m in mentions:
        ok, li = verify_surface(lines, m)
        if not ok:
            rejected.append(m)
            continue
        src = Source(doc_id=doc_id, page_id=page_id, line_index=li, transcription_backend=backend_tag, extraction_method=f"llm/{res.get('model') or model}")
        out.append(Record.new(type=m["type"], surface_form=m["surface_form"], source=src, normalized=m.get("normalized"),
                              date_start=m.get("date_start"), date_end=m.get("date_end"), notes=m.get("note") or None))
    return out, rejected


@app.command()
def run(transcripts: Path = typer.Option(..., exists=True), doc_id: str = typer.Option(...), out: Path = typer.Option(...),
        model: Optional[str] = None, page_date: Optional[str] = typer.Option(None, help="EDTF date for the whole document, if known"),
        limit: int = 0):
    model = model or env.get("EXTRACT_MODEL", "anthropic/claude-haiku-4.5")
    pages = sorted(transcripts.glob("*.txt"))[: limit or None]
    records: list[Record] = []
    report = {"model": model, "prompt_sha256": sha256_text(load_prompt()), "pages": []}
    for p in pages:
        lines = [l.rstrip("\n") for l in p.read_text(encoding="utf-8").splitlines()]
        side = p.with_suffix(".json")
        backend_tag = None
        if side.exists():
            meta = json.loads(side.read_text(encoding="utf-8"))
            backend_tag = f"{meta.get('backend')}/{meta.get('model')}"
        try:
            recs, rejected = extract_page_llm(lines, model=model, doc_id=doc_id, page_id=p.stem, backend_tag=backend_tag, page_date=page_date)
        except MissingCredential as e:
            typer.echo(f"skip: {e}")
            raise typer.Exit(1)
        records.extend(recs)
        report["pages"].append({"page_id": p.stem, "mentions": len(recs), "rejected_not_verbatim": rejected})
        typer.echo(f"{p.stem}: {len(recs)} mentions" + (f", {len(rejected)} rejected (not verbatim on page)" if rejected else ""))
    n = write_jsonl(records, out)
    write_csv(records, out.with_suffix(".csv"))
    out.with_name(out.stem + "_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    typer.echo(f"{n} records -> {out} (+ .csv, _report.json)")


if __name__ == "__main__":
    app()
