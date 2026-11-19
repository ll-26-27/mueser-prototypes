"""Anchor settled lines to boxes by aligning them with a reading that has coordinates.

The text a person reads is the medoid reading, which on most pages is a whole-page vision reading with no boxes.
A hybrid or Kraken reading of the same page has a box for every line it segmented. Aligning the two lists of
line strings (Needleman–Wunsch, cost = the declared normalised distance) gives each settled line a box, or says
honestly that it has none. Four operations:

- ``match``       one settled line, one polygon
- ``merge``       two settled lines against one polygon (the segmenter joined them); both get that box
- ``split``       one settled line against two polygons (a column gap); the box is their union
- ``unanchored``  a settled line no polygon fits (cost above ``max_dist``, or no polygon left)

A polygon no settled line fits (an ornament, masthead lettering, an empty crop) is dropped and counted.
Line-level rather than character-level so that each failure mode is explicit and carries a confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mueser.text.compare import dist

GAP_SETTLED = 1.0      # leaving a settled line without a polygon
GAP_POLYGON = 1.0      # dropping a polygon that has text
GAP_EMPTY = 0.15       # dropping a polygon whose reading is empty is cheap
PAIR_PENALTY = 0.15    # merge and split should not beat two clean matches


@dataclass
class SegLine:
    idx: int
    text: str
    bbox: list[float] | None
    baseline: list | None = None


@dataclass
class Anchor:
    op: str                                   # match | merge | split | unanchored
    seg_idx: list[int] = field(default_factory=list)
    bbox: list[float] | None = None
    confidence: float | None = None

    def to_dict(self) -> dict:
        return {"op": self.op, "seg_idx": self.seg_idx, "bbox": self.bbox, "confidence": self.confidence}


def union(boxes: list[list[float]]) -> list[float]:
    xs = [b[0] for b in boxes] + [b[0] + b[2] for b in boxes]
    ys = [b[1] for b in boxes] + [b[1] + b[3] for b in boxes]
    return [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]


def align_lines(settled: list[str], seg: list[SegLine], *, max_dist: float = 0.55) -> tuple[list[Anchor], dict]:
    """Return one Anchor per settled line and a summary with counts."""
    n, m = len(settled), len(seg)
    memo: dict[tuple[str, str], float] = {}

    def d(a: str, b: str) -> float:
        k = (a, b)
        if k not in memo:
            memo[k] = dist(a, b)
        return memo[k]

    INF = 1e9
    dp = [[INF] * (m + 1) for _ in range(n + 1)]
    back: list[list[tuple | None]] = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                continue
            cands: list[tuple[float, tuple]] = []
            if i > 0:
                cands.append((dp[i - 1][j] + GAP_SETTLED, ("gap_s",)))
            if j > 0:
                cands.append((dp[i][j - 1] + (GAP_POLYGON if seg[j - 1].text.strip() else GAP_EMPTY), ("gap_p",)))
            # a pairing above max_dist is not an option at all; otherwise the DP would take a bad pairing over two gaps
            if i > 0 and j > 0:
                c = d(settled[i - 1], seg[j - 1].text)
                if c <= max_dist:
                    cands.append((dp[i - 1][j - 1] + c, ("match", c)))
            if i > 1 and j > 0:
                c = d(settled[i - 2] + " " + settled[i - 1], seg[j - 1].text)
                if c <= max_dist:
                    cands.append((dp[i - 2][j - 1] + c + PAIR_PENALTY, ("merge", c)))
            if i > 0 and j > 1:
                c = d(settled[i - 1], seg[j - 2].text + " " + seg[j - 1].text)
                if c <= max_dist:
                    cands.append((dp[i - 1][j - 2] + c + PAIR_PENALTY, ("split", c)))
            dp[i][j], back[i][j] = min(cands, key=lambda t: t[0])

    anchors: list[Anchor | None] = [None] * n
    dropped: list[int] = []
    i, j = n, m
    while i > 0 or j > 0:
        op = back[i][j]
        assert op is not None
        if op[0] == "gap_s":
            anchors[i - 1] = Anchor("unanchored")
            i -= 1
        elif op[0] == "gap_p":
            dropped.append(j - 1)
            j -= 1
        elif op[0] == "match":
            c = op[1]
            if c > max_dist:
                anchors[i - 1] = Anchor("unanchored", confidence=round(1 - c, 3))
                dropped.append(j - 1)
            else:
                anchors[i - 1] = Anchor("match", [j - 1], seg[j - 1].bbox, round(1 - c, 3))
            i -= 1; j -= 1
        elif op[0] == "merge":
            c = op[1]
            if c > max_dist:
                anchors[i - 1] = Anchor("unanchored", confidence=round(1 - c, 3))
                anchors[i - 2] = Anchor("unanchored", confidence=round(1 - c, 3))
                dropped.append(j - 1)
            else:
                anchors[i - 1] = Anchor("merge", [j - 1], seg[j - 1].bbox, round(1 - c, 3))
                anchors[i - 2] = Anchor("merge", [j - 1], seg[j - 1].bbox, round(1 - c, 3))
            i -= 2; j -= 1
        elif op[0] == "split":
            c = op[1]
            if c > max_dist:
                anchors[i - 1] = Anchor("unanchored", confidence=round(1 - c, 3))
                dropped.extend([j - 2, j - 1])
            else:
                boxes = [b for b in (seg[j - 2].bbox, seg[j - 1].bbox) if b]
                anchors[i - 1] = Anchor("split", [j - 2, j - 1], union(boxes) if boxes else None, round(1 - c, 3))
            i -= 1; j -= 2
    out = [a or Anchor("unanchored") for a in anchors]
    conf = [a.confidence for a in out if a.op != "unanchored" and a.confidence is not None]
    summary = {
        "matched": sum(1 for a in out if a.op == "match"),
        "merged": sum(1 for a in out if a.op == "merge"),
        "split": sum(1 for a in out if a.op == "split"),
        "unanchored": sum(1 for a in out if a.op == "unanchored"),
        "dropped_polygons": len(set(dropped)),
        "mean_confidence": round(sum(conf) / len(conf), 3) if conf else None,
        "max_dist": max_dist,
    }
    return out, summary


def seg_lines_from_reading(reading: dict) -> list[SegLine]:
    """A per-page run JSON (PageResult.to_dict) -> the polygons it carries, in order; lines without a box are skipped."""
    out = []
    for i, ln in enumerate(reading.get("lines", [])):
        if ln.get("bbox"):
            out.append(SegLine(i, ln.get("text") or "", list(ln["bbox"]), ln.get("baseline")))
    return out
