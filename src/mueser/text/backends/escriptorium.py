"""eScriptorium: the open HTR platform (Kraken inside, a web GUI for correction and training) that a lab can host
itself. This backend drives an instance through its REST API: upload the page, segment, transcribe with a chosen
model, poll, fetch the lines with their coordinates. Skipped with a reason until ESCRIPTORIUM_URL and
ESCRIPTORIUM_TOKEN are set in .env.

API shape (eScriptorium 0.13+, see <instance>/api/ and the docs at https://escriptorium.readthedocs.io/):
  GET  /api/documents/                                   list documents
  POST /api/documents/                                   {"name", "main_script", "read_direction"} -> document
  POST /api/documents/{doc}/parts/                       multipart {"image": file} -> part (one page)
  POST /api/documents/{doc}/parts/{part}/segment/        {"model": <segmenter id or null>, "steps": "both"}
  POST /api/documents/{doc}/parts/{part}/transcribe/     {"model": <recognition model id>}
  GET  /api/documents/{doc}/parts/{part}/                "workflow": {"segment": "done", "transcribe": "done"} when finished
  GET  /api/documents/{doc}/parts/{part}/transcriptions/?transcription=<id>  lines: {"line": id, "content": text}
  GET  /api/documents/{doc}/parts/{part}/lines/          lines with "baseline" and "mask" polygons
  GET  /api/models/                                      models visible to the token (recognition + segmentation)
Auth: header "Authorization: Token <ESCRIPTORIUM_TOKEN>" (from the user's profile page on the instance).

Running an instance locally: https://gitlab.com/scripta/escriptorium (docker compose), or use a hosted instance
you have an account on. The same Kraken models used here (models/kraken/*.mlmodel) can be uploaded to it.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import httpx

from mueser.shared import env
from .base import Line, Mode, PageResult, page_id_for


class EScriptoriumBackend:
    name = "escriptorium"

    def __init__(self, model: Optional[str] = None, document: Optional[str] = None, poll_seconds: float = 5.0, timeout: float = 900.0, **_):
        self.model = model or env.get("ESCRIPTORIUM_MODEL", "auto")
        self.document_name = document or env.get("ESCRIPTORIUM_DOCUMENT", "mueser-prototypes bake-off")
        self.poll_seconds = poll_seconds
        self.timeout = timeout

    def check(self) -> Optional[str]:
        missing = env.missing("ESCRIPTORIUM_URL", "ESCRIPTORIUM_TOKEN")
        if missing:
            return f"{', '.join(missing)} not set in .env (no eScriptorium instance yet; see src/mueser/text/backends/escriptorium.py)"
        try:
            r = self._client().get("/api/models/")
            r.raise_for_status()
        except Exception as e:  # noqa: BLE001
            return f"eScriptorium at {env.get('ESCRIPTORIUM_URL')} not reachable: {e}"
        return None

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=env.get("ESCRIPTORIUM_URL").rstrip("/"), headers={"Authorization": f"Token {env.get('ESCRIPTORIUM_TOKEN')}"}, timeout=120)

    def _model_id(self, c: httpx.Client, mode: Mode) -> Optional[int]:
        models = c.get("/api/models/").json().get("results", [])
        rec = [m for m in models if m.get("job") in ("Recognize", "recognize")]
        if self.model != "auto":
            for m in rec:
                if str(m.get("id")) == str(self.model) or m.get("name") == self.model:
                    return m["id"]
            raise RuntimeError(f"recognition model {self.model!r} not found on the instance; available: {[m.get('name') for m in rec]}")
        want = "hand" if mode == "hand" else "print"
        for m in rec:
            if want in (m.get("name") or "").lower():
                return m["id"]
        return rec[0]["id"] if rec else None

    def _document_id(self, c: httpx.Client) -> int:
        for d in c.get("/api/documents/").json().get("results", []):
            if d.get("name") == self.document_name:
                return d["id"]
        r = c.post("/api/documents/", json={"name": self.document_name, "main_script": "Latin", "read_direction": "ltr"})
        r.raise_for_status()
        return r.json()["id"]

    def transcribe(self, image_path: Path, *, mode: Mode = "print", lang: str = "de") -> PageResult:
        t0 = time.time()
        with self._client() as c:
            doc = self._document_id(c)
            with open(image_path, "rb") as f:
                part = c.post(f"/api/documents/{doc}/parts/", files={"image": (Path(image_path).name, f)}).json()
            pid = part["pk"] if "pk" in part else part["id"]
            c.post(f"/api/documents/{doc}/parts/{pid}/segment/", json={"steps": "both", "model": None}).raise_for_status()
            model_id = self._model_id(c, mode)
            if model_id is None:
                raise RuntimeError("no recognition model on the instance; upload one (models/kraken/*.mlmodel) first")
            c.post(f"/api/documents/{doc}/parts/{pid}/transcribe/", json={"model": model_id}).raise_for_status()
            deadline = time.time() + self.timeout
            while time.time() < deadline:
                st = c.get(f"/api/documents/{doc}/parts/{pid}/").json().get("workflow", {})
                if st.get("transcribe") == "done":
                    break
                if "error" in (st.get("segment"), st.get("transcribe")):
                    raise RuntimeError(f"eScriptorium reported an error: {st}")
                time.sleep(self.poll_seconds)
            else:
                raise RuntimeError("eScriptorium did not finish in time")
            lines_meta = {ln["pk"] if "pk" in ln else ln["id"]: ln for ln in c.get(f"/api/documents/{doc}/parts/{pid}/lines/").json().get("results", [])}
            trs = c.get(f"/api/documents/{doc}/parts/{pid}/transcriptions/").json().get("results", [])
        lines = []
        for t in trs:
            meta = lines_meta.get(t.get("line"), {})
            bbox = None
            mask = meta.get("mask") or meta.get("box")
            if mask:
                xs = [p[0] for p in mask]; ys = [p[1] for p in mask]
                bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
            lines.append(Line(text=t.get("content", ""), bbox=bbox, baseline=meta.get("baseline"), confidence=t.get("avg_confidence")))
        return PageResult(page_id=page_id_for(image_path), lines=lines, raw={"document": doc, "part": pid, "transcriptions": trs},
                          backend=self.name, model=str(model_id), cost_usd=0.0, seconds=round(time.time() - t0, 2))
