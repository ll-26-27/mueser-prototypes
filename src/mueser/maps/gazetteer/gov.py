"""GOV, the Genealogisches Ortsverzeichnis (gov.genealogy.net): the historical gazetteer of the German-speaking
world, with names and administrative membership over time. Highest priority here.

Public JSON API (OpenAPI spec at https://gov.genealogy.net/v3/api-docs; checked 2026-11-04):
  GET /api/searchByNameAndType?placename=<name>[&types=<code,...>]  -> list of objects
  GET /api/getObject?itemId=<id>                                      -> one object
Each object has ``id`` (textual like BREADTJO81MC for the main place objects, or object_NNN), ``position``
{lon, lat}, ``name`` [{lang, value, timespan{begin{jd}, end{jd}}, beginYear}], ``type`` [{value: <code>}],
``partOf``, ``url``. Timespans are Julian Day numbers; we convert them to years. Type codes are GOV's own
(51 = Stadt); we keep the code and prefer objects with a textual id and an exact name match.

The search is a contains-search, so "Breslau" also returns "Peterswaldau, Bez. Breslau"; scoring handles that.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from .base import Candidate, HttpCached, fold, name_similarity

SEARCH = "https://gov.genealogy.net/api/searchByNameAndType"
OBJECT = "https://gov.genealogy.net/api/getObject"
# GOV object-type codes seen in results; label the common ones for readers (others shown as the raw code).
TYPE_LABELS = {"51": "Stadt", "55": "Stadtteil/Ortsteil", "26": "Pfarrei (ev.)", "29": "Kirche (ev.)", "3": "Dorf", "9": "Vorwerk", "11": "Gut",
               "27": "Pfarrei (kath.)", "42": "Landkreis/Kreis", "46": "Regierungsbezirk", "6": "Gemeinde", "103": "Standesamt", "105": "Amtsgericht", "187": "Bezirk"}
SETTLEMENT_CODES = {"51", "55", "3", "6", "9", "11", "1", "2", "4", "5", "7", "8", "10", "12", "39", "40", "41", "120", "150"}


def jd_to_year(jd: float | int | None) -> Optional[int]:
    if jd is None:
        return None
    try:
        date = dt.date(1970, 1, 1) + dt.timedelta(days=float(jd) - 2440587.5)
        return date.year
    except (OverflowError, ValueError):
        return None


class GOVResolver(HttpCached):
    name = "gov"
    min_interval = 1.5

    def check(self) -> Optional[str]:
        return None

    def resolve(self, name: str, context: dict | None = None) -> list[Candidate]:
        try:
            data = self._get(SEARCH, params={"placename": name})
        except Exception as e:  # noqa: BLE001
            return [Candidate(uri="", label=f"gov error: {e}", lat=None, lon=None, source=self.name, score=0.0)]
        if not isinstance(data, list):
            return []
        out = []
        for it in data:
            gid = it.get("id", "")
            pos = it.get("position") or {}
            lat, lon = pos.get("lat"), pos.get("lon")
            names = it.get("name") or []
            values = [n.get("value", "") for n in names]
            de = [n for n in names if n.get("lang") == "deu"] or names
            # label: the German name that best matches the query, else the first German name
            label = max(de, key=lambda n: name_similarity(name, n.get("value", "")), default={}).get("value") or (values[0] if values else gid)
            best = max([name_similarity(name, v) for v in values] + [0.0])
            codes = [t.get("value", "") for t in it.get("type") or []]
            type_label = "; ".join(f"{TYPE_LABELS.get(c, 'type ' + c)}" for c in codes) or None
            is_settlement = any(c in SETTLEMENT_CODES for c in codes)
            textual_id = bool(gid) and not gid.startswith(("object_", "adm_"))
            score = best
            if not is_settlement:
                score -= 0.25     # churches, parishes, courts, districts share the town's name
            if textual_id:
                score += 0.05     # GOV's primary place objects carry textual ids
            score = round(max(0.0, min(1.0, score)), 3)
            # validity: span of the matching German name(s)
            vf = vt = None
            for n in de:
                if name_similarity(name, n.get("value", "")) >= 0.8:
                    ts = n.get("timespan") or {}
                    b = jd_to_year((ts.get("begin") or {}).get("jd")) or n.get("beginYear")
                    e = jd_to_year((ts.get("end") or {}).get("jd")) or n.get("endYear")
                    vf = str(b) if b and (vf is None or b < int(vf)) else vf
                    vt = str(e) if e and (vt is None or e > int(vt)) else vt
            urls = [u.get("value") for u in it.get("url") or [] if u.get("value")]
            pop = None
            pops = it.get("population")
            if isinstance(pops, list):
                vals = [int(x.get("value")) for x in pops if isinstance(x, dict) and str(x.get("value", "")).isdigit()]
                pop = max(vals) if vals else None
            elif isinstance(pops, (int, str)) and str(pops).isdigit():
                pop = int(pops)
            out.append(Candidate(uri=f"https://gov.genealogy.net/item/show/{gid}" if gid else "", label=label,
                                 lat=float(lat) if lat is not None else None, lon=float(lon) if lon is not None else None,
                                 source=self.name, score=score, valid_from=vf, valid_to=vt, feature_type=type_label,
                                 alt_names=[v for v in values if fold(v) != fold(label)][:15], admin=None,
                                 note=("; ".join(urls[:2]) or None), population=pop))
        return sorted(out, key=lambda c: (-c.score, c.lat is None, -(c.population or 0), c.label))[:12]
