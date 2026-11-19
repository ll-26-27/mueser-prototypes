"""Wikidata, read through its SPARQL endpoint, every reply cached raw.

Queries go by POST (the VALUES lists are long), with a generic client name and a pause between calls. A cache
hit returns the stored bindings without a request, so a run can be repeated offline and audited later: the
cache entry keeps the query text, the time it was fetched and the untouched JSON reply.
"""

from __future__ import annotations

import re
import time
from typing import Iterable

import httpx

from mueser.shared.cache import DiskCache, cache_key

ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "research-prototype/0.1 (local script)", "Accept": "application/sparql-results+json"}
PAUSE = 0.4  # seconds between live requests
OFFLINE_WAIT = 3600.0  # how long to wait for the network to come back, seconds

_cache = DiskCache("wikidata")


def sparql(query: str, *, timeout: float = 300.0, retries: int = 3) -> list[dict]:
    """Run one query; return the bindings with each variable reduced to its string value.

    A server error or a rate limit is retried ``retries`` times. A connection failure (no network, as on a
    laptop between two Wi-Fi networks) is waited out: the call sleeps and tries again for up to an hour.
    """
    key = cache_key("wikidata-sparql", query=query)
    hit = _cache.get(key)
    if hit:
        return hit["parsed"]
    last: Exception | None = None
    attempt = 0
    offline_since: float | None = None
    while True:
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.post(ENDPOINT, data={"query": query}, headers=HEADERS)
            if res.status_code == 429 or res.status_code >= 500:
                raise RuntimeError(f"HTTP {res.status_code}")
            res.raise_for_status()
            if len(res.content) > 50_000_000:
                raise RuntimeError(f"reply of {len(res.content) / 1e6:.0f} MB: the query ran into the endpoint's limit")
            raw = res.json()
            rows = [{k: v.get("value") for k, v in b.items()} for b in raw["results"]["bindings"]]
            _cache.put(key, request={"endpoint": ENDPOINT, "query": query}, raw=raw, parsed=rows)
            time.sleep(PAUSE)
            return rows
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            offline_since = offline_since or time.time()
            if time.time() - offline_since > OFFLINE_WAIT:
                raise RuntimeError(f"no network for {OFFLINE_WAIT / 60:.0f} minutes: {e}") from e
            time.sleep(15)
        except Exception as e:  # noqa: BLE001
            last = e
            attempt += 1
            if attempt > retries:
                raise RuntimeError(f"Wikidata query failed after {retries + 1} attempts: {last}") from last
            time.sleep(2.0 * attempt)


def qid(uri: str | None) -> str | None:
    if not uri:
        return None
    return uri.rsplit("/", 1)[-1]


def values(qids: Iterable[str]) -> str:
    return " ".join(f"wd:{q}" for q in qids)


def batched(items: list, size: int) -> Iterable[list]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


_DATE = re.compile(r"^(-?)(\d{1,6})-(\d\d)-(\d\d)T")


def year_of(value: str | None) -> int | None:
    """``"1588-04-05T00:00:00Z"`` -> 1588; ``"-0384-01-01T00:00:00Z"`` -> -384. None if unparseable."""
    if not value:
        return None
    m = _DATE.match(value)
    if not m:
        return None
    y = int(m.group(2))
    return -y if m.group(1) else y


def date_label(value: str | None, precision: int | None) -> str:
    """A human date honouring Wikidata's precision: 11 day, 10 month, 9 year, 8 decade, 7 century."""
    y = year_of(value)
    if y is None:
        return ""
    era = " BCE" if y < 0 else ""
    ay = abs(y)
    if precision is not None and precision <= 7:
        c = (ay - 1) // 100 + 1
        return f"{c}th century{era}" if c not in (1, 2, 3) else f"{c}{'st' if c == 1 else 'nd' if c == 2 else 'rd'} century{era}"
    if precision == 8:
        return f"{ay // 10 * 10}s{era}"
    if precision == 10:
        m = _DATE.match(value)
        return f"{ay}-{m.group(3)}{era}"
    if precision == 11:
        m = _DATE.match(value)
        return f"{ay}-{m.group(3)}-{m.group(4)}{era}"
    return f"{ay}{era}"


def split_multi(value: str | None) -> list[str]:
    if not value:
        return []
    seen: list[str] = []
    for part in value.split("␟"):
        part = part.strip()
        if part and part not in seen:
            seen.append(part)
    return seen
