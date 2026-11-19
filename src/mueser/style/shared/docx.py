"""Read and edit a .docx as what it is: a zip of XML parts.

A part that no command touched is written back byte for byte. Text is addressed by character offset
within a paragraph, where a tab counts as one character (``\\t``) and a line break as one (``\\n``), so a
finding made on the extracted text can be applied to exactly the runs that hold it.
"""

from __future__ import annotations

import copy
import zipfile
from pathlib import Path

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
DOCUMENT = "word/document.xml"
FOOTNOTES = "word/footnotes.xml"
STYLES = "word/styles.xml"


def q(tag: str) -> str:
    return f"{{{W}}}{tag}"


def attr(el, name: str, default=None):
    return default if el is None else el.get(q(name), default)


class Docx:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        with zipfile.ZipFile(self.path) as z:
            self.infos = z.infolist()
            self.parts: dict[str, bytes] = {i.filename: z.read(i.filename) for i in self.infos}
        self._trees: dict[str, etree._Element] = {}
        self.dirty: set[str] = set()

    def tree(self, name: str):
        if name not in self.parts:
            return None
        if name not in self._trees:
            self._trees[name] = etree.fromstring(self.parts[name])
        return self._trees[name]

    @property
    def document(self):
        return self.tree(DOCUMENT)

    @property
    def body(self):
        return self.document.find(q("body"))

    @property
    def footnotes(self):
        return self.tree(FOOTNOTES)

    def touch(self, name: str = DOCUMENT) -> None:
        self.dirty.add(name)

    def save(self, out: Path | str) -> Path:
        out = Path(out)
        if out.resolve() == self.path.resolve():
            raise ValueError("refusing to overwrite the source document; write to a run folder")
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for info in self.infos:
                data = self.parts[info.filename]
                if info.filename in self.dirty:
                    data = etree.tostring(self._trees[info.filename], xml_declaration=True, encoding="UTF-8",
                                          standalone=True)
                z.writestr(info, data)
        return out

    # -- notes ------------------------------------------------------------------------------------

    def footnote_list(self) -> list[tuple[int, str, etree._Element]]:
        """(n, id, element) in the order the notes are referenced in the text; n starts at 1."""
        root = self.footnotes
        if root is None:
            return []
        by_id = {attr(f, "id"): f for f in root.findall(q("footnote")) if attr(f, "type") is None}
        out, seen = [], set()
        for ref in self.document.iter(q("footnoteReference")):
            fid = attr(ref, "id")
            if fid in by_id and fid not in seen:
                seen.add(fid)
                out.append((len(out) + 1, fid, by_id[fid]))
        return out

    def text(self) -> str:
        """Every paragraph of the body in order, then every footnote, one per line."""
        lines = [para_text(p) for p in self.document.iter(q("p"))]
        for n, _, f in self.footnote_list():
            lines.append(f"[{n}] " + "\n".join(para_text(p) for p in f.iter(q("p"))))
        return "\n".join(lines)


# -- paragraphs as text ---------------------------------------------------------------------------

def segments(p) -> list[tuple[etree._Element, str, str]]:
    """The paragraph's visible pieces in order: (node, kind, text) with kind 't', 'tab' or 'br'."""
    out = []
    for el in p.iter():
        if el.tag == q("t"):
            out.append((el, "t", el.text or ""))
        elif el.tag == q("tab") and el.getparent().tag == q("r"):
            out.append((el, "tab", "\t"))
        elif el.tag in (q("br"), q("cr")):
            out.append((el, "br", "\n"))
        elif el.tag == q("noBreakHyphen"):
            out.append((el, "br", "‑"))
    return out


def para_text(p) -> str:
    return "".join(s[2] for s in segments(p))


def run_of(node):
    while node is not None and node.tag != q("r"):
        node = node.getparent()
    return node


def _on(rpr, tag: str) -> bool:
    el = None if rpr is None else rpr.find(q(tag))
    return el is not None and attr(el, "val", "true") not in ("0", "false", "off")


def run_flags(run) -> tuple[bool, bool]:
    rpr = None if run is None else run.find(q("rPr"))
    return _on(rpr, "b"), _on(rpr, "i")


def italic_spans(p) -> list[tuple[int, int]]:
    """Character ranges set in italic by direct run formatting (titles, foreign words)."""
    out, pos = [], 0
    for node, _, text in segments(p):
        if text and run_flags(run_of(node))[1]:
            if out and out[-1][1] == pos:
                out[-1] = (out[-1][0], pos + len(text))
            else:
                out.append((pos, pos + len(text)))
        pos += len(text)
    return out


def style_id(p) -> str:
    ppr = p.find(q("pPr"))
    st = None if ppr is None else ppr.find(q("pStyle"))
    return attr(st, "val", "") or ""


def replace_span(p, start: int, end: int, new: str) -> None:
    """Replace characters [start, end) of the paragraph's text with ``new``, inside the runs that hold them.

    The replacement takes the formatting of the run where the span begins. A span that crosses a tab or
    a line break is refused: those are structure, not text.
    """
    segs, pos, first = segments(p), 0, True
    if start == end:  # an insertion goes at the end of the text node that ends at ``start``, else the start of the next
        for node, kind, text in segs:
            if kind == "t" and pos <= start <= pos + len(text):
                node.text = text[:start - pos] + new + text[start - pos:]
                node.set(XML_SPACE, "preserve")
                return
            pos += len(text)
        raise ValueError("no text run at that position")
    for node, kind, text in segs:
        a, b = pos, pos + len(text)
        pos = b
        if b <= start or a >= end:
            continue
        if kind != "t":
            raise ValueError("the span crosses a tab or line break")
        lo, hi = max(start, a) - a, min(end, b) - a
        node.text = text[:lo] + (new if first else "") + text[hi:]
        node.set(XML_SPACE, "preserve")
        first = False
    if first:
        raise ValueError("span is outside the paragraph")


def apply_edits(text: str, edits: list[tuple[int, int, str]]) -> str:
    for s, e, new in sorted(edits, reverse=True):
        text = text[:s] + new + text[e:]
    return text


# -- building runs from light markup (used by the CV renderer) --------------------------------------

def to_markup(p) -> str:
    """The paragraph as text with *italic*, **bold** and ***both*** marked; tabs and breaks kept."""
    out, cur, buf = [], (False, False), ""

    def flush():
        nonlocal buf
        if buf:
            mark = "*" * ((2 if cur[0] else 0) + (1 if cur[1] else 0))
            lead = buf[:len(buf) - len(buf.lstrip(" "))]
            trail = buf[len(buf.rstrip(" ")):] if buf.strip(" ") else ""
            core = buf.strip(" ")
            out.append(lead + (mark + core + mark if core and mark else core) + trail)
            buf = ""

    for node, kind, text in segments(p):
        if kind != "t":
            flush()
            out.append(text)
            continue
        flags = run_flags(run_of(node))
        if flags != cur:
            flush()
            cur = flags
        buf += text.replace("\\", "\\\\").replace("*", "\\*")
    flush()
    return "".join(out)


def parse_markup(s: str) -> list[tuple[str, bool, bool]]:
    """Inverse of ``to_markup``: [(text, bold, italic)], with '\\t' and '\\n' as their own pieces."""
    out: list[tuple[str, bool, bool]] = []
    bold = italic = False
    buf, i = "", 0

    def flush():
        nonlocal buf
        if buf:
            out.append((buf, bold, italic))
            buf = ""

    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] in "\\*":
            buf += s[i + 1]
            i += 2
        elif ch == "*":
            n = 1
            while i + n < len(s) and s[i + n] == "*" and n < 3:
                n += 1
            flush()
            if n in (2, 3):
                bold = not bold
            if n in (1, 3):
                italic = not italic
            i += n
        elif ch in "\t\n":
            flush()
            out.append((ch, False, False))
            i += 1
        else:
            buf += ch
            i += 1
    flush()
    return out


def base_rpr(p):
    """The run properties that carry most of the paragraph's text: the font the entry is set in."""
    weight: dict[int, int] = {}
    keep: dict[int, etree._Element | None] = {}
    for node, kind, text in segments(p):
        r = run_of(node)
        if r is None:
            continue
        keep[id(r)] = r.find(q("rPr"))
        weight[id(r)] = weight.get(id(r), 0) + (len(text) if kind == "t" else 0)
    if not weight:
        ppr = p.find(q("pPr"))
        mark = None if ppr is None else ppr.find(q("rPr"))
        return None if mark is None else copy.deepcopy(mark)
    best = max(weight, key=lambda k: weight[k])
    return None if keep[best] is None else copy.deepcopy(keep[best])


def set_runs(p, markup: str) -> None:
    """Replace the paragraph's content with runs built from markup; paragraph properties are kept as they are."""
    base = base_rpr(p)
    if base is not None:
        base.tag = q("rPr")
        for tag in ("b", "bCs", "i", "iCs", "ins", "del", "moveFrom", "moveTo", "rPrChange"):
            for el in base.findall(q(tag)):
                base.remove(el)
    for child in list(p):
        if child.tag != q("pPr"):
            p.remove(child)
    for text, bold, italic in parse_markup(markup):
        r = etree.SubElement(p, q("r"))
        rpr = copy.deepcopy(base) if base is not None else etree.Element(q("rPr"))
        for flag, tags in ((bold, ("b", "bCs")), (italic, ("i", "iCs"))):
            if flag:
                for tag in tags:
                    rpr.insert(0, etree.Element(q(tag)))
        if len(rpr):
            r.append(rpr)
        if text == "\t":
            etree.SubElement(r, q("tab"))
        elif text == "\n":
            etree.SubElement(r, q("br"))
        else:
            t = etree.SubElement(r, q("t"))
            t.text = text
            t.set(XML_SPACE, "preserve")


def c14n(el) -> bytes:
    return etree.tostring(el, method="c14n")
