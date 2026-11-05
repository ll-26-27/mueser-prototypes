"""GeoNames search (free web services; needs a username with web services enabled, GEONAMES_USERNAME in .env).

Good coverage of alternate/historical names via `alternateNames`; coordinates modern. Rate-limited (hourly and
daily caps on the free tier), so every answer is cached.
"""

from __future__ import annotations

from typing import Optional

from mueser.shared import env
from .base import Candidate, HttpCached, name_similarity

ENDPOINT = "http://api.geonames.org/searchJSON"


class GeoNamesResolver(HttpCached):
    name = "geonames"
    min_interval = 1.0

    def check(self) -> Optional[str]:
        if env.missing("GEONAMES_USERNAME"):
            return "GEONAMES_USERNAME not set in .env (free account at geonames.org/login; then enable web services on the account page)"
        return None

    def resolve(self, name: str, context: dict | None = None) -> list[Candidate]:
        user = env.get("GEONAMES_USERNAME")
        if not user:
            return []
        params = {"q": name, "maxRows": 10, "username": user, "style": "FULL", "featureClass": ["P", "A"], "isNameRequired": "true"}
        try:
            data = self._get(ENDPOINT, params=params)
        except Exception as e:  # noqa: BLE001
            return [Candidate(uri="", label=f"geonames error: {e}", lat=None, lon=None, source=self.name, score=0.0)]
        if "status" in data:
            return [Candidate(uri="", label=f"geonames: {data['status'].get('message')}", lat=None, lon=None, source=self.name, score=0.0)]
        out = []
        for g in data.get("geonames", []):
            alts = [a.get("name") for a in g.get("alternateNames", []) if a.get("name")]
            best = max([name_similarity(name, g.get("name", ""))] + [name_similarity(name, a) for a in alts] + [0.0])
            out.append(Candidate(uri=f"https://www.geonames.org/{g['geonameId']}", label=g.get("name", ""), lat=float(g["lat"]), lon=float(g["lng"]),
                                 source=self.name, score=round(best, 3), feature_type=g.get("fcodeName") or g.get("fcode"),
                                 alt_names=alts[:15], admin=", ".join(x for x in [g.get("adminName1"), g.get("countryName")] if x)))
        return sorted(out, key=lambda c: -c.score)
