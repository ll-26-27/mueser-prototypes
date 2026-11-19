"""mueser.reading: the reading room.

One page per scan: the image on the left, the settled transcription and its translation on the right, in
register. Selecting text lights the lines of the scan it came from; a passage copies with its citation; the
open differences between readers (transcription) and between translators (translation) are decided here, and
every decision, question, issue and excerpt is appended to ``outputs/reading/log.jsonl``.

Steps, each a command of ``python -m mueser.reading``:

- ``settle``    consensus + medoid reading -> an immutable build with diplomatic lines and remapped spans
- ``anchor``    settled lines -> boxes, by aligning them to a reading that has coordinates
- ``translate`` settled lines -> sentence segments with line references, from two models
- ``build``     build + translation + log -> one self-contained ``index.html``
- ``serve``     the page on 127.0.0.1 with ``POST /api/log`` appending to the log
- ``apply``     log decisions -> a new build
- ``ingest``    exported browser logs -> the log
- ``cite``      a citation for a page and line range
- ``init-doc``  a ``metadata.json`` skeleton from ``ingest``'s ``pages.json``
"""

from pathlib import Path

WEB = Path(__file__).parent / "web"


def case_paths(case: Path) -> dict[str, Path]:
    case = Path(case)
    return {
        "case": case,
        "pages": case / "inputs" / "pages",
        "metadata": case / "inputs" / "metadata.json",
        "consensus": case / "inputs" / "readings" / "consensus",
        "medoid": case / "inputs" / "readings" / "medoid",
        "segmentation": case / "inputs" / "readings" / "segmentation",
        "out": case / "outputs",
        "reading": case / "outputs" / "reading",
        "log": case / "outputs" / "reading" / "log.jsonl",
        "inbox": case / "outputs" / "reading" / "inbox",
        "builds": case / "outputs" / "reading" / "builds",
        "runs": case / "outputs" / "reading" / "runs",
        "index": case / "outputs" / "index.html",
    }
