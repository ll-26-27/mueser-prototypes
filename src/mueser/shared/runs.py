"""Run folders: every expensive operation writes into a timestamped folder with a run.json manifest.

Outputs are never overwritten; a new run is a new folder. run.json records parameters, model, prompt hash,
cost, timings and which inputs were used, so a result can be reproduced or disputed later.
"""

from __future__ import annotations

import json
import platform
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mueser import REPO_ROOT


def git_sha() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def run_id(prefix: str = "") -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    return f"{prefix}{ts}" if prefix else ts


@dataclass
class RunManifest:
    run_id: str
    step: str
    params: dict[str, Any] = field(default_factory=dict)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    seconds: float = 0.0
    notes: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    git: str | None = field(default_factory=git_sha)
    python: str = field(default_factory=platform.python_version)

    def write(self, folder: Path) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        p = folder / "run.json"
        p.write_text(json.dumps(self.__dict__, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return p


def rel(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
