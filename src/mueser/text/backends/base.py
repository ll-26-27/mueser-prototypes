from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal, Optional, Protocol, runtime_checkable

Mode = Literal["print", "hand"]


@dataclass
class Line:
    text: str
    bbox: Optional[list[float]] = None       # [x, y, w, h] in image pixels
    baseline: Optional[list[list[float]]] = None  # [[x,y], ...]
    confidence: Optional[float] = None       # 0..1 when the backend gives one


@dataclass
class PageResult:
    page_id: str
    lines: list[Line]
    raw: dict                                # untouched backend response (or a pointer to the cache file)
    backend: str
    model: str
    cost_usd: Optional[float] = None
    seconds: Optional[float] = None
    cached: bool = False
    prompt_sha256: Optional[str] = None
    notes: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(l.text for l in self.lines)

    def to_dict(self) -> dict:
        return asdict(self)


class Skipped(RuntimeError):
    """Raised by a backend that cannot run here (no binary, model file or credential). Carries the reason."""


@runtime_checkable
class Backend(Protocol):
    name: str
    model: str

    def check(self) -> Optional[str]:
        """Return None if the backend can run, else a one-line reason it will be skipped."""
        ...

    def transcribe(self, image_path: Path, *, mode: Mode = "print", lang: str = "de") -> PageResult: ...


def page_id_for(image_path: Path) -> str:
    return Path(image_path).stem
