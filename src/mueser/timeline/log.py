"""The append-only log of what a person does in the timeline page.

One JSON object per line in ``outputs/timeline/log.jsonl``: a decision on a proposed connection (accept or
reject), a connection the person adds themselves, an issue, a question or a comment on a node or an edge, and
every excerpt copied with its citation. Nothing rewrites the log; ``build`` derives the current status of every
edge from the latest decision that names it. Events made in a browser that could not reach the server arrive as
exported files in ``outputs/timeline/inbox/`` and are appended by ``ingest``, skipping ids already present.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EventType = Literal["comment", "issue", "question", "decision", "status", "excerpt", "edge"]


class Anchor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    node: str | None = None
    edge: str | None = None
    field: str | None = None
    quote: str = ""


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    ts: str
    who: str = ""
    client: str = ""
    data_id: str | None = None
    type: EventType
    anchor: Anchor | None = None
    body: dict = Field(default_factory=dict)
    ref: str | None = None


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def new_id() -> str:
    return f"evt_{uuid.uuid4().hex}"


def make(type: EventType, *, who: str = "", data_id: str | None = None, anchor: Anchor | dict | None = None,
         body: dict | None = None, ref: str | None = None, client: str = "mueser.timeline") -> Event:
    if isinstance(anchor, dict):
        anchor = Anchor(**anchor)
    return Event(id=new_id(), ts=now(), who=who, client=client, data_id=data_id, type=type, anchor=anchor,
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
            events.append(Event.model_validate_json(line))
        except Exception as e:  # noqa: BLE001
            raise ValueError(f"{path}:{n}: {e}") from e
    return events


def ids(path: Path) -> set[str]:
    return {e.id for e in read(path)}


def append(path: Path, event: Event) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = event.model_dump_json(exclude_none=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    return line


def ingest(inbox: Path, log: Path) -> dict[str, int]:
    """Append every event from ``inbox/*.jsonl`` whose id is not yet in the log."""
    seen = ids(log)
    counts = {"added": 0, "duplicate": 0, "invalid": 0, "files": 0}
    for f in sorted(Path(inbox).glob("*.jsonl")):
        counts["files"] += 1
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = Event.model_validate_json(line)
            except Exception:  # noqa: BLE001
                counts["invalid"] += 1
                continue
            if ev.id in seen:
                counts["duplicate"] += 1
                continue
            append(log, ev)
            seen.add(ev.id)
            counts["added"] += 1
    return counts


def edge_decisions(events: list[Event]) -> dict[str, dict]:
    """Latest decision per edge id: {edge_id: {"choice": accept|reject, "who", "ts", "note", "event"}}."""
    out: dict[str, dict] = {}
    for e in events:
        if e.type != "decision" or not e.anchor or not e.anchor.edge:
            continue
        out[e.anchor.edge] = {"choice": e.body.get("choice"), "who": e.who, "ts": e.ts, "note": e.body.get("note", ""), "event": e.id}
    return out


def person_edges(events: list[Event]) -> list[dict]:
    """Connections a person added in the page (type ``edge``), as edge records with status ``person``."""
    out: list[dict] = []
    for e in events:
        if e.type != "edge":
            continue
        b = e.body
        if not (b.get("src") and b.get("dst") and b.get("type")):
            continue
        out.append({"id": f"{b['type']}:{b['src']}:{b['dst']}", "type": b["type"], "src": b["src"], "dst": b["dst"],
                    "source": f"person:{e.who or 'unnamed'}", "status": "person", "reason": b.get("reason", ""),
                    "evidence": b.get("evidence", ""), "event": e.id, "ts": e.ts})
    return out


def current_status(events: list[Event]) -> dict[str, str]:
    """Latest status per issue/question id, from ``status`` events that reference it."""
    out: dict[str, str] = {}
    for e in events:
        if e.type in ("issue", "question"):
            out.setdefault(e.id, "open")
        elif e.type == "status" and e.ref:
            out[e.ref] = e.body.get("status", "open")
    return out
