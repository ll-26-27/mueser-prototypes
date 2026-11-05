"""One OpenAI-compatible client for OpenRouter: text or image in, JSON-schema-constrained text out.

Usage and cost come back from OpenRouter when ``usage.include`` is set; both are stored with the cached
raw response and appended to a cost log so the bill is auditable line by line.
"""

from __future__ import annotations

import base64
import csv
import json
import mimetypes
import time
from pathlib import Path
from typing import Any, Optional

import httpx

from mueser import REPO_ROOT
from mueser.shared import env
from mueser.shared.cache import DiskCache, cache_key, sha256_file, sha256_text

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
COST_LOG = REPO_ROOT / "cache" / "cost-log.csv"


class MissingCredential(RuntimeError):
    pass


class JSONReplyError(RuntimeError):
    """The model answered, but not with parseable JSON. ``raw`` keeps the whole response for the record."""

    def __init__(self, message: str, raw: dict | None = None):
        super().__init__(message)
        self.raw = raw


def parse_json_reply(text: str):
    """Tolerant JSON extraction: strip code fences, then take the first balanced {...} or [...] block."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
        t = t.strip()
    for candidate in (t,):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    start = min([i for i in (t.find("{"), t.find("[")) if i >= 0], default=-1)
    if start < 0:
        return None
    depth, in_str, esc = 0, False, False
    opener = t[start]; closer = "}" if opener == "{" else "]"
    for i in range(start, len(t)):
        ch = t[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(t[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def image_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    b64 = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def log_cost(step: str, model: str, usage: dict, cached: bool, note: str = "") -> None:
    COST_LOG.parent.mkdir(parents=True, exist_ok=True)
    new = not COST_LOG.exists()
    with COST_LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "step", "model", "cached", "prompt_tokens", "completion_tokens", "cost_usd", "note"])
        w.writerow([time.strftime("%Y-%m-%dT%H:%M:%S"), step, model, int(cached),
                    usage.get("prompt_tokens", ""), usage.get("completion_tokens", ""),
                    f"{float(usage.get('cost') or 0):.6f}", note])


def chat(
    *,
    model: str,
    system: str,
    user_text: str,
    image_path: Optional[Path] = None,
    schema: Optional[dict] = None,
    schema_name: str = "answer",
    temperature: float = 0.0,
    max_tokens: int = 4000,
    step: str = "chat",
    retries: int = 4,
    timeout: float = 180.0,
    cache: Optional[DiskCache] = None,
) -> dict:
    """Return {"text", "parsed", "usage", "cost_usd", "cached", "model", "provider", "raw", "key"}.

    Raises MissingCredential if OPENROUTER_API_KEY is unset (callers turn that into a skip).
    """
    key = env.get("OPENROUTER_API_KEY")
    if not key:
        raise MissingCredential("OPENROUTER_API_KEY is not set in .env")

    cache = cache or DiskCache("openrouter")
    ck = cache_key(
        "openrouter", model=model, system=sha256_text(system), user=sha256_text(user_text),
        image=sha256_file(image_path) if image_path else None, schema=schema, temperature=temperature,
        max_tokens=max_tokens,
    )
    hit = cache.get(ck)
    if hit:
        usage = hit["raw"].get("usage", {}) if isinstance(hit["raw"], dict) else {}
        log_cost(step, model, usage, cached=True)
        return {**hit["parsed"], "cached": True, "raw": hit["raw"], "key": ck}

    content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
    if image_path:
        content.append({"type": "image_url", "image_url": {"url": image_data_url(image_path)}})
    body: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}],
        "usage": {"include": True},
    }
    if schema:
        body["response_format"] = {"type": "json_schema", "json_schema": {"name": schema_name, "strict": True, "schema": schema}}

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "HTTP-Referer": "https://github.com/ll-26-27/mueser-prototypes", "X-Title": "mueser-prototypes"}
    last_err: Exception | None = None
    t0 = time.time()
    for attempt in range(retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.post(ENDPOINT, headers=headers, json=body)
            data = res.json()
            if res.status_code != 200 or "error" in data:
                raise RuntimeError(f"HTTP {res.status_code}: {json.dumps(data.get('error', data))[:400]}")
            text = data["choices"][0]["message"]["content"] or ""
            parsed_json = None
            if schema:
                parsed_json = parse_json_reply(text)
                if parsed_json is None:
                    finish = data["choices"][0].get("finish_reason") or data["choices"][0].get("native_finish_reason")
                    # A malformed or empty reply is not a transport error: retry once, then give up with the raw text kept.
                    if attempt < 1:
                        raise RuntimeError(f"no JSON in reply (finish_reason={finish}): {text[:120]!r}")
                    raise JSONReplyError(f"no JSON in reply after retry (finish_reason={finish}): {text[:200]!r}", raw=data)
            usage = data.get("usage", {}) or {}
            result = {
                "text": text, "parsed": parsed_json, "usage": usage,
                "cost_usd": float(usage.get("cost") or 0.0), "model": data.get("model", model),
                "provider": data.get("provider"), "seconds": round(time.time() - t0, 2),
            }
            # Cache stores the request WITHOUT the base64 image (the image hash is in the key).
            req = {**body, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user_text}],
                   "image_path": str(image_path) if image_path else None}
            cache.put(ck, request=req, raw=data, parsed=result)
            log_cost(step, model, usage, cached=False)
            return {**result, "cached": False, "raw": data, "key": ck}
        except JSONReplyError:
            raise
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries:
                time.sleep(1.5 * 2**attempt)
    raise RuntimeError(f"OpenRouter call failed after {retries + 1} attempts: {last_err}")
