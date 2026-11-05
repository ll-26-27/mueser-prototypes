"""Load the repo-root .env once and answer "is this credential present?" without ever printing it."""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

from mueser import REPO_ROOT


@lru_cache(maxsize=1)
def _load() -> bool:
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
        return True
    return False


def get(key: str, default: str | None = None) -> str | None:
    _load()
    value = os.environ.get(key)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def missing(*keys: str) -> list[str]:
    """Return the subset of keys that are not set. Empty list means all present."""
    return [k for k in keys if get(k) is None]
