"""Kraken (the engine behind eScriptorium): layout segmentation + recognition, local, free.

Install with ``uv sync --extra htr`` (pulls PyTorch). Models are fetched from Zenodo with
``kraken get <DOI>``; ``python -m mueser.text.models fetch kraken`` does this for the defaults in
MODELS below. ``segment()`` is also used alone for hybrid mode: Kraken draws the lines, a VLM reads them.
"""

from __future__ import annotations

import importlib.util
import time
from pathlib import Path
from typing import Optional

from mueser import REPO_ROOT
from .base import Line, Mode, PageResult, page_id_for

MODEL_DIR = REPO_ROOT / "models" / "kraken"
# Filled in by models.py after `kraken get`; see 01-use-cases/transcription/README.md for the DOIs used.
MODELS = {"print": "german_print.mlmodel", "hand": "german_handwriting.mlmodel"}


class KrakenBackend:
    name = "kraken"

    def __init__(self, model: Optional[str] = None, seg_model: Optional[str] = None, **_):
        self.model = model or "auto"
        self.seg_model = seg_model  # None -> kraken's built-in blla.mlmodel

    def _model_path(self, mode: Mode) -> Path:
        if self.model != "auto":
            p = Path(self.model)
            return p if p.exists() else MODEL_DIR / self.model
        return MODEL_DIR / MODELS[mode]

    def check(self) -> Optional[str]:
        if importlib.util.find_spec("kraken") is None:
            return "kraken not installed (uv sync --extra htr)"
        for mode in ("print", "hand"):
            if self.model == "auto" and not self._model_path(mode).exists():
                return f"kraken model for {mode} missing at {self._model_path(mode)}; run: uv run python -m mueser.text.models fetch kraken"
        return None

    def segment(self, image_path: Path) -> dict:
        from kraken import blla
        from kraken.lib import vgsl
        from PIL import Image

        im = Image.open(image_path)
        if self.seg_model:
            model = vgsl.TorchVGSLModel.load_model(self.seg_model)
            return blla.segment(im, model=model)
        return blla.segment(im)

    def transcribe(self, image_path: Path, *, mode: Mode = "print", lang: str = "de") -> PageResult:
        from kraken import rpred
        from kraken.lib import models
        from PIL import Image

        t0 = time.time()
        im = Image.open(image_path)
        seg = self.segment(image_path)
        model_path = self._model_path(mode)
        net = models.load_any(str(model_path))
        lines = []
        for rec in rpred.rpred(net, im, seg):
            bbox = None
            try:
                xs = [p[0] for p in rec.boundary]; ys = [p[1] for p in rec.boundary]
                bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
            except Exception:  # noqa: BLE001
                pass
            conf = (sum(rec.confidences) / len(rec.confidences)) if rec.confidences else None
            lines.append(Line(text=rec.prediction, bbox=bbox, baseline=[list(p) for p in rec.baseline] if rec.baseline else None,
                              confidence=conf))
        return PageResult(page_id=page_id_for(image_path), lines=lines, raw={"segmentation": "see kraken output"},
                          backend=self.name, model=model_path.name, cost_usd=0.0, seconds=round(time.time() - t0, 2))
