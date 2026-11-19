"""Page counts through LibreOffice. Absent LibreOffice is reported, never worked around."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

MAC_SOFFICE = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
INSTALL_HINT = "LibreOffice is not installed (brew install --cask libreoffice); page counts were skipped."


def soffice() -> str | None:
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    return str(MAC_SOFFICE) if MAC_SOFFICE.exists() else None


def to_pdf(docx: Path, outdir: Path) -> Path | None:
    exe = soffice()
    if not exe:
        return None
    outdir.mkdir(parents=True, exist_ok=True)
    subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(docx)], check=True,
                   capture_output=True, timeout=180)
    pdf = outdir / (Path(docx).stem + ".pdf")
    return pdf if pdf.exists() else None


def page_texts(pdf: Path) -> list[str]:
    from pypdf import PdfReader
    return [(page.extract_text() or "") for page in PdfReader(str(pdf)).pages]
