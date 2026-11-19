"""cv extract: the CV as data (sections, entries, a format fingerprint each) and a geometry report."""

from __future__ import annotations

import tempfile
from collections import Counter
from pathlib import Path

import yaml

from mueser.shared.cache import sha256_file
from mueser.style.shared import pdf
from mueser.style.shared.docx import Docx, attr, q, run_of, segments

from . import fingerprint, is_heading, unit_markup, unit_text, units

HEADER = """\
# The CV as data, written by `cv extract`. Each entry is one paragraph or one table row of the document.
#
# To add an entry, put a new item where it should appear in its section, with only a `text` line:
#     - text: "2026\\tTitle of the talk, *Name of the Venue*, Place"
# \\t is a tab (or the next table cell), *...* is italic, **...** is bold, \\n is a line break.
# The new entry is a copy of the entry above it (the entry below, if it is first), so indents, tab
# stops, fonts and spacing are that entry's. To copy a different one, add `like: <its id>`.
# Changing the `text` of an existing entry changes only that entry's text. Do not edit ids,
# source_index or fingerprints: they tie each entry to its place in the document.
"""

FRONT = "(front matter)"


def _mm(twips: str | None) -> float | None:
    return None if twips is None else round(int(twips) / 1440 * 25.4, 1)


def geometry(doc: Docx) -> dict:
    sect = doc.body.find(q("sectPr"))
    size = None if sect is None else sect.find(q("pgSz"))
    mar = None if sect is None else sect.find(q("pgMar"))
    fonts: Counter[str] = Counter()
    for node, kind, text in (s for p in doc.document.iter(q("p")) for s in segments(p)):
        if kind != "t":
            continue
        rpr = run_of(node).find(q("rPr")) if run_of(node) is not None else None
        rf = None if rpr is None else rpr.find(q("rFonts"))
        fonts[attr(rf, "ascii") or "(from the style)"] += len(text)
    return {
        "page_mm": {"width": _mm(attr(size, "w")), "height": _mm(attr(size, "h"))},
        "margins_mm": {k: _mm(attr(mar, k)) for k in ("top", "right", "bottom", "left")},
        "fonts_by_characters": dict(fonts.most_common()),
        "sections_in_document": len(list(doc.document.iter(q("sectPr")))),
    }


def extract(source: Path, out: Path, echo=print) -> dict:
    doc = Docx(source)
    us = units(doc)
    sections: list[dict] = [{"title": FRONT, "source_index": None, "entries": []}]
    for u in us:
        text = unit_text(u)
        if not text.strip():
            continue  # spacer paragraphs stay in the document; render copies them where the layout uses them
        if is_heading(u):
            sections.append({"title": text.strip(), "source_index": u["index"], "entries": []})
            continue
        sections[-1]["entries"].append({"id": f"u{u['index']:03d}", "source_index": u["index"], "kind": u["kind"],
                                        "text": unit_markup(u), "fingerprint": fingerprint(u)})
    if not sections[0]["entries"]:
        sections.pop(0)
    geo = geometry(doc)
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = pdf.to_pdf(source, Path(tmp)) if pdf.soffice() else None
        geo["pages"] = len(pdf.page_texts(pdf_path)) if pdf_path else None
    data = {"source": {"file": source.name, "sha256": sha256_file(source)}, "document": geo, "sections": sections}
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(f"{out} exists; it may hold entries you added. Move it or choose another --out.")
    out.write_text(HEADER + "\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")

    skipped = sum(1 for child in doc.body if child.tag not in (q("p"), q("tbl"), q("sectPr")))
    echo(f"{source.name}: {len(us)} paragraphs and table rows, {len(sections)} sections, "
         f"{sum(len(s['entries']) for s in sections)} entries")
    echo(f"page {geo['page_mm']['width']} x {geo['page_mm']['height']} mm; margins {geo['margins_mm']}")
    echo("fonts: " + ", ".join(f"{k} ({v} characters)" for k, v in geo["fonts_by_characters"].items()))
    echo(f"pages: {geo['pages']}" if geo["pages"] else pdf.INSTALL_HINT)
    if skipped:
        echo(f"{skipped} block(s) that are neither a paragraph nor a table (content controls, etc.) were not read")
    for s in sections:
        kinds = Counter(e["fingerprint"] for e in s["entries"])
        echo(f"  {s['title']}: {len(s['entries'])} entries, {len(kinds)} format(s)")
    echo(f"wrote {out}")
    return data
