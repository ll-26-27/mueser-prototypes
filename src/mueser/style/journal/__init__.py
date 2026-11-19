"""An article brought to a journal's house style: measure the journal, propose the changes, apply the decided ones."""

from __future__ import annotations

import re
from pathlib import Path

MODEL = "google/gemini-3.8-flash"
# Restyling a citation is copying after a pattern. Left unset, the first run spent 30,717 thinking tokens on four notes.
REASONING = {"effort": "low"}


def squash(text: str) -> str:
    """One space for every run of whitespace: PDF text breaks lines inside sentences."""
    return re.sub(r"\s+", " ", text).strip()


def read_sample(path: Path) -> tuple[str, int | None]:
    """The whole text of a sample article and its page count where the format has pages."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from mueser.style.shared.pdf import page_texts
        pages = page_texts(path)
        return "\n".join(pages), len(pages)
    if suffix == ".docx":
        from mueser.style.shared.docx import Docx
        return Docx(path).text(), None
    return path.read_text(encoding="utf-8"), None
