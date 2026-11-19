"""The append-only log: every decision, question, issue, comment and excerpt a person makes in the reading room.

One JSON object per line in ``outputs/reading/log.jsonl``. Nothing rewrites it: a mistake is corrected by a later
event, a status change is an event that references the issue, and ``apply`` takes the latest decision per target.
Events made in a browser that could not reach the server arrive as exported files in ``outputs/reading/inbox/``
and are appended by ``ingest``, skipping ids already present.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EventType = Literal["highlight", "comment", "issue", "question", "decision", "status", "excerpt"]
Layer = Literal["transcription", "translation"]


class Pos(BaseModel):
    model_config = ConfigDict(extra="forbid")
    line: str
    char: int = Field(ge=0)


class Anchor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    doc: str
    page: str
    layer: Layer = "transcription"
    lines: list[str] = Field(default_factory=list)
    segment: str | None = None
    block: str | None = None
    start: Pos | None = None
    end: Pos | None = None
    quote: str = ""


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    ts: str
    who: str = ""
    client: str = ""
    build_id: str | None = None
    type: EventType
    anchor: Anchor | None = None
    body: dict = Field(default_factory=dict)
    ref: str | None = None


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def new_id() -> str:
    return f"evt_{uuid.uuid4().hex}"


def make(type: EventType, *, who: str = "", build_id: str | None = None, anchor: Anchor | dict | None = None,
         body: dict | None = None, ref: str | None = None, client: str = "mueser.reading") -> Event:
    if isinstance(anchor, dict):
        anchor = Anchor(**anchor)
    return Event(id=new_id(), ts=now(), who=who, client=client, build_id=build_id, type=type, anchor=anchor,
                 body=body or {}, ref=ref)


def read(path: Path) -> list[Event]:
    path = Path(path)
    if not path.exists():
        return []
    events: list[Event] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(Event(**json.loads(line)))
        except Exception as e:
            raise ValueError(f"{path}:{n}: not a valid event: {e}") from e
    return events


def append(path: Path, event: Event) -> str:
    """Append one event and return the exact line written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event.model_dump(exclude_none=False), ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    return line


def ids(path: Path) -> set[str]:
    return {e.id for e in read(path)}


def ingest(inbox: Path, log: Path) -> dict:
    """Append every event in ``inbox/*.jsonl`` whose id is not yet in the log. Returns counts per file."""
    seen = ids(log)
    report: dict[str, dict] = {}
    for f in sorted(Path(inbox).glob("*.jsonl")):
        added = dup = bad = 0
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                ev = Event(**json.loads(line))
            except Exception:  # noqa: BLE001
                bad += 1
                continue
            if ev.id in seen:
                dup += 1
                continue
            append(log, ev)
            seen.add(ev.id)
            added += 1
        report[f.name] = {"added": added, "duplicate": dup, "invalid": bad}
    return report


def latest_decisions(events: list[Event]) -> dict[str, Event]:
    """The last decision per target (``span:<page>:<id>``, ``line:<page>:<id>``, ``block:<page>:<id>``), by ts then order."""
    out: dict[str, Event] = {}
    for ev in sorted((e for e in events if e.type == "decision" and e.body.get("target")), key=lambda e: e.ts):
        out[ev.body["target"]] = ev
    return out


def current_status(events: list[Event]) -> dict[str, str]:
    """Status per issue/question/comment id: ``open`` unless a later status event says otherwise."""
    status: dict[str, str] = {e.id: "open" for e in events if e.type in ("issue", "question", "comment")}
    for ev in sorted((e for e in events if e.type == "status" and e.body.get("target")), key=lambda e: e.ts):
        if ev.body["target"] in status:
            status[ev.body["target"]] = ev.body.get("status", "open")
    return status
