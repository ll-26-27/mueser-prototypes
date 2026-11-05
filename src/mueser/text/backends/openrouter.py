"""Vision-language models through OpenRouter (Qwen3-VL, Gemini, Claude, GPT…), constrained to a JSON line array.

Returns no bboxes: a VLM reads the page as a whole. Use ``--hybrid`` in the bake-off to have Kraken segment
the page into lines first and send each crop here, which keeps coordinates and PAGE-XML.
The prompt lives in prompts/transcribe_de.md; its hash is recorded on every result.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Optional

from mueser.shared import env
from mueser.shared.cache import sha256_text
from mueser.shared.openrouter import MissingCredential, chat
from .base import Line, Mode, PageResult, page_id_for

PROMPT_PATH = Path(__file__).parent / "prompts" / "transcribe_de.md"

LINES_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["lines", "script", "notes"],
    "properties": {
        "lines": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["text"],
                                             "properties": {"text": {"type": "string"}}}},
        "script": {"type": "string", "enum": ["fraktur", "antiqua", "kurrent", "suetterlin", "mixed", "unknown"]},
        "notes": {"type": "string"},
    },
}


def load_prompt(path: Path = PROMPT_PATH) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"<!-- PROMPT START -->\s*(.*?)\s*<!-- PROMPT END -->", text, re.S)
    return (m.group(1) if m else text).strip()


class OpenRouterVLMBackend:
    name = "openrouter"

    def __init__(self, model: Optional[str] = None, prompt_path: Path = PROMPT_PATH, max_tokens: int = 6000, **_):
        self.model = model or env.get("VLM_MODEL_DEFAULT", "qwen/qwen3-vl-30b-a3b-instruct")
        self.prompt_path = prompt_path
        self.max_tokens = max_tokens

    def check(self) -> Optional[str]:
        if env.missing("OPENROUTER_API_KEY"):
            return "OPENROUTER_API_KEY not set in .env"
        return None

    def transcribe(self, image_path: Path, *, mode: Mode = "print", lang: str = "de") -> PageResult:
        system = load_prompt(self.prompt_path)
        user = (f"Transcribe this {'handwritten' if mode == 'hand' else 'printed'} page (language: {lang}). "
                f"Return JSON only.")
        t0 = time.time()
        try:
            res = chat(model=self.model, system=system, user_text=user, image_path=Path(image_path), schema=LINES_SCHEMA,
                       schema_name="transcription", max_tokens=self.max_tokens, step=f"transcribe/{self.name}")
        except MissingCredential as e:
            raise RuntimeError(str(e)) from e
        parsed = res.get("parsed") or {"lines": [], "script": "unknown", "notes": "no JSON parsed"}
        lines = [Line(text=l.get("text", "")) for l in parsed.get("lines", [])]
        notes = [n for n in [parsed.get("notes", ""), f"script={parsed.get('script')}"] if n]
        return PageResult(page_id=page_id_for(image_path), lines=lines, raw={"cache_key": res["key"], "response": res["raw"]},
                          backend=self.name, model=res.get("model") or self.model, cost_usd=res.get("cost_usd"),
                          seconds=res.get("seconds", round(time.time() - t0, 2)), cached=res.get("cached", False),
                          prompt_sha256=sha256_text(system), notes=notes)
