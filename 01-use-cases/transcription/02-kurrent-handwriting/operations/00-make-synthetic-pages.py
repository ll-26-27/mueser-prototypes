"""Step 0 (deterministic code): render the synthetic letters into Kurrent-style page images with exact ground truth.

    uv run python 01-use-cases/transcription/02-kurrent-handwriting/operations/00-make-synthetic-pages.py

Uses Wiegel Kurrent (regular and bold) from models/fonts/. Ground truth is the rendered lines (inputs/gt/synth-*.txt).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mueser.text.synth import PageSpec, render  # noqa: E402

FONTS = ROOT / "models" / "fonts" / "WiegelKurrent.unz1t"
REG = str(FONTS / "WiegelKurrent.unz1t.ttf")
BOLD = str(FONTS / "WiegelKurrent.unz1tB.ttf")
TEXT = HERE.parent / "inputs" / "synthetic-text" / "briefe.txt"
PAGES = HERE.parent / "inputs" / "pages"
GT = HERE.parent / "inputs" / "gt"

SPECS = [
    PageSpec(font=REG, font_size=46, line_gap=1.5, paper=(240, 232, 210), ink=(55, 40, 30), seed=11),
    PageSpec(font=REG, font_size=44, line_gap=1.5, blur=0.6, speckle=0.003, rotate_deg=-0.6, paper=(236, 226, 200), ink=(60, 45, 35), seed=12),
    PageSpec(font=BOLD, font_size=42, line_gap=1.5, blur=0.4, paper=(242, 236, 218), ink=(45, 35, 30), seed=13),
]


def sections(text: str) -> list[tuple[str, str]]:
    out, head, body = [], None, []
    for line in text.splitlines():
        if line.startswith("# "):
            if head is not None:
                out.append((head, "\n".join(body).strip()))
            head, body = line[2:].strip(), []
        else:
            body.append(line)
    if head is not None:
        out.append((head, "\n".join(body).strip()))
    return out


def main() -> None:
    for i, ((head, body), spec) in enumerate(zip(sections(TEXT.read_text(encoding="utf-8")), SPECS), 1):
        pid = f"synth-{i:02d}"
        meta = render(body, spec, PAGES / f"{pid}.png", GT / f"{pid}.txt", header=head)
        print(pid, meta["lines"], "lines", meta["chars"], "chars", Path(spec.font).name)


if __name__ == "__main__":
    main()
