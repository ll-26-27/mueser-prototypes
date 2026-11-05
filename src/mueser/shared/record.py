"""The shared Record model: one mention of a place/person/event/org in one source, with provenance.

Validated against shared/schema/record.schema.json (the JSON Schema is the contract; this model mirrors it
and adds helpers). Dates are kept as EDTF-tolerant text; sortable years are derived.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mueser import REPO_ROOT

SCHEMA_PATH = REPO_ROOT / "shared" / "schema" / "record.schema.json"

RecordType = Literal["place", "person", "event", "org", "other"]
ResolutionStatus = Literal["auto", "reviewed", "unresolved"]


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")
    doc_id: str
    page_id: str
    line_index: Optional[int] = None
    bbox: Optional[list[float]] = Field(default=None, min_length=4, max_length=4)
    iiif_canvas: Optional[str] = None
    transcription_backend: Optional[str] = None
    extraction_method: Optional[str] = None


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    type: RecordType
    surface_form: str
    normalized: Optional[str] = None
    source: Source
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    place_uri: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    resolution_status: ResolutionStatus = "unresolved"
    resolution_source: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _derive_years(self) -> "Record":
        if self.year_start is None and self.date_start:
            ys, ye = parse_edtf_years(self.date_start)
            self.year_start = ys
            if self.year_end is None and not self.date_end:
                self.year_end = ye
        if self.year_end is None and self.date_end:
            _, ye = parse_edtf_years(self.date_end)
            self.year_end = ye
        return self

    @classmethod
    def new(cls, *, type: RecordType, surface_form: str, source: Source, **kw) -> "Record":
        rid = stable_id(source.doc_id, source.page_id, source.line_index, surface_form, type)
        return cls(id=rid, type=type, surface_form=surface_form, source=source, **kw)

    def to_flat(self) -> dict:
        """One flat dict for CSV / DuckDB, with source.* columns prefixed."""
        d = self.model_dump()
        src = d.pop("source")
        for k, v in src.items():
            d[f"source_{k}"] = json.dumps(v) if isinstance(v, list) else v
        return d

    @classmethod
    def from_flat(cls, row: dict) -> "Record":
        row = {k: (None if v == "" else v) for k, v in row.items()}
        src = {}
        for k in list(row):
            if k.startswith("source_"):
                v = row.pop(k)
                if k == "source_bbox" and isinstance(v, str):
                    v = json.loads(v)
                if k == "source_line_index" and v is not None:
                    v = int(v)
                src[k[len("source_"):]] = v
        for k in ("lat", "lon", "confidence"):
            if row.get(k) is not None:
                row[k] = float(row[k])
        for k in ("year_start", "year_end"):
            if row.get(k) is not None:
                row[k] = int(row[k])
        return cls(source=Source(**src), **row)


def stable_id(doc_id: str, page_id: str, line_index: Optional[int], surface_form: str, type: str) -> str:
    key = json.dumps([doc_id, page_id, line_index, surface_form, type], ensure_ascii=False)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


_EDTF_YEAR = re.compile(r"^(\d{1,3}X{1,3}|-?\d{1,4})")


def parse_edtf_years(text: str) -> tuple[Optional[int], Optional[int]]:
    """Derive (start_year, end_year) from an ISO-8601 / EDTF-ish string.

    '1743' -> (1743, 1743); '1743-05-02' -> (1743, 1743); '1743~' / '1743?' -> (1743, 1743);
    '174X' -> (1740, 1749); '17XX' -> (1700, 1799); '1743/1745' -> (1743, 1745);
    '[1743,1745]' -> (1743, 1745); '..1745' -> (None, 1745); '1743..' -> (1743, None).
    Anything unparseable -> (None, None).
    """
    if not text:
        return None, None
    s = text.strip().strip("[]{}")
    if "/" in s:
        a, b = s.split("/", 1)
        return parse_edtf_years(a)[0], parse_edtf_years(b)[1]
    if "," in s:
        parts = [p for p in (x.strip() for x in s.split(",")) if p]
        years = [parse_edtf_years(p) for p in parts]
        starts = [y[0] for y in years if y[0] is not None]
        ends = [y[1] for y in years if y[1] is not None]
        return (min(starts) if starts else None, max(ends) if ends else None)
    if s.startswith(".."):
        return None, parse_edtf_years(s[2:])[1]
    if s.endswith(".."):
        return parse_edtf_years(s[:-2])[0], None
    m = _EDTF_YEAR.match(s)
    if not m:
        return None, None
    tok = m.group(1)
    if "X" in tok:
        n = tok.count("X")
        base = int(tok.replace("X", "0"))
        return base, base + 10**n - 1
    y = int(tok)
    return y, y


# ---- IO ---------------------------------------------------------------------------------------

def write_jsonl(records: Iterable[Record], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")
            n += 1
    return n


def read_jsonl(path: Path) -> list[Record]:
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(Record.model_validate_json(line))
    return out


FLAT_COLUMNS = [
    "id", "type", "surface_form", "normalized",
    "source_doc_id", "source_page_id", "source_line_index", "source_bbox", "source_iiif_canvas",
    "source_transcription_backend", "source_extraction_method",
    "date_start", "date_end", "year_start", "year_end",
    "place_uri", "lat", "lon", "resolution_status", "resolution_source", "confidence", "notes",
]


def write_csv(records: Iterable[Record], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FLAT_COLUMNS)
        w.writeheader()
        for r in records:
            w.writerow({k: ("" if v is None else v) for k, v in r.to_flat().items()})
            n += 1
    return n


def read_csv(path: Path) -> list[Record]:
    with path.open(encoding="utf-8", newline="") as f:
        return [Record.from_flat(row) for row in csv.DictReader(f)]


def validate_against_schema(record: Record | dict) -> None:
    """Raise jsonschema.ValidationError if the record does not satisfy shared/schema/record.schema.json."""
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    data = record.model_dump() if isinstance(record, Record) else record
    jsonschema.validate(data, schema)
