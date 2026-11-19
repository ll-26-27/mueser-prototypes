"""Where every node's citation comes from, and the texts fetched for it.

Two kinds of thing are fetched here, both cached raw on disk and both attributed on the page:

- **Stanford Encyclopedia of Philosophy entries**: for every node with an SEP ID, the entry page, from which the
  title, authors, first-published and substantive-revision dates are read (the page's ``citation_*`` meta tags
  and its ``pubinfo`` block). That gives the citation the Encyclopedia itself asks for.
- **Wikipedia summaries**: the lead extract of the English article (German when there is no English one), with
  its revision id and timestamp, through the REST summary endpoint. Shown on the page as the overview, under the
  article's name and licence (CC BY-SA 4.0). It is a summary a reader can check, not a claim of this repository.

The link-outs (``links``) are built from the identifiers Wikidata holds, by the URL pattern of each reference
work, and listed with the work's name so a reader knows what each link is before following it.
"""

from __future__ import annotations

import html
import json
import re
import time
from pathlib import Path
from urllib.parse import quote

import httpx

from mueser.shared.cache import DiskCache, cache_key
from mueser.shared.runs import RunManifest, rel

from . import case_paths

UA = {"User-Agent": "research-prototype/0.1 (local script)"}
OFFLINE_WAIT = 3600.0


def get(url: str, *, params: dict | None = None, timeout: float = 60.0) -> httpx.Response:
    """GET with the generic client name; a lost network is waited out for up to an hour, as in wikidata.py."""
    offline_since: float | None = None
    while True:
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                return client.get(url, params=params, headers=UA)
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            offline_since = offline_since or time.time()
            if time.time() - offline_since > OFFLINE_WAIT:
                raise RuntimeError(f"no network for {OFFLINE_WAIT / 60:.0f} minutes: {e}") from e
            time.sleep(15)

# scheme -> (name, url pattern, what it is)
LINK_SCHEMES: dict[str, tuple[str, str, str]] = {
    "P3123": ("Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/{}/", "entry"),
    "P5088": ("Internet Encyclopedia of Philosophy", "https://iep.utm.edu/{}/", "entry"),
    "P1417": ("Encyclopædia Britannica", "https://www.britannica.com/{}", "article"),
    "P1415": ("Oxford Dictionary of National Biography", "https://doi.org/10.1093/ref:odnb/{}", "article (subscription)"),
    "P12582": ("Oxford Reference", "https://www.oxfordreference.com/view/10.1093/oi/authority.{}", "overview"),
    "P8410": ("Oxford Bibliographies", "https://www.oxfordbibliographies.com/view/document/{}.xml", "bibliography (subscription)"),
    "P5275": ("Oxford English Dictionary", "https://www.oed.com/view/Entry/{}", "entry (subscription)"),
    "P12510": ("Oxford English Dictionary", "https://www.oed.com/dictionary/{}", "entry (subscription)"),
    "P9106": ("Oxford Classical Dictionary", "https://oxfordre.com/classics/view/10.1093/acrefore/9780199381135.001.0001/acrefore-9780199381135-e-{}", "entry"),
    "P7902": ("Deutsche Biographie", "https://www.deutsche-biographie.de/{}.html", "entry"),
    "P7993": ("Treccani, Dizionario di Filosofia", "https://www.treccani.it/enciclopedia/{}_(Dizionario-di-filosofia)/", "entry"),
    "P3365": ("Treccani", "https://www.treccani.it/enciclopedia/{}/", "entry"),
    "P11802": ("Zeno.org", "http://www.zeno.org/nid/{}", "text"),
    "P1938": ("Project Gutenberg", "https://www.gutenberg.org/ebooks/author/{}", "author's texts"),
    "P2034": ("Project Gutenberg", "https://www.gutenberg.org/ebooks/{}", "ebook"),
    "P724": ("Internet Archive", "https://archive.org/details/{}", "scan"),
    "P648": ("Open Library", "https://openlibrary.org/works/{}", "editions"),
    "P243": ("WorldCat", "https://www.worldcat.org/oclc/{}", "library record"),
    "P214": ("VIAF", "https://viaf.org/viaf/{}/", "authority record"),
    "P244": ("Library of Congress", "https://id.loc.gov/authorities/{}", "authority record"),
    "P227": ("GND", "https://d-nb.info/gnd/{}", "authority record"),
    "P3732": ("PhilPapers", "https://philpapers.org/rec/{}", "record"),
    "P1296": ("Gran Enciclopèdia Catalana", "https://www.enciclopedia.cat/gran-enciclopedia-catalana/{}", "entry"),
}


def links_for(node: dict) -> list[dict]:
    out: list[dict] = []
    for prop, value in node.get("ids", {}).items():
        spec = LINK_SCHEMES.get(prop)
        if not spec:
            continue
        name, pattern, kind = spec
        out.append({"scheme": prop, "name": name, "kind": kind, "id": value, "url": pattern.format(quote(str(value), safe="/:()._-"))})
    for lang, title in node.get("wiki", {}).items():
        out.append({"scheme": f"wikipedia:{lang}", "name": f"Wikipedia ({lang})", "kind": "article", "id": title,
                    "url": f"https://{lang}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"})
    out.append({"scheme": "wikidata", "name": "Wikidata", "kind": "item", "id": node["id"], "url": f"https://www.wikidata.org/wiki/{node['id']}"})
    if node.get("image"):
        fn = node["image"].rsplit("/", 1)[-1]
        out.append({"scheme": "commons", "name": "Wikimedia Commons", "kind": "image", "id": fn,
                    "url": f"https://commons.wikimedia.org/wiki/File:{fn}"})
    return out


def image_url(node: dict, width: int = 360) -> str | None:
    if not node.get("image"):
        return None
    fn = node["image"].rsplit("/", 1)[-1]
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{fn}?width={width}"


# ----------------------------------------------------------------------------------------------- SEP

_sep_cache = DiskCache("sep")
_META = re.compile(r'<meta name="citation_(\w+)" content="([^"]*)"')
_PUB = re.compile(r'<div id="pubinfo">\s*<em>(.*?)</em>', re.DOTALL)


def fetch_sep(entry_id: str, *, pause: float = 0.4) -> dict:
    url = f"https://plato.stanford.edu/entries/{entry_id}/"
    key = cache_key("sep-entry", url=url)
    hit = _sep_cache.get(key)
    if hit:
        return hit["parsed"]
    parsed: dict = {"id": entry_id, "url": url, "ok": False}
    try:
        res = get(url)
        raw = res.text
        parsed["status"] = res.status_code
        if res.status_code == 200:
            metas: dict[str, list[str]] = {}
            for k, v in _META.findall(raw):
                metas.setdefault(k, []).append(html.unescape(v))
            pub = _PUB.search(raw)
            parsed.update({
                "ok": bool(metas.get("title")),
                "title": (metas.get("title") or [""])[0],
                "authors": metas.get("author", []),
                "published": (metas.get("publication_date") or [""])[0],
                "pubinfo": html.unescape(re.sub(r"<[^>]+>", "", pub.group(1))).strip() if pub else "",
            })
        _sep_cache.put(key, request={"url": url}, raw=raw, parsed=parsed, meta={"status": res.status_code})
        time.sleep(pause)
    except Exception as e:  # noqa: BLE001
        parsed["error"] = str(e)[:200]
    return parsed


def sep_citation(meta: dict, accessed: str) -> dict:
    """The form the Encyclopedia asks for, without the archive edition (the live entry is cited, with its revision)."""
    authors = meta.get("authors") or []
    names = [a.strip() for a in authors]
    # citation_author is "Last, First"; keep that for the first, "First Last" for the others, as SEP does.
    def flip(n: str) -> str:
        parts = [p.strip() for p in n.split(",", 1)]
        return f"{parts[1]} {parts[0]}" if len(parts) == 2 else n
    if not names:
        who = ""
    elif len(names) == 1:
        who = names[0]
    elif len(names) == 2:
        who = f"{names[0]} and {flip(names[1])}"
    else:
        who = ", ".join([names[0]] + [flip(n) for n in names[1:-1]]) + f", and {flip(names[-1])}"
    rev = meta.get("pubinfo", "")
    m = re.search(r"substantive revision (.+)$", rev)
    when = m.group(1).strip() if m else re.sub(r"^First published ", "", rev).strip()
    title = meta.get("title", "")
    url = meta.get("url", "")
    plain = f'{who}, "{title}", The Stanford Encyclopedia of Philosophy' + (f" ({when})" if when else "") + \
            f", Edward N. Zalta and Uri Nodelman (eds.), URL = <{url}> (accessed {accessed})."
    return {"plain": plain, "who": who, "title": title, "when": when, "url": url, "pubinfo": rev}


# ----------------------------------------------------------------------------------------------- Wikipedia

_wp_cache = DiskCache("wikipedia")


def fetch_summaries(lang: str, titles: list[str], *, pause: float = 0.5, echo=None) -> dict[str, dict | None]:
    """Lead extracts for up to twenty titles per request through the Action API (``prop=extracts``, intro only,
    plain text), with each page's latest revision id and timestamp and its canonical URL. One request per chunk
    is cached raw; a rate-limited or failed chunk is retried with a growing pause and, if it still fails, left
    uncached so the next run asks again. Redirects and title normalisation are followed and recorded.
    """
    out: dict[str, dict | None] = {}
    url = f"https://{lang}.wikipedia.org/w/api.php"
    for i in range(0, len(titles), 20):
        chunk = titles[i:i + 20]
        params = {"action": "query", "format": "json", "formatversion": "2", "prop": "extracts|revisions|info",
                  "exintro": "1", "explaintext": "1", "exlimit": "max", "rvprop": "ids|timestamp", "inprop": "url",
                  "redirects": "1", "titles": "|".join(chunk)}
        key = cache_key("wikipedia-extracts", url=url, params=params)
        hit = _wp_cache.get(key)
        raw = hit["raw"] if hit else None
        if raw is None:
            for attempt in range(6):
                try:
                    res = get(url, params=params)
                except Exception:  # noqa: BLE001
                    res = None
                if res is None or res.status_code == 429 or res.status_code >= 500:
                    time.sleep(4.0 * (attempt + 1))
                    continue
                if res.status_code != 200:
                    break
                raw = res.json()
                _wp_cache.put(key, request={"url": url, "params": params}, raw=raw, parsed=None)
                time.sleep(pause)
                break
        if raw is None:
            for t in chunk:
                out[t] = None
            if echo:
                echo(f"  chunk at {i} not fetched after retries")
            continue
        q = raw.get("query", {})
        rename = {r["from"]: r["to"] for r in (q.get("normalized") or []) + (q.get("redirects") or [])}
        pages = {p.get("title"): p for p in q.get("pages") or []}
        for t in chunk:
            final = t
            for _ in range(4):
                if final in rename and rename[final] != final:
                    final = rename[final]
            pg = pages.get(final)
            if not pg or pg.get("missing") or not (pg.get("extract") or "").strip():
                out[t] = None
                continue
            rev = (pg.get("revisions") or [{}])[0]
            out[t] = {"lang": lang, "title": pg["title"], "extract": pg["extract"].strip(), "revision": rev.get("revid"),
                      "timestamp": rev.get("timestamp"), "licence": "CC BY-SA 4.0",
                      "url": pg.get("fullurl") or f"https://{lang}.wikipedia.org/wiki/{quote(pg['title'].replace(' ', '_'))}"}
    return out


# ----------------------------------------------------------------------------------------------- the run

def fetch_sources(case: Path, run: Path, *, workers: int = 4, echo=print) -> Path:
    """For the nodes of a collect run: SEP metadata and Wikipedia summaries, into ``outputs/timeline/sources/``."""
    P = case_paths(case)
    nodes = json.loads((run / "nodes.json").read_text(encoding="utf-8"))
    out = P["sources"]
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    accessed = time.strftime("%Y-%m-%d")

    sep_ids = [(n["id"], n["ids"]["P3123"]) for n in nodes if n.get("ids", {}).get("P3123")]
    echo(f"SEP entries: {len(sep_ids)} …")
    sep: dict[str, dict] = {}
    for i, (q, eid) in enumerate(sep_ids):
        meta = fetch_sep(eid)
        sep[q] = meta
        if (i + 1) % 100 == 0:
            echo(f"  {i + 1}/{len(sep_ids)}")
    ok = sum(1 for m in sep.values() if m.get("ok"))
    (out / "sep.json").write_text(json.dumps({"accessed": accessed, "entries": sep}, ensure_ascii=False, indent=1), encoding="utf-8")
    echo(f"  {ok} parsed, {len(sep) - ok} not")

    todo = [(n["id"], n["wiki"]) for n in nodes if n.get("wiki")]
    echo(f"Wikipedia extracts: {len(todo)} nodes, twenty titles per request …")
    summaries: dict[str, dict] = {}
    en = [(q, w["en"]) for q, w in todo if w.get("en")]
    got = fetch_summaries("en", [t for _, t in en], echo=echo)
    for q, t in en:
        if got.get(t):
            summaries[q] = got[t]
    de = [(q, w["de"]) for q, w in todo if w.get("de") and q not in summaries]
    got = fetch_summaries("de", [t for _, t in de], echo=echo)
    for q, t in de:
        if got.get(t):
            summaries[q] = got[t]
    (out / "wikipedia.json").write_text(json.dumps({"accessed": accessed, "summaries": summaries}, ensure_ascii=False, indent=1), encoding="utf-8")
    echo(f"  {len(summaries)} with an extract")

    RunManifest(run_id=f"sources-{time.strftime('%Y%m%d-%H%M%S')}", step="timeline.sources",
                params={"collect_run": run.name, "workers": workers},
                inputs=[rel(run / "nodes.json"), "https://plato.stanford.edu/entries/", "https://*.wikipedia.org/api/rest_v1/page/summary/"],
                outputs=[rel(out / "sep.json"), rel(out / "wikipedia.json")], seconds=round(time.time() - t0, 1),
                notes=[f"sep parsed {ok}/{len(sep)}", f"wikipedia extracts {len(summaries)}/{len(todo)}"]).write(out)
    return out


def load_sources(case: Path) -> tuple[dict, dict]:
    P = case_paths(case)
    sep = json.loads((P["sources"] / "sep.json").read_text(encoding="utf-8")) if (P["sources"] / "sep.json").exists() else {"entries": {}}
    wp = json.loads((P["sources"] / "wikipedia.json").read_text(encoding="utf-8")) if (P["sources"] / "wikipedia.json").exists() else {"summaries": {}}
    return sep, wp
