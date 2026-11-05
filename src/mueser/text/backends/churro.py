"""CHURRO (Stanford OVAL, 2025): an open 3B vision-language model trained on historical documents.

Not on OpenRouter. Runs locally with Hugging Face Transformers or vLLM on a GPU (FASRC), not on a laptop.
Stub: reports itself as skipped unless CHURRO_ENDPOINT points at a running vLLM OpenAI-compatible server,
in which case it is called exactly like the OpenRouter backend but against that URL.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mueser.shared import env
from .base import Mode, PageResult


class ChurroBackend:
    name = "churro"

    def __init__(self, model: str = "stanford-oval/churro-3B", **_):
        self.model = model

    def check(self) -> Optional[str]:
        if not env.get("CHURRO_ENDPOINT"):
            return "CHURRO_ENDPOINT not set (needs a GPU host running vLLM with the CHURRO model)"
        return "CHURRO backend is a stub: set CHURRO_ENDPOINT and implement the vLLM call in churro.py"

    def transcribe(self, image_path: Path, *, mode: Mode = "print", lang: str = "de") -> PageResult:
        raise NotImplementedError(self.check())
