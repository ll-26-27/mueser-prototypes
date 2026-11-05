"""Tesseract 5 with a Fraktur model. Deterministic, local, free. Returns line bboxes and confidences.

Models: ``frak2021`` (UB Mannheim, trained on GT4HistOCR; best for 18th–20th c. print) or Tesseract's own
``deu_frak`` / ``script/Fraktur``. The traineddata file is looked for in TESSDATA_PREFIX, then in
<repo>/models/tesseract/. ``python -m mueser.text.models fetch tesseract`` downloads frak2021.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from mueser import REPO_ROOT
from .base import Line, Mode, PageResult, page_id_for

MODEL_DIR = REPO_ROOT / "models" / "tesseract"


class TesseractBackend:
    name = "tesseract"

    def __init__(self, model: str = "frak2021", psm: int = 4, **_):
        self.model = model
        self.psm = psm

    def _tessdata_dir(self) -> Optional[Path]:
        candidates = []
        if os.environ.get("TESSDATA_PREFIX"):
            candidates.append(Path(os.environ["TESSDATA_PREFIX"]))
        candidates.append(MODEL_DIR)
        for brew in ("/opt/homebrew/share/tessdata", "/usr/local/share/tessdata", "/usr/share/tesseract-ocr/5/tessdata"):
            candidates.append(Path(brew))
        for c in candidates:
            if (c / f"{self.model}.traineddata").exists():
                return c
        return None

    def check(self) -> Optional[str]:
        if not shutil.which("tesseract"):
            return "tesseract binary not found (brew install tesseract)"
        if self._tessdata_dir() is None:
            return f"model {self.model}.traineddata not found; run: uv run python -m mueser.text.models fetch tesseract"
        return None

    def transcribe(self, image_path: Path, *, mode: Mode = "print", lang: str = "de") -> PageResult:
        import pytesseract
        from PIL import Image

        tessdata = self._tessdata_dir()
        assert tessdata is not None, self.check()
        t0 = time.time()
        img = Image.open(image_path)
        config = f'--tessdata-dir "{tessdata}" --psm {self.psm}'
        data = pytesseract.image_to_data(img, lang=self.model, config=config, output_type=pytesseract.Output.DICT)
        # Group words into lines by (block, par, line).
        lines: dict[tuple, dict] = {}
        for i, word in enumerate(data["text"]):
            if not word.strip():
                continue
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            L = lines.setdefault(key, {"words": [], "confs": [], "x0": 1e9, "y0": 1e9, "x1": 0, "y1": 0})
            L["words"].append(word)
            conf = float(data["conf"][i])
            if conf >= 0:
                L["confs"].append(conf / 100.0)
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            L["x0"], L["y0"] = min(L["x0"], x), min(L["y0"], y)
            L["x1"], L["y1"] = max(L["x1"], x + w), max(L["y1"], y + h)
        out = []
        for key in sorted(lines):
            L = lines[key]
            out.append(Line(
                text=" ".join(L["words"]),
                bbox=[L["x0"], L["y0"], L["x1"] - L["x0"], L["y1"] - L["y0"]],
                confidence=(sum(L["confs"]) / len(L["confs"])) if L["confs"] else None,
            ))
        return PageResult(page_id=page_id_for(image_path), lines=out, raw={"tsv": data}, backend=self.name,
                          model=self.model, cost_usd=0.0, seconds=round(time.time() - t0, 2))
