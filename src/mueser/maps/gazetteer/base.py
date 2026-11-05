"""Resolver interface: a historical place name (+ context) -> candidates with coordinates and a score.

Every resolver caches each HTTP response on disk (cache/<resolver>/) and never raises on a miss: it returns an
empty list. ``check()`` says whether it can run (GeoNames needs a username). Scores are 0..1 and comparable only
within one resolver; reconcile.py combines them with resolver priority.
"""

from __future__ import annotations

import time
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Optional, Protocol

import httpx

from mueser.shared.cache import DiskCache, cache_key

USER_AGENT = "mueser-prototypes/0.1 (Harvard Bok Center Learning Lab; research prototype; cached, rate-limited lookups)"


@dataclass
class Candidate:
    uri: str
    label: str
    lat: Optional[float]
    lon: Optional[float]
    source: str                     # gov | wikidata | whg | geonames
    score: float                    # 0..1 within the resolver
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    feature_type: Optional[str] = None
    alt_names: list[str] = field(default_factory=list)
    admin: Optional[str] = None     # modern country / region string for a reader
    note: Optional[str] = None
    population: Optional[int] = None  # latest known population, when the gazetteer records one (tie-break only)

    def to_dict(self) -> dict:
        return asdict(self)


class Resolver(Protocol):
    name: str

    def check(self) -> Optional[str]: ...
    def resolve(self, name: str, context: dict | None = None) -> list[Candidate]: ...


def fold(s: str) -> str:
    """Lowercase, strip accents, map ß->ss, collapse spaces; for comparing names, never for display."""
    s = unicodedata.normalize("NFKD", s).replace("ß", "ss")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def name_similarity(query: str, label: str) -> float:
    """Cheap, explainable: exact folded match 1.0; prefix/contains 0.8; Levenshtein ratio otherwise."""
    q, l = fold(query), fold(label)
    if not q or not l:
        return 0.0
    if q == l:
        return 1.0
    if l.startswith(q) or q.startswith(l) or q in l.split() or l in q.split():
        return 0.8
    # ratio
    from mueser.text.evaluate import levenshtein

    d = levenshtein(q, l)
    return max(0.0, 1 - d / max(len(q), len(l)))


class HttpCached:
    """Mixin: GET/POST with disk cache, polite rate limit, and identifying User-Agent."""

    name = "http"
    min_interval = 1.0
    _last = 0.0

    def __init__(self):
        self.cache = DiskCache(f"gazetteer_{self.name}")

    def _get(self, url: str, params: dict | None = None, headers: dict | None = None, *, as_json: bool = True, trim=None):
        """GET with cache. ``trim`` (optional) reduces a huge JSON reply to the parts the resolver reads BEFORE it is
        cached; the cache entry then carries the trimmed reply, which is what the resolver saw."""
        key = cache_key(self.name, url=url, params=params)
        hit = self.cache.get(key)
        if hit:
            return hit["raw"]
        wait = self._last + self.min_interval - time.time()
        if wait > 0:
            time.sleep(wait)
        HttpCached._last = time.time()
        h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        h.update(headers or {})
        r = None
        for attempt in range(4):
            with httpx.Client(timeout=60, follow_redirects=True) as c:
                r = c.get(url, params=params, headers=h)
            if r.status_code == 429 or r.status_code >= 500:
                # Back off and retry: these services ask clients to slow down rather than fail.
                time.sleep(float(r.headers.get("Retry-After") or (5 * 3**attempt)))
                continue
            break
        assert r is not None
        r.raise_for_status()
        raw = r.json() if as_json else r.text
        if trim is not None:
            raw = trim(raw)
        self.cache.put(key, request={"url": url, "params": params}, raw=raw, meta={"trimmed": trim is not None})
        return raw
