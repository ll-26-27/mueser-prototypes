"""Wikidata, no key. Two steps through the MediaWiki API (which is not affected by SPARQL-endpoint outages or its
rate limits): ``wbsearchentities`` finds items whose label OR alias matches the name (that is where historical
German names live: "Breslau" is an alias of Wrocław), then ``wbgetentities`` fetches coordinates (P625), country
(P17), instance-of (P31), inception (P571) and dissolution (P576). Coordinates are modern. One request a second,
every response cached.
"""

from __future__ import annotations

from typing import Optional

from .base import Candidate, HttpCached, name_similarity

API = "https://www.wikidata.org/w/api.php"
SETTLEMENT_WORDS = ("city", "town", "village", "municipality", "settlement", "commune", "urban", "borough", "capital", "stadt", "gemeinde", "dorf", "hamlet", "district", "county", "region", "state", "province", "duchy", "voivodeship", "island", "castle", "monastery", "abbey", "fortress")


class WikidataResolver(HttpCached):
    name = "wikidata"
    min_interval = 1.0

    def check(self) -> Optional[str]:
        return None

    def _search(self, name: str, lang: str) -> list[dict]:
        data = self._get(API, params={"action": "wbsearchentities", "search": name, "language": lang, "uselang": "de", "type": "item", "limit": 12, "format": "json"})
        return data.get("search", [])

    # Only these claims are read. Entities are trimmed to them before caching, because a full entity for a
    # capital city runs to megabytes; the cache entry says so ("trimmed_to").
    PROPS = ("P625", "P17", "P31", "P571", "P576", "P1082")

    def _entities(self, ids: list[str]) -> dict:
        if not ids:
            return {}
        params = {"action": "wbgetentities", "ids": "|".join(ids), "props": "labels|descriptions|claims|aliases", "languages": "de|en", "format": "json"}
        data = self._get(API, params=params, trim=self._trim)
        return data.get("entities", {})

    @staticmethod
    def _trim_claims(prop: str, claims: list) -> list:
        kept = [{"mainsnak": {"datavalue": c.get("mainsnak", {}).get("datavalue")}} for c in claims]
        if prop == "P1082":
            # Population has one claim per census year; keep only the largest so the tie-break sees the city, not 1800.
            def amount(c):
                try:
                    return float(c["mainsnak"]["datavalue"]["value"]["amount"])
                except (KeyError, TypeError, ValueError):
                    return -1.0
            kept = sorted(kept, key=amount, reverse=True)[:1]
        return kept[:5]

    @classmethod
    def _trim(cls, data: dict) -> dict:
        ents = {}
        for qid, ent in (data.get("entities") or {}).items():
            ents[qid] = {"id": qid, "labels": ent.get("labels", {}), "descriptions": ent.get("descriptions", {}), "aliases": ent.get("aliases", {}),
                         "claims": {p: cls._trim_claims(p, ent.get("claims", {}).get(p, [])) for p in cls.PROPS if p in ent.get("claims", {})}}
        return {"entities": ents, "trimmed_to": list(cls.PROPS) + ["labels", "descriptions", "aliases"]}

    @staticmethod
    def _claim_value(ent: dict, prop: str):
        for c in ent.get("claims", {}).get(prop, []):
            try:
                return c["mainsnak"]["datavalue"]["value"]
            except KeyError:
                continue
        return None

    @staticmethod
    def _label(ent: dict) -> str:
        labels = ent.get("labels", {})
        return (labels.get("de") or labels.get("en") or {}).get("value", ent.get("id", ""))

    def resolve(self, name: str, context: dict | None = None) -> list[Candidate]:
        try:
            hits = self._search(name, "de")
            if len(hits) < 3:
                seen = {h["id"] for h in hits}
                hits += [h for h in self._search(name, "en") if h["id"] not in seen]
            ids = [h["id"] for h in hits][:12]
            ents = self._entities(ids)
        except Exception as e:  # noqa: BLE001
            return [Candidate(uri="", label=f"wikidata error: {e}", lat=None, lon=None, source=self.name, score=0.0)]
        # Resolve the Q-ids of country and instance-of to labels in one more call.
        ref_ids: set[str] = set()
        for ent in ents.values():
            for prop in ("P17", "P31"):
                for c in ent.get("claims", {}).get(prop, [])[:3]:
                    try:
                        ref_ids.add(c["mainsnak"]["datavalue"]["value"]["id"])
                    except KeyError:
                        pass
        try:
            ref = self._entities(sorted(ref_ids)[:50]) if ref_ids else {}
        except Exception:  # noqa: BLE001
            ref = {}   # labels for country / type are a nicety; the candidate list must not fail without them
        out = []
        for qid in ids:
            ent = ents.get(qid)
            if not ent:
                continue
            coord = self._claim_value(ent, "P625")
            if not coord:
                continue
            label = self._label(ent)
            aliases = [a["value"] for lang in ("de", "en") for a in ent.get("aliases", {}).get(lang, [])]
            types = []
            for c in ent.get("claims", {}).get("P31", [])[:3]:
                try:
                    types.append(self._label(ref.get(c["mainsnak"]["datavalue"]["value"]["id"], {})))
                except KeyError:
                    pass
            country = None
            cv = self._claim_value(ent, "P17")
            if isinstance(cv, dict):
                country = self._label(ref.get(cv.get("id"), {})) or None
            pop = None
            for c in ent.get("claims", {}).get("P1082", []):
                try:
                    v = int(float(c["mainsnak"]["datavalue"]["value"]["amount"]))
                    pop = v if pop is None else max(pop, v)
                except (KeyError, ValueError):
                    pass
            inception = self._claim_value(ent, "P571")
            dissolved = self._claim_value(ent, "P576")
            best = max([name_similarity(name, label)] + [name_similarity(name, a) for a in aliases] + [0.0])
            typestr = "; ".join(t for t in types if t)
            is_settlement = any(w in typestr.lower() for w in SETTLEMENT_WORDS)
            score = round(min(1.0, best + (0.0 if is_settlement else -0.2)), 3)
            desc = (ent.get("descriptions", {}).get("de") or ent.get("descriptions", {}).get("en") or {}).get("value", "")
            out.append(Candidate(uri=f"https://www.wikidata.org/wiki/{qid}", label=label, lat=float(coord["latitude"]), lon=float(coord["longitude"]),
                                 source=self.name, score=score, valid_from=(inception or {}).get("time", "").lstrip("+")[:10] or None if isinstance(inception, dict) else None,
                                 valid_to=(dissolved or {}).get("time", "").lstrip("+")[:10] or None if isinstance(dissolved, dict) else None,
                                 feature_type=typestr or None, alt_names=aliases[:15], admin=country, note=desc or None, population=pop))
        return sorted(out, key=lambda c: -c.score)[:10]
