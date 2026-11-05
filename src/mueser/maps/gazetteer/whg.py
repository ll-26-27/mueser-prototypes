"""World Historical Gazetteer (whgazetteer.org): an aggregator of historical place names with temporal scope.

Public index API, no key. Returns name variants and, when the contributed data has them, time spans.
"""

from __future__ import annotations

from typing import Optional

from .base import Candidate, HttpCached, name_similarity

ENDPOINT = "https://whgazetteer.org/api/index/"


class WHGResolver(HttpCached):
    name = "whg"
    min_interval = 1.0

    def check(self) -> Optional[str]:
        return None

    def resolve(self, name: str, context: dict | None = None) -> list[Candidate]:
        try:
            params = {"name": name}
            if context and context.get("ccodes"):
                params["ccodes"] = ",".join(context["ccodes"])
            data = self._get(ENDPOINT, params=params)
        except Exception as e:  # noqa: BLE001
            return [Candidate(uri="", label=f"whg error: {e}", lat=None, lon=None, source=self.name, score=0.0)]
        feats = data.get("features", []) if isinstance(data, dict) else []
        out = []
        for f in feats[:15]:
            props = f.get("properties", {})
            geom = f.get("geometry") or {}
            lat = lon = None
            if geom.get("type") == "Point" and geom.get("coordinates"):
                lon, lat = geom["coordinates"][:2]
            elif geom.get("type") == "GeometryCollection":
                for g in geom.get("geometries", []):
                    if g.get("type") == "Point":
                        lon, lat = g["coordinates"][:2]
                        break
            label = props.get("title") or props.get("name") or ""
            variants = [v if isinstance(v, str) else v.get("toponym", "") for v in props.get("variants", [])]
            best = max([name_similarity(name, label)] + [name_similarity(name, v) for v in variants if v] + [0.0])
            vf = vt = None
            mm = props.get("minmax")
            if isinstance(mm, list) and len(mm) == 2 and all(isinstance(x, (int, float)) for x in mm):
                vf, vt = str(int(mm[0])), str(int(mm[1]))
            else:
                ts = props.get("timespans") or []
                starts = [t.get("start", {}).get("in") or t.get("start", {}).get("earliest") for t in ts if isinstance(t, dict)]
                ends = [t.get("end", {}).get("in") or t.get("end", {}).get("latest") for t in ts if isinstance(t, dict)]
                starts = [s for s in starts if s is not None]; ends = [e for e in ends if e is not None]
                vf, vt = (str(min(starts)) if starts else None), (str(max(ends)) if ends else None)
            out.append(Candidate(uri=f"https://whgazetteer.org/places/{props.get('place_id') or props.get('pid') or ''}/portal",
                                 label=label, lat=lat, lon=lon, source=self.name, score=round(best, 3), valid_from=vf, valid_to=vt,
                                 feature_type=", ".join(props.get("types", []) or []) or None, alt_names=[v for v in variants if v][:15],
                                 admin=props.get("ccodes") and ", ".join(props["ccodes"])))
        return sorted(out, key=lambda c: -c.score)
