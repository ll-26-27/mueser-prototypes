"""Disk cache for expensive calls, keyed by a hash of everything that could change the answer.

Every cached file keeps the untouched raw response next to the parsed result, so a run can be audited
later without re-calling the service. Keys are sha256 of a canonical JSON of (namespace, parts...).
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

from mueser import REPO_ROOT

DEFAULT_CACHE_DIR = REPO_ROOT / "cache"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def cache_key(namespace: str, **parts: Any) -> str:
    canon = json.dumps([namespace, parts], sort_keys=True, ensure_ascii=False, default=str)
    return sha256_text(canon)


class DiskCache:
    def __init__(self, namespace: str, root: Path | None = None):
        self.dir = (root or DEFAULT_CACHE_DIR) / namespace
        self.dir.mkdir(parents=True, exist_ok=True)
        self.namespace = namespace

    def path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def get(self, key: str) -> Optional[dict]:
        p = self.path(key)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return None

    def put(self, key: str, *, request: dict, raw: Any, parsed: Any = None, meta: dict | None = None) -> dict:
        entry = {
            "namespace": self.namespace,
            "key": key,
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "request": request,
            "raw": raw,
            "parsed": parsed,
            "meta": meta or {},
        }
        self.path(key).write_text(json.dumps(entry, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        return entry
