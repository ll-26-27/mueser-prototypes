"""Step 3 (deterministic code): turn the mention list into shared Records, keeping only mentions that occur
verbatim on the stated line of the transcription, and write the rejected ones to a report.

    uv run python 01-use-cases/maps/03-from-page-to-map/operations/03-records-from-mentions.py

Reads operations/02-mentions.json (model judgment, recorded there) and inputs/<page>.txt (Kraken output).
Writes operations/work/03-records.jsonl (+ .csv) and operations/work/03-report.json. Each record's
source.transcription_backend and source.extraction_method say exactly where it came from. This is the same
check `mueser.text.extract` applies to API output; the mention list here was produced in session instead.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mueser.shared.record import Record, Source, write_csv, write_jsonl  # noqa: E402

MENTIONS = HERE / "02-mentions.json"
INPUTS = HERE.parent / "inputs"
WORK = HERE / "work"


def main() -> None:
    m = json.loads(MENTIONS.read_text(encoding="utf-8"))
    records: list[Record] = []
    report = {"method": m["method"], "pages": {}}
    for page_id, mentions in m["pages"].items():
        lines = [l.rstrip("\n") for l in (INPUTS / f"{page_id}.txt").read_text(encoding="utf-8").splitlines()]
        side = INPUTS / f"{page_id}.json"
        backend_tag = m["transcription_backend"]
        if side.exists():
            meta = json.loads(side.read_text(encoding="utf-8"))
            backend_tag = f"{meta.get('backend')}/{meta.get('model')}"
        kept, rejected = 0, []
        for x in mentions:
            li = x["line_index"]
            if not (0 <= li < len(lines)) or x["surface_form"] not in lines[li]:
                rejected.append({**x, "reason": f"not found verbatim on line {li}"})
                continue
            src = Source(doc_id=m["doc_id"], page_id=page_id, line_index=li, transcription_backend=backend_tag,
                         extraction_method="in-session/claude-fable-5-1")
            records.append(Record.new(type=x["type"], surface_form=x["surface_form"], source=src, normalized=x.get("normalized"),
                                      date_start=x.get("date_start") or m.get("document_date"), date_end=x.get("date_end"),
                                      notes=x.get("note") or None))
            kept += 1
        report["pages"][page_id] = {"lines": len(lines), "mentions": len(mentions), "kept": kept, "rejected": rejected}
        print(f"{page_id}: {kept} of {len(mentions)} mentions verified on their lines" + (f"; rejected: {[r['surface_form'] for r in rejected]}" if rejected else ""))
    WORK.mkdir(parents=True, exist_ok=True)
    n = write_jsonl(records, WORK / "03-records.jsonl")
    write_csv(records, WORK / "03-records.csv")
    (WORK / "03-report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    by_type = {}
    for r in records:
        by_type[r.type] = by_type.get(r.type, 0) + 1
    print(f"{n} records -> {WORK / '03-records.jsonl'}  {by_type}")


if __name__ == "__main__":
    main()
