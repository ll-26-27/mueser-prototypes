"""Citations for a passage of a page: plain, Markdown, and CSL-JSON (which Zotero imports from the clipboard).

The bibliographic record comes from ``inputs/metadata.json``; the provenance clause from the build (which reader,
which run, which build, how many decisions) and, for a translation, from the translation run. CSL has no slot
for provenance, so it travels in ``note``. A synthetic document says so in every form.
"""

from __future__ import annotations

import json
import re


def split_name(name: str) -> dict:
    name = name.strip()
    if "," in name:
        fam, giv = [p.strip() for p in name.split(",", 1)]
        return {"family": fam, "given": giv}
    parts = name.split()
    if len(parts) == 1:
        return {"family": parts[0]}
    return {"family": parts[-1], "given": " ".join(parts[:-1])}


def year_of(date: str | None) -> int | None:
    if not date:
        return None
    m = re.search(r"\d{4}", str(date))
    return int(m.group(0)) if m else None


def line_label(line_ids: list[str]) -> str:
    nums = sorted(int(x[1:]) for x in line_ids if re.fullmatch(r"l\d+", x))
    if not nums:
        return ""
    if len(nums) == 1:
        return f"l. {nums[0]}"
    return f"ll. {nums[0]}–{nums[-1]}"


def authors_short(doc: dict) -> str:
    au = doc.get("author") or []
    fams = [split_name(a)["family"] for a in au]
    if not fams:
        return doc.get("archive") or ""
    if len(fams) == 1:
        return fams[0]
    if len(fams) == 2:
        return f"{fams[0]} and {fams[1]}"
    return f"{fams[0]} et al."


def provenance_sentence(prov: dict) -> str:
    parts = []
    t = prov.get("transcription") or {}
    if t:
        s = f"Transcription: medoid {t.get('reader')}, run {t.get('run_id')}, settled build {t.get('build_id')}"
        n = t.get("decisions")
        if n:
            s += f", {n} decision{'s' if n != 1 else ''}"
            if t.get("who"):
                s += f" by {t['who']}"
        parts.append(s + ".")
    tr = prov.get("translation") or {}
    if tr:
        s = f"Translation: {tr.get('model')}, run {tr.get('run_id')}"
        if tr.get("block"):
            s += f", block {tr['block']}"
            if tr.get("decided_by"):
                s += f" decided by {tr['decided_by']}"
        parts.append(s + ".")
    return " ".join(parts)


def citation(meta: dict, doc_id: str, page_id: str, line_ids: list[str], *, quote: str = "", layer: str = "transcription",
             provenance: dict | None = None, repo_path: str = "") -> dict:
    """Return {"plain", "markdown", "csl"} for a passage."""
    doc = (meta.get("docs") or {}).get(doc_id) or {"title": doc_id, "pages": {}}
    page = (doc.get("pages") or {}).get(page_id) or {}
    label = page.get("label") or page_id
    lines = line_label(line_ids)
    where = ", ".join(x for x in (label, lines) if x)
    synthetic = bool(doc.get("synthetic"))
    prov = provenance_sentence(provenance or {})

    imprint = ", ".join(x for x in (doc.get("place"), str(doc.get("date")) if doc.get("date") else None) if x)
    head = f"{authors_short(doc)}, {doc.get('title', doc_id)}" if authors_short(doc) else doc.get("title", doc_id)
    if imprint:
        head += f" ({imprint})"
    arch = ", ".join(x for x in (doc.get("archive"), doc.get("shelfmark")) if x)
    plain = f"{head}, {where}."
    if arch and doc.get("type") in ("manuscript", "personal_communication", "letter"):
        plain = f"{head}, {where}. {arch}."
    if synthetic:
        plain += " Synthetic page: invented text rendered for testing, not a historical source."
    if layer == "translation":
        plain += " English translation."
    if prov:
        plain += " " + prov

    md_lines = []
    if quote:
        md_lines.append("> " + quote.replace("\n", "\n> "))
        md_lines.append("")
    md_lines.append(f"[^1]: {plain}" + (f" `{repo_path}`" if repo_path else ""))
    markdown = "\n".join(md_lines)

    csl: dict = {"type": doc.get("type") or "document", "title": doc.get("title", doc_id)}
    if doc.get("author"):
        csl["author"] = [split_name(a) for a in doc["author"]]
    y = year_of(doc.get("date"))
    if y:
        csl["issued"] = {"date-parts": [[y]]}
    for src, dst in (("publisher", "publisher"), ("place", "publisher-place"), ("url", "URL"), ("archive", "archive"),
                     ("shelfmark", "archive_location"), ("language", "language")):
        if doc.get(src):
            csl[dst] = doc[src]
    loc = re.sub(r"^(p\.|pp\.|S\.|fol\.)\s*", "", label)
    csl["locator"] = loc + (f", {lines}" if lines else "")
    csl["label"] = "page"
    note = prov
    if synthetic:
        note = ("Synthetic page, not a historical source. " + note).strip()
    if layer == "translation":
        note = ("English translation. " + note).strip()
    if note:
        csl["note"] = note
    return {"plain": plain, "markdown": markdown, "csl": csl, "csl_json": json.dumps(csl, ensure_ascii=False, indent=1)}
