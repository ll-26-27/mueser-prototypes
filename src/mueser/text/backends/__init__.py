"""OCR/HTR backends. Each exposes ``name`` and ``transcribe(image_path, mode=..., lang=...) -> PageResult``.

``available()`` returns every registered backend with a reason if it cannot run (missing binary, model or key),
so the bake-off can list what ran and what was skipped instead of crashing.
"""

from __future__ import annotations

from .base import Backend, Line, PageResult, Skipped  # noqa: F401


def registry() -> dict[str, type]:
    from . import churro, kraken, mistral_ocr, openrouter, tesseract, transkribus

    return {
        "tesseract": tesseract.TesseractBackend,
        "kraken": kraken.KrakenBackend,
        "openrouter": openrouter.OpenRouterVLMBackend,
        "mistral": mistral_ocr.MistralOCRBackend,
        "transkribus": transkribus.TranskribusBackend,
        "churro": churro.ChurroBackend,
    }


def make(name: str, **kw) -> Backend:
    reg = registry()
    if name not in reg:
        raise KeyError(f"unknown backend {name!r}; known: {', '.join(reg)}")
    return reg[name](**kw)
