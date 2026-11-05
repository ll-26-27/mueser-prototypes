"""Bring page images in: a local folder (copied, renamed to a stable page id) or a IIIF Presentation manifest
(v2 or v3), downloading each canvas image at a chosen width. Writes a pages.json manifest with provenance
(source URL / original filename, canvas id, size, sha256) so every later step can point back.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from pathlib import Path

import httpx
import typer
from PIL import Image

app = typer.Typer(help="Ingest page images from a folder or a IIIF manifest.")

IMG_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


@app.command()
def folder(src: Path, dest: Path, doc_id: str = typer.Option(..., help="document id used in every record")):
    """Copy images from SRC into DEST/pages as p001.png… and write DEST/pages.json."""
    pages_dir = dest / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in IMG_EXT)
    manifest = {"doc_id": doc_id, "source": {"type": "folder", "path": str(src)}, "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "pages": []}
    for i, f in enumerate(files, 1):
        pid = f"p{i:03d}"
        out = pages_dir / f"{pid}{f.suffix.lower()}"
        shutil.copy2(f, out)
        with Image.open(out) as im:
            w, h = im.size
        manifest["pages"].append({"page_id": pid, "file": out.name, "original_name": f.name, "width": w, "height": h, "sha256": _sha(out)})
    (dest / "pages.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    typer.echo(f"{len(files)} pages -> {pages_dir}")


@app.command()
def iiif(manifest_url: str, dest: Path, doc_id: str = typer.Option(None), width: int = 2000, limit: int = 0):
    """Download every canvas of a IIIF manifest (v2 or v3) at WIDTH px wide into DEST/pages."""
    pages_dir = dest / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=60, follow_redirects=True, headers={"User-Agent": "mueser-prototypes/0.1 (research ingest)"}) as c:
        man = c.get(manifest_url).json()
        canvases = man.get("items") or man.get("sequences", [{}])[0].get("canvases", [])
        label = man.get("label")
        if isinstance(label, dict):
            label = next(iter(label.values()))[0]
        doc_id = doc_id or _slug(str(label or "iiif-doc"))[:60]
        out = {"doc_id": doc_id, "source": {"type": "iiif", "manifest": manifest_url, "label": label}, "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "pages": []}
        for i, cv in enumerate(canvases, 1):
            if limit and i > limit:
                break
            # v3: items[0].items[0].body.service[0].id ; v2: images[0].resource.service.@id
            service_id = None
            try:
                body = cv["items"][0]["items"][0]["body"]
                svc = body.get("service", [{}])
                svc = svc[0] if isinstance(svc, list) else svc
                service_id = svc.get("id") or svc.get("@id")
                if not service_id:
                    service_id = body["id"].split("/full/")[0]
            except Exception:  # noqa: BLE001
                try:
                    svc = cv["images"][0]["resource"]["service"]
                    service_id = svc.get("@id") or svc.get("id")
                except Exception:  # noqa: BLE001
                    pass
            if not service_id:
                typer.echo(f"canvas {i}: no image service found; skipped")
                continue
            url = f"{service_id.rstrip('/')}/full/{width},/0/default.jpg"
            pid = f"p{i:03d}"
            path = pages_dir / f"{pid}.jpg"
            if not path.exists():
                r = c.get(url)
                r.raise_for_status()
                path.write_bytes(r.content)
                time.sleep(0.5)
            with Image.open(path) as im:
                w, h = im.size
            out["pages"].append({"page_id": pid, "file": path.name, "iiif_canvas": cv.get("id") or cv.get("@id"), "image_url": url, "width": w, "height": h, "sha256": _sha(path)})
            typer.echo(f"{pid} <- {url}")
    (dest / "pages.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    app()
