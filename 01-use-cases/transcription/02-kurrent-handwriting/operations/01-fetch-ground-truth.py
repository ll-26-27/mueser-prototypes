"""Step 1 (deterministic code): fetch the transcriptions that accompany the three real handwriting samples on
Wikimedia Commons (written by the uploaders or taken from the holding institution), record the revision used, and
save them as plain-text ground truth. They are community transcriptions, not editions: the README says what to
check. Square brackets in the Poesiealbum text mark the uploader's own uncertain readings; they are kept.

    uv run python 01-use-cases/transcription/02-kurrent-handwriting/operations/01-fetch-ground-truth.py
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
GT = HERE.parent / "inputs" / "gt"
UA = "mueser-prototypes/0.1 (Harvard Bok Center Learning Lab research prototype; https://github.com/ll-26-27)"

PAGES = {
    "real-kaskel-to-schnorr-1864": "File:Fotothek_Df_hauptkatalog_0280537_&_0280538.jpg",
    "real-schnitzler-to-beer-hofmann-1896": "File:Arthur_Schnitzler_an_Richard_Beer-Hofmann,_14._März_1896.jpg",
    "real-poesiealbum-hedwig-1901-p02": "File:Poesiealbum_von_Hedwig-02.JPG",
}


def fetch(title: str) -> tuple[str, dict]:
    with httpx.Client(timeout=60, headers={"User-Agent": UA}) as c:
        r = c.get("https://commons.wikimedia.org/w/api.php", params={"action": "query", "prop": "revisions", "rvprop": "content|ids|timestamp",
                                                                      "rvslots": "main", "format": "json", "titles": title})
    r.raise_for_status()
    page = next(iter(r.json()["query"]["pages"].values()))
    rev = page["revisions"][0]
    return rev["slots"]["main"]["*"], {"title": title, "pageid": page.get("pageid"), "revid": rev.get("revid"), "timestamp": rev.get("timestamp"),
                                       "url": "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_")}


def extract(page_id: str, wikitext: str) -> list[str]:
    m = re.search(r"\{\{de\|1=(.*?)\}\}\s*\n\|", wikitext, re.S)
    body = m.group(1) if m else wikitext
    if page_id == "real-kaskel-to-schnorr-1864":
        body = body.split("Blatt 84", 1)[1]                      # the catalogue header comes first
        body = body.replace(" (Ludwig Schnorr von Carolsfeld; Anm. des Uploaders)", "")
    elif page_id == "real-schnitzler-to-beer-hofmann-1896":
        m2 = re.search(r"»(.*?)«", body, re.S)
        body = m2.group(1) if m2 else body
        body = re.sub(r"https?://\S+", "", body)
    elif page_id == "real-poesiealbum-hedwig-1901-p02":
        body = body.split(":TEXT", 1)[1]
        body = "\n".join(l.lstrip(":") for l in body.splitlines())
    lines = [re.sub(r"\s+", " ", l).strip() for l in body.splitlines()]
    return [l for l in lines if l]


def main() -> None:
    GT.mkdir(parents=True, exist_ok=True)
    prov = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "pages": {}}
    for page_id, title in PAGES.items():
        wt, meta = fetch(title)
        lines = extract(page_id, wt)
        (GT / f"{page_id}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (GT / f"{page_id}.wikitext").write_text(wt, encoding="utf-8")
        prov["pages"][page_id] = {**meta, "lines": len(lines), "chars": sum(len(l) for l in lines),
                                  "note": "transcription from the Commons file description (uploader / holding institution); not a checked edition"}
        print(f"{page_id}: {len(lines)} lines, rev {meta['revid']}")
        time.sleep(1)
    (GT / "provenance.json").write_text(json.dumps(prov, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
