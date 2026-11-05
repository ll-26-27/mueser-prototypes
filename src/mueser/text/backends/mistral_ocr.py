"""Mistral OCR: a dedicated document-OCR endpoint (POST /v1/ocr), not a chat model, so it is called directly.

It returns Markdown per page. We split it into lines; no bboxes. Priced per page. Cached like every other call.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import httpx

from mueser.shared import env
from mueser.shared.cache import DiskCache, cache_key, sha256_file
from mueser.shared.openrouter import image_data_url, log_cost
from .base import Line, Mode, PageResult, page_id_for

ENDPOINT = "https://api.mistral.ai/v1/ocr"


class MistralOCRBackend:
    name = "mistral"

    def __init__(self, model: str = "mistral-ocr-latest", **_):
        self.model = model

    def check(self) -> Optional[str]:
        if env.missing("MISTRAL_API_KEY"):
            return "MISTRAL_API_KEY not set in .env"
        return None

    def transcribe(self, image_path: Path, *, mode: Mode = "print", lang: str = "de") -> PageResult:
        key = env.get("MISTRAL_API_KEY")
        assert key
        cache = DiskCache("mistral_ocr")
        ck = cache_key("mistral_ocr", model=self.model, image=sha256_file(image_path))
        t0 = time.time()
        hit = cache.get(ck)
        if hit:
            data, cached = hit["raw"], True
        else:
            body = {"model": self.model, "document": {"type": "image_url", "image_url": image_data_url(Path(image_path))},
                    "include_image_base64": False}
            with httpx.Client(timeout=180) as client:
                res = client.post(ENDPOINT, headers={"Authorization": f"Bearer {key}"}, json=body)
            if res.status_code != 200:
                raise RuntimeError(f"Mistral OCR HTTP {res.status_code}: {res.text[:400]}")
            data = res.json()
            cache.put(ck, request={"model": self.model, "image_path": str(image_path)}, raw=data)
            cached = False
        pages = data.get("pages", [])
        md = "\n".join(p.get("markdown", "") for p in pages)
        lines = [Line(text=t) for t in (s.rstrip() for s in md.splitlines()) if t.strip()]
        usage = data.get("usage_info", {}) or {}
        pages_processed = usage.get("pages_processed", len(pages))
        # Mistral OCR list price: see 01-use-cases/transcription/README.md (checked on the date noted there).
        cost = round(0.004 * pages_processed, 6)   # $4 per 1,000 pages, docs.mistral.ai, checked 2026-11-04
        log_cost(f"transcribe/{self.name}", self.model, {"cost": cost, "prompt_tokens": "", "completion_tokens": ""}, cached)
        return PageResult(page_id=page_id_for(image_path), lines=lines, raw={"cache_key": ck, "response": data},
                          backend=self.name, model=self.model, cost_usd=cost, seconds=round(time.time() - t0, 2),
                          cached=cached, notes=[f"pages_processed={pages_processed}", "cost is list price per page, not metered"])
