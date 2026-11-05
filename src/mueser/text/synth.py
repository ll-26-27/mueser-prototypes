"""Synthetic test pages: render German text in a Fraktur or Kurrent-style font to a page image, with the text as
ground truth. Because the ground truth is known exactly, the bake-off can report a CER before any page has been
hand-corrected. Noise (slight rotation, blur, speckle, yellowed paper) is added so backends are not scored on a
flat ideal; the parameters are written next to each page.

Synthetic pages are a check on the pipeline, not a measurement of real sources: a model can read a font it has
seen a thousand times and still fail on a real 1780 impression. The README says so; the real-sample fixtures are
the other half of the test set.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


@dataclass
class PageSpec:
    font: str
    font_size: int = 40
    width: int = 1600
    height: int = 2200
    margin: int = 160
    line_gap: float = 1.35
    rotate_deg: float = 0.0
    blur: float = 0.0
    speckle: float = 0.0        # fraction of pixels darkened
    paper: tuple[int, int, int] = (245, 238, 220)
    ink: tuple[int, int, int] = (40, 30, 25)
    seed: int = 0


def wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Greedy wrap by words; keep explicit newlines as paragraph breaks. Output lines ARE the ground truth."""
    lines: list[str] = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            trial = f"{cur} {w}"
            if draw.textlength(trial, font=font) <= max_width:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def render(text: str, spec: PageSpec, out_png: Path, out_gt: Path, *, header: str | None = None) -> dict:
    rnd = random.Random(spec.seed)
    font = ImageFont.truetype(spec.font, spec.font_size)
    img = Image.new("RGB", (spec.width, spec.height), spec.paper)
    draw = ImageDraw.Draw(img)
    max_w = spec.width - 2 * spec.margin
    lines = wrap(text, font, max_w, draw)
    y = spec.margin
    gt_lines: list[str] = []
    if header:
        draw.text((spec.width / 2, y), header, font=font, fill=spec.ink, anchor="mt")
        gt_lines.append(header)
        y += int(spec.font_size * spec.line_gap * 1.5)
    step = int(spec.font_size * spec.line_gap)
    for line in lines:
        if y + step > spec.height - spec.margin:
            break
        if line:
            draw.text((spec.margin, y), line, font=font, fill=spec.ink)
            gt_lines.append(line)
        y += step
    # Degradation
    if spec.speckle > 0:
        px = img.load()
        n = int(spec.width * spec.height * spec.speckle)
        for _ in range(n):
            x, yy = rnd.randrange(spec.width), rnd.randrange(spec.height)
            r, g, b = px[x, yy]
            k = rnd.randint(60, 140)
            px[x, yy] = (max(0, r - k), max(0, g - k), max(0, b - k))
    if spec.blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(spec.blur))
    if spec.rotate_deg:
        img = img.rotate(spec.rotate_deg, resample=Image.BICUBIC, expand=False, fillcolor=spec.paper)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    out_gt.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)
    out_gt.write_text("\n".join(gt_lines) + "\n", encoding="utf-8")
    meta = {"png": out_png.name, "gt": out_gt.name, "lines": len(gt_lines), "chars": sum(len(l) for l in gt_lines), "spec": asdict(spec)}
    out_png.with_suffix(".json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    return meta
