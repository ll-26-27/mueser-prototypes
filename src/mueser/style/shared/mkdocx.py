"""A minimal .docx writer for synthetic fixtures. Never used on a real document.

Runs are ``"text"``, ``("text", "i")``, ``("text", "b")``, ``("text", "bi")``, ``TAB`` or ``("fn", id)``.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

TAB = object()
NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
FONT = '<w:rFonts w:ascii="{f}" w:hAnsi="{f}" w:cs="{f}"/>'


def run(item, font: str | None = None, size: int | None = None) -> str:
    props = (FONT.format(f=font) if font else "") + (f'<w:sz w:val="{size}"/>' if size else "")
    if item is TAB:
        return f"<w:r>{'<w:rPr>' + props + '</w:rPr>' if props else ''}<w:tab/></w:r>"
    if isinstance(item, tuple) and item[0] == "fn":
        return f'<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:footnoteReference w:id="{item[1]}"/></w:r>'
    text, flags = (item, "") if isinstance(item, str) else item
    props = ("<w:b/>" if "b" in flags else "") + ("<w:i/>" if "i" in flags else "") + props
    return f"<w:r>{'<w:rPr>' + props + '</w:rPr>' if props else ''}<w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r>"


def para(runs=(), style: str | None = None, left: int | None = None, hanging: int | None = None,
         tabs: tuple = (), after: int | None = None, font: str | None = None, size: int | None = None) -> str:
    ppr = f'<w:pStyle w:val="{style}"/>' if style else ""
    if tabs:
        ppr += "<w:tabs>" + "".join(f'<w:tab w:val="{v}" w:pos="{p}"/>' for p, v in tabs) + "</w:tabs>"
    if after is not None:
        ppr += f'<w:spacing w:after="{after}"/>'
    if left is not None or hanging is not None:
        ppr += f'<w:ind w:left="{left or 0}"' + (f' w:hanging="{hanging}"' if hanging else "") + "/>"
    if isinstance(runs, str):
        runs = (runs,)
    return f"<w:p>{'<w:pPr>' + ppr + '</w:pPr>' if ppr else ''}{''.join(run(r, font, size) for r in runs)}</w:p>"


def table(rows: list[list[str]], widths: tuple[int, ...]) -> str:
    grid = "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"
    body = ""
    for cells in rows:
        body += "<w:tr>" + "".join(
            f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/></w:tcPr>{c}</w:tc>' for c, w in zip(cells, widths)) + "</w:tr>"
    return f'<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/></w:tblPr>{grid}{body}</w:tbl>'


STYLES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles {NS}><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr></w:rPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr><w:rPr><w:b/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="720" w:right="720"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="FootnoteText"><w:name w:val="footnote text"/><w:basedOn w:val="Normal"/><w:rPr><w:sz w:val="20"/></w:rPr></w:style>
</w:styles>"""

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>{fn}</Types>"""
FN_TYPE = '<Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>"""
DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>{fn}</Relationships>"""
FN_REL = '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes" Target="footnotes.xml"/>'


def write_docx(path: Path, blocks: list[str], footnotes: dict[int, list] | None = None,
               page: tuple[int, int] = (12240, 15840), margins: tuple[int, int, int, int] = (1440, 1440, 1440, 1440)) -> Path:
    """blocks: paragraph and table XML in order. footnotes: {id: runs}. page and margins in twentieths of a point."""
    top, right, bottom, left = margins
    sect = (f'<w:sectPr><w:pgSz w:w="{page[0]}" w:h="{page[1]}"/>'
            f'<w:pgMar w:top="{top}" w:right="{right}" w:bottom="{bottom}" w:left="{left}" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>')
    document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document {NS}><w:body>{"".join(blocks)}{sect}</w:body></w:document>'
    parts = {"[Content_Types].xml": CONTENT_TYPES.format(fn=FN_TYPE if footnotes else ""), "_rels/.rels": RELS,
             "word/document.xml": document, "word/styles.xml": STYLES,
             "word/_rels/document.xml.rels": DOC_RELS.format(fn=FN_REL if footnotes else "")}
    if footnotes:
        notes = ('<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>'
                 '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>')
        for fid, runs in footnotes.items():
            ref = '<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:footnoteRef/></w:r>'
            body = para(runs, style="FootnoteText").replace("</w:pPr>", "</w:pPr>" + ref, 1)
            notes += f'<w:footnote w:id="{fid}">{body}</w:footnote>'
        parts["word/footnotes.xml"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:footnotes {NS}>{notes}</w:footnotes>'
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():  # fixed timestamp: the same input gives the same bytes
            z.writestr(zipfile.ZipInfo(name, date_time=(2026, 11, 19, 0, 0, 0)), data.encode("utf-8"))
    return path
