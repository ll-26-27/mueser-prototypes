"""The CV as a list of units (paragraphs and table rows), extended by cloning a neighbour's XML."""

from __future__ import annotations

import re

from mueser.style.shared.docx import attr, para_text, q, run_flags, run_of, segments, style_id, to_markup

HEADING_STYLE = re.compile(r"heading|title|section|berschrift", re.IGNORECASE)


def units(doc) -> list[dict]:
    """Every paragraph and table row directly under the body, in order: {index, kind, el}."""
    out = []
    for child in doc.body:
        if child.tag == q("p"):
            out.append({"kind": "paragraph", "el": child})
        elif child.tag == q("tbl"):
            out.extend({"kind": "row", "el": tr} for tr in child.findall(q("tr")))
    for i, u in enumerate(out):
        u["index"] = i
    return out


def cells(tr) -> list:
    return tr.findall(q("tc"))


def unit_markup(u) -> str:
    """Text with emphasis marked. A row is its cells joined by tabs; paragraphs within a cell by line breaks."""
    if u["kind"] == "paragraph":
        return to_markup(u["el"])
    return "\t".join("\n".join(to_markup(p) for p in tc.findall(q("p"))) for tc in cells(u["el"]))


def unit_text(u) -> str:
    if u["kind"] == "paragraph":
        return para_text(u["el"])
    return "\t".join("\n".join(para_text(p) for p in tc.findall(q("p"))) for tc in cells(u["el"]))


def is_heading(u) -> bool:
    """A section heading: a heading style, or a short line with no tab that is all bold or all capitals."""
    if u["kind"] != "paragraph":
        return False
    p, text = u["el"], para_text(u["el"]).strip()
    if not text:
        return False
    if HEADING_STYLE.search(style_id(p)):
        return True
    if "\t" in text or len(text.split()) > 8:
        return False
    runs = [run_of(n) for n, kind, t in segments(p) if kind == "t" and t.strip()]
    letters = [c for c in text if c.isalpha()]
    all_bold = bool(runs) and all(run_flags(r)[0] for r in runs)
    caps = bool(runs) and all(r.find(q("rPr")) is not None and (r.find(q("rPr")).find(q("smallCaps")) is not None
                                                               or r.find(q("rPr")).find(q("caps")) is not None) for r in runs)
    return all_bold or caps or (len(letters) > 2 and text.upper() == text)


def fingerprint(u) -> str:
    """The format a new entry inherits, as one line: style, indents, tab stops, spacing, run pattern."""
    if u["kind"] == "row":
        widths = [attr(tc.find(q("tcPr")).find(q("tcW")), "w", "?") if tc.find(q("tcPr")) is not None
                  and tc.find(q("tcPr")).find(q("tcW")) is not None else "?" for tc in cells(u["el"])]
        return f"row cells={len(widths)} widths={','.join(widths)}"
    p = u["el"]
    ppr = p.find(q("pPr"))
    bits = [f"style={style_id(p) or '(none)'}"]
    if ppr is not None:
        ind, sp, jc, tabs = ppr.find(q("ind")), ppr.find(q("spacing")), ppr.find(q("jc")), ppr.find(q("tabs"))
        if ind is not None:
            bits += [f"{k}={attr(ind, k)}" for k in ("left", "start", "hanging", "firstLine", "right") if attr(ind, k)]
        if tabs is not None:
            bits.append("tabs=" + ",".join(f"{attr(t, 'pos')}{(attr(t, 'val') or 'left')[0].upper()}" for t in tabs))
        if sp is not None:
            bits += [f"{k}={attr(sp, k)}" for k in ("before", "after", "line") if attr(sp, k)]
        if jc is not None:
            bits.append(f"align={attr(jc, 'val')}")
    pattern, last = [], None
    for node, kind, _ in segments(p):
        b, i = run_flags(run_of(node))
        name = "tab" if kind == "tab" else "break" if kind == "br" else ("bold-italic" if b and i else "bold" if b else "italic" if i else "plain")
        if name != last:
            pattern.append(name)
            last = name
    bits.append("runs=" + "|".join(pattern))
    return " ".join(bits)
