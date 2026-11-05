"""Character and word error rate against ground truth, raw and after a declared normalisation.

CER = (substitutions + deletions + insertions) / characters in the ground truth. 0.05 means one wrong character
in twenty. Reported twice: **raw** (what the backend actually wrote) and **normalised** (ſ→s, superscript-e
umlauts → ä/ö/ü, hyphenation and whitespace collapsed) so a VLM that silently modernises is neither punished
nor rewarded for it without the reader seeing both numbers. The normalisation is a function, printed in the report.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def normalize(text: str) -> str:
    """The declared normalisation. Keep it small and listed in the README."""
    t = unicodedata.normalize("NFC", text)
    t = t.replace("ſ", "s")
    t = t.replace("aͤ", "ä").replace("oͤ", "ö").replace("uͤ", "ü").replace("Aͤ", "Ä").replace("Oͤ", "Ö").replace("Uͤ", "Ü")
    t = t.replace("ꝛ", "r").replace("ꝰ", "")
    t = t.replace("„", '"').replace("“", '"').replace("”", '"').replace("‚", "'").replace("‘", "'").replace("’", "'")
    t = re.sub(r"[‐‑‒–—]", "-", t)
    t = re.sub(r"-\n", "", t)          # join end-of-line hyphenation
    t = re.sub(r"\s+", " ", t).strip()
    return t


@dataclass
class Scores:
    cer: float
    wer: float
    cer_norm: float
    wer_norm: float
    gt_chars: int
    gt_words: int
    hyp_lines: int
    gt_lines: int


def _wer(gt: str, hyp: str) -> float:
    g, h = gt.split(), hyp.split()
    if not g:
        return 0.0 if not h else 1.0
    # word-level Levenshtein
    prev = list(range(len(h) + 1))
    for i, ga in enumerate(g, 1):
        cur = [i]
        for j, hb in enumerate(h, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ga != hb)))
        prev = cur
    return prev[-1] / len(g)


def _cer(gt: str, hyp: str) -> float:
    if not gt:
        return 0.0 if not hyp else 1.0
    return levenshtein(gt, hyp) / len(gt)


def score(gt_text: str, hyp_text: str) -> Scores:
    """Scores on the whole page as one string (line breaks become spaces), so line-order errors cost words, not pages."""
    gt_flat = re.sub(r"\s+", " ", unicodedata.normalize("NFC", gt_text)).strip()
    hyp_flat = re.sub(r"\s+", " ", unicodedata.normalize("NFC", hyp_text)).strip()
    return Scores(
        cer=round(_cer(gt_flat, hyp_flat), 4),
        wer=round(_wer(gt_flat, hyp_flat), 4),
        cer_norm=round(_cer(normalize(gt_text), normalize(hyp_text)), 4),
        wer_norm=round(_wer(normalize(gt_text), normalize(hyp_text)), 4),
        gt_chars=len(gt_flat),
        gt_words=len(gt_flat.split()),
        hyp_lines=len([l for l in hyp_text.splitlines() if l.strip()]),
        gt_lines=len([l for l in gt_text.splitlines() if l.strip()]),
    )


def char_diff(gt: str, hyp: str) -> list[tuple[str, str]]:
    """Opcode-level diff for the HTML report: list of (tag, text) with tag in equal/replace/delete/insert."""
    import difflib

    sm = difflib.SequenceMatcher(a=gt, b=hyp, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append(("equal", gt[i1:i2]))
        elif tag == "replace":
            out.append(("delete", gt[i1:i2]))
            out.append(("insert", hyp[j1:j2]))
        elif tag == "delete":
            out.append(("delete", gt[i1:i2]))
        elif tag == "insert":
            out.append(("insert", hyp[j1:j2]))
    return out
