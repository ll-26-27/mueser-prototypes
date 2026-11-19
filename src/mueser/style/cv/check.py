"""cv check: page count before and after, and the first page that differs. A longer CV stops here."""

from __future__ import annotations

import tempfile
from pathlib import Path

from mueser.style.shared import pdf


def check(before: Path, after: Path, echo=print) -> int:
    """Exit status: 0 same page count (or check skipped), 2 the page count grew."""
    if not pdf.soffice():
        echo(pdf.INSTALL_HINT)
        echo("Open both files in Word and compare the page count by eye until it is installed.")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        a = pdf.to_pdf(before, Path(tmp) / "before")
        b = pdf.to_pdf(after, Path(tmp) / "after")
        if not a or not b:
            echo("LibreOffice produced no PDF; nothing was compared")
            return 0
        ta, tb = pdf.page_texts(a), pdf.page_texts(b)
    echo(f"pages before: {len(ta)}   pages after: {len(tb)}")
    first = next((i + 1 for i, (x, y) in enumerate(zip(ta, tb)) if x != y), None)
    if first is None and len(ta) != len(tb):
        first = min(len(ta), len(tb)) + 1
    echo(f"first page that differs: {first if first else 'none'}")
    echo("(pages are laid out by LibreOffice, which can break lines differently from Word; the comparison holds between these two files)")
    if len(tb) > len(ta):
        echo(f"The CV grew by {len(tb) - len(ta)} page(s). Nothing was shrunk to fit; decide what to cut.")
        return 2
    return 0
