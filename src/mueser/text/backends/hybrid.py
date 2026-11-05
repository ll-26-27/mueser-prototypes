"""Hybrid: Kraken draws the lines, a vision model reads each one.

Kraken's segmenter is reliable on layout and cannot invent text; a vision model reads a single line crop better
than a whole page and has no room to skip or reorder lines. The result keeps every line's coordinates (so PAGE-XML
is complete) while the reading comes from the model. Cost is one small call per line; every crop is cached by
its hash, so a rerun is free.

Spec: ``hybrid:<openrouter model id>``. Needs --extra htr (Kraken) and OPENROUTER_API_KEY.
"""

from __future__ import annotations

import importlib.util
import re
import time
from pathlib import Path
from typing import Optional

from PIL import Image

from mueser.shared import env
from mueser.shared.cache import sha256_text
from mueser.shared.openrouter import JSONReplyError, chat
from .base import Line, Mode, PageResult, page_id_for

PROMPT_PATH = Path(__file__).parent / "prompts" / "transcribe_line_de.md"
LINE_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["text", "uncertain"],
               "properties": {"text": {"type": "string"}, "uncertain": {"type": "boolean"}}}


def load_prompt() -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    m = re.search(r"<!-- PROMPT START -->\s*(.*?)\s*<!-- PROMPT END -->", text, re.S)
    return (m.group(1) if m else text).strip()


class HybridBackend:
    name = "hybrid"

    def __init__(self, model: Optional[str] = None, pad: int = 6, max_lines: int = 400, **_):
        self.model = model or env.get("VLM_MODEL_FRONTIER", "google/gemini-2.5-flash")
        self.pad = pad
        self.max_lines = max_lines

    def check(self) -> Optional[str]:
        if importlib.util.find_spec("kraken") is None:
            return "kraken not installed (uv sync --extra htr); hybrid needs its segmenter"
        if env.missing("OPENROUTER_API_KEY"):
            return "OPENROUTER_API_KEY not set in .env"
        return None

    def transcribe(self, image_path: Path, *, mode: Mode = "print", lang: str = "de") -> PageResult:
        from .kraken import KrakenBackend

        t0 = time.time()
        seg = KrakenBackend().segment(image_path)
        seg_lines = seg.lines if hasattr(seg, "lines") else seg.get("lines", [])
        im = Image.open(image_path).convert("RGB")
        W, H = im.size
        system = load_prompt()
        crops_dir = Path(image_path).parent.parent / "work" / "crops" / Path(image_path).stem
        crops_dir.mkdir(parents=True, exist_ok=True)
        lines, cost, cached_all, failures = [], 0.0, True, []
        for i, ln in enumerate(seg_lines[: self.max_lines]):
            boundary = getattr(ln, "boundary", None) or (ln.get("boundary") if isinstance(ln, dict) else None)
            if not boundary:
                continue
            xs = [p[0] for p in boundary]; ys = [p[1] for p in boundary]
            x0, y0, x1, y1 = max(0, int(min(xs)) - self.pad), max(0, int(min(ys)) - self.pad), min(W, int(max(xs)) + self.pad), min(H, int(max(ys)) + self.pad)
            if x1 - x0 < 8 or y1 - y0 < 8:
                continue
            crop_path = crops_dir / f"l{i:03d}.png"
            im.crop((x0, y0, x1, y1)).save(crop_path)
            try:
                res = chat(model=self.model, system=system, user_text=f"Transcribe this one line ({'handwriting' if mode == 'hand' else 'print'}, {lang}). JSON only.",
                           image_path=crop_path, schema=LINE_SCHEMA, schema_name="line", max_tokens=2000, step="transcribe/hybrid")
                parsed = res.get("parsed") or {"text": "", "uncertain": True}
            except JSONReplyError as e:
                # The model answered without JSON (often on an ornament or a blank crop). Keep the line, mark it, go on.
                failures.append({"line": i, "crop": crop_path.name, "error": str(e)[:200]})
                res = {"cost_usd": 0.0, "cached": False}
                parsed = {"text": "[...]", "uncertain": True}
            text = parsed.get("text", "")
            if parsed.get("uncertain") and text and not text.startswith("[?"):
                text = f"[?{text}]" if " " not in text else text
            baseline = getattr(ln, "baseline", None) or (ln.get("baseline") if isinstance(ln, dict) else None)
            lines.append(Line(text=text, bbox=[x0, y0, x1 - x0, y1 - y0], baseline=[list(p) for p in baseline] if baseline else None))
            cost += float(res.get("cost_usd") or 0)
            cached_all = cached_all and bool(res.get("cached"))
        return PageResult(page_id=page_id_for(image_path), lines=lines, raw={"segmenter": "kraken blla", "crops": str(crops_dir), "failures": failures},
                          backend=self.name, model=self.model, cost_usd=round(cost, 6), seconds=round(time.time() - t0, 2), cached=cached_all,
                          prompt_sha256=sha256_text(system), notes=[f"{len(lines)} line crops read one by one"] + ([f"{len(failures)} crops got no JSON reply and are marked [...]: " + ", ".join(f['crop'] for f in failures)] if failures else []))
