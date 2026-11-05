"""Read and write transcription formats: PAGE-XML (the archival interchange format Transkribus, eScriptorium,
Kraken and OCR-D all speak), plain text (one line per text line), and a minimal TEI export.

A PageResult with no bboxes (VLM output) still gets valid PAGE-XML: one TextRegion, TextLines without Coords
points except a zero polygon, and the text. That keeps every backend's output in one format for evaluation.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from xml.sax.saxutils import escape

from .backends.base import Line, PageResult

PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"


def _poly(bbox: list[float] | None) -> str:
    if not bbox:
        return "0,0 0,0 0,0 0,0"
    x, y, w, h = bbox
    x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
    return f"{x},{y} {x + w},{y} {x + w},{y + h} {x},{y + h}"


def to_page_xml(result: PageResult, image_filename: str, width: int, height: int) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<PcGts xmlns="{PAGE_NS}">',
        "  <Metadata>",
        f"    <Creator>mueser/{escape(result.backend)}/{escape(result.model)}</Creator>",
        f"    <Created>{now}</Created>",
        f"    <LastChange>{now}</LastChange>",
        f"    <Comments>{escape('; '.join(result.notes))}</Comments>",
        "  </Metadata>",
        f'  <Page imageFilename="{escape(image_filename)}" imageWidth="{width}" imageHeight="{height}">',
        '    <TextRegion id="r1">',
        f'      <Coords points="{_poly([0, 0, width, height])}"/>',
    ]
    for i, line in enumerate(result.lines):
        conf = f' conf="{line.confidence:.3f}"' if line.confidence is not None else ""
        parts.append(f'      <TextLine id="l{i + 1}">')
        parts.append(f'        <Coords points="{_poly(line.bbox)}"/>')
        if line.baseline:
            parts.append('        <Baseline points="' + " ".join(f"{int(x)},{int(y)}" for x, y in line.baseline) + '"/>')
        parts.append(f"        <TextEquiv{conf}><Unicode>{escape(line.text)}</Unicode></TextEquiv>")
        parts.append("      </TextLine>")
    parts += ["    </TextRegion>", "  </Page>", "</PcGts>", ""]
    return "\n".join(parts)


def from_page_xml(path: Path) -> list[Line]:
    """Read TextLines (text + bbox from Coords) from a PAGE-XML file, any 2013+ namespace."""
    from lxml import etree

    tree = etree.parse(str(path))
    root = tree.getroot()
    ns = root.nsmap.get(None) or PAGE_NS
    nsmap = {"p": ns}
    out = []
    for tl in root.iterfind(".//p:TextLine", nsmap):
        text_el = tl.find("p:TextEquiv/p:Unicode", nsmap)
        text = (text_el.text or "") if text_el is not None else ""
        bbox = None
        coords = tl.find("p:Coords", nsmap)
        if coords is not None and coords.get("points"):
            pts = [tuple(map(float, p.split(","))) for p in coords.get("points").split()]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            if max(xs) > 0 or max(ys) > 0:
                bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
        out.append(Line(text=text, bbox=bbox))
    return out


def to_text(result: PageResult) -> str:
    return "\n".join(l.text for l in result.lines) + "\n"


def read_text_lines(path: Path) -> list[str]:
    return [l.rstrip("\n") for l in Path(path).read_text(encoding="utf-8").splitlines()]


def to_tei(doc_id: str, pages: list[tuple[str, list[Line]]], title: str = "") -> str:
    """Minimal TEI: one <pb/> per page, one <lb/> per line, text diplomatic as transcribed."""
    body = []
    for page_id, lines in pages:
        body.append(f'      <pb n="{escape(page_id)}"/>')
        for l in lines:
            body.append(f"      <lb/>{escape(l.text)}")
    return "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">',
        "  <teiHeader><fileDesc>",
        f"    <titleStmt><title>{escape(title or doc_id)}</title></titleStmt>",
        "    <publicationStmt><p>Machine transcription; see run.json for backend, model and prompt hash.</p></publicationStmt>",
        f"    <sourceDesc><p>{escape(doc_id)}</p></sourceDesc>",
        "  </fileDesc></teiHeader>",
        "  <text><body><div>",
        *body,
        "  </div></body></text>",
        "</TEI>",
        "",
    ])
