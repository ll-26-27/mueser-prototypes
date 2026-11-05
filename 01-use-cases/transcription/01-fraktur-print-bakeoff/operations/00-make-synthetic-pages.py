"""Step 0 (deterministic code): render the synthetic travel journal into Fraktur page images with exact ground truth.

    uv run python 01-use-cases/transcription/01-fraktur-print-bakeoff/operations/00-make-synthetic-pages.py

One page per `#` section of inputs/synthetic-text/reisetagebuch-1786.txt, in UnifrakturMaguntia (a Fraktur
revival, OFL). Each page gets a different, recorded degradation (clean; blur; speckle + blur; slight rotation;
a bolder second face) so the backends are not scored on one ideal image. Ground truth is the rendered lines
themselves (inputs/gt/synth-*.txt); the rendering parameters sit beside each image as JSON.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from mueser.text.synth import PageSpec, render  # noqa: E402

FONTS = ROOT / "models" / "fonts"
MAGUNTIA = str(FONTS / "UnifrakturMaguntia-Book.ttf")
COOK = str(FONTS / "UnifrakturCook-Bold.ttf")
TEXT = HERE.parent / "inputs" / "synthetic-text" / "reisetagebuch-1786.txt"
PAGES = HERE.parent / "inputs" / "pages"
GT = HERE.parent / "inputs" / "gt"

# One spec per section, in order. Degradations are deliberate and recorded.
SPECS = [
    PageSpec(font=MAGUNTIA, font_size=40, seed=1),
    PageSpec(font=MAGUNTIA, font_size=40, blur=0.8, seed=2),
    PageSpec(font=MAGUNTIA, font_size=38, blur=0.5, speckle=0.004, seed=3),
    PageSpec(font=MAGUNTIA, font_size=40, rotate_deg=0.8, speckle=0.002, seed=4),
    PageSpec(font=COOK, font_size=36, blur=0.3, seed=5),
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
    secs = sections(TEXT.read_text(encoding="utf-8"))
    for i, ((head, body), spec) in enumerate(zip(secs, SPECS), 1):
        pid = f"synth-{i:02d}"
        meta = render(body, spec, PAGES / f"{pid}.png", GT / f"{pid}.txt", header=head)
        print(pid, meta["lines"], "lines", meta["chars"], "chars", Path(spec.font).name, f"blur={spec.blur} speckle={spec.speckle} rot={spec.rotate_deg}")


if __name__ == "__main__":
    main()
