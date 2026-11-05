"""Step 1 (deterministic code): fetch the community transcriptions that serve as ground truth for the real sample
pages, record exactly which revision was used, and clean the wiki markup into one plain-text line per line.

    uv run python 01-use-cases/transcription/01-fraktur-print-bakeoff/operations/01-fetch-ground-truth.py

Writes inputs/gt/<page>.txt and inputs/gt/provenance.json. The Wikisource pages are proofread transcriptions
(quality level recorded) that normalise ſ to s and, for prose, do not keep the printed line breaks; the
evaluation therefore reports CER on the flattened text and a normalised CER that also folds ſ→s.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
GT = HERE.parent / "inputs" / "gt"
UA = "mueser-prototypes/0.1 (Harvard Bok Center Learning Lab research prototype; https://github.com/ll-26-27)"

PAGES = {
    "real-schiller-musenalmanach-1796-p093": ("de.wikisource.org", "Seite:Schiller_Musenalmanach_1796_093.jpg"),
    "real-grimm-khm-1812-i-p093": ("de.wikisource.org", "Seite:Kinder_und_Hausmärchen_(Grimm)_1812_I_093.jpg"),
    "real-gartenlaube-1853-p001": ("de.wikisource.org", "Seite:Die_Gartenlaube_(1853)_001.jpg"),
}


def fetch_wikitext(host: str, title: str) -> tuple[str, dict]:
    with httpx.Client(timeout=60, headers={"User-Agent": UA}) as c:
        r = c.get(f"https://{host}/w/api.php", params={"action": "query", "prop": "revisions", "rvprop": "content|ids|timestamp|user",
                                                       "rvslots": "main", "format": "json", "titles": title})
    r.raise_for_status()
    page = next(iter(r.json()["query"]["pages"].values()))
    rev = page["revisions"][0]
    return rev["slots"]["main"]["*"], {"host": host, "title": title, "pageid": page.get("pageid"), "revid": rev.get("revid"),
                                       "timestamp": rev.get("timestamp"), "url": f"https://{host}/wiki/{title}"}


def clean(wikitext: str) -> list[str]:
    t = wikitext
    quality = re.search(r'<pagequality level="(\d)"', t)
    t = re.sub(r"<noinclude>.*?</noinclude>", "", t, flags=re.S)
    t = re.sub(r"<section [^>]*/>", "", t)
    t = re.sub(r"\{\{idt\}\}", "", t)
    t = re.sub(r"\{\{Zeile\|\d+\}\}", "", t)
    t = re.sub(r"\{\{GLÜberschrift\|[^|}]*\|[^|}]*\|([^}]*)\}\}", r"\1", t)
    for _ in range(3):   # nested templates like {{Center|<big>'''x'''</big>}}
        t = re.sub(r"\{\{(?:Center|center|Zentriert|Rechts|Links|Sperrschrift|SperrSchrift|Bold|fett)\|([^{}]*)\}\}", r"\1", t)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t)             # any other template: drop
    t = re.sub(r"\{\|.*?\|\}", lambda m: "\n".join(re.findall(r"'''([^']+)'''", m.group(0))), t, flags=re.S)  # tables: keep bold cells
    t = re.sub(r"</?(poem|big|small|br|span|div|u|i|b|center)[^>]*>", "", t)
    t = re.sub(r"^-{4,}\s*$", "", t, flags=re.M)
    t = t.replace("'''", "").replace("''", "")
    lines = [re.sub(r"\s+", " ", l).strip() for l in t.splitlines()]
    out = [l for l in lines if l]
    return out, (quality.group(1) if quality else None)


def main() -> None:
    GT.mkdir(parents=True, exist_ok=True)
    prov = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "pages": {}}
    for page_id, (host, title) in PAGES.items():
        wt, meta = fetch_wikitext(host, title)
        lines, quality = clean(wt)
        (GT / f"{page_id}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (GT / f"{page_id}.wikitext").write_text(wt, encoding="utf-8")
        prov["pages"][page_id] = {**meta, "proofread_level": quality, "lines": len(lines), "chars": sum(len(l) for l in lines),
                                  "note": "Wikisource proofread transcription; ſ normalised to s by Wikisource convention; prose line breaks not preserved"}
        print(f"{page_id}: {len(lines)} lines, quality {quality}, rev {meta['revid']}")
        time.sleep(1)
    (GT / "provenance.json").write_text(json.dumps(prov, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
