"""Step 00 (deterministic code): copy the pages and readings this use case works from, and record where each came from.

Sources, all in 01-use-cases/transcription/03-layout-and-hybrid/ (the run that has both whole-page vision readings
and a hybrid reading with a box on every line):

- the page images from inputs/pages-print/ and inputs/pages-hand/
- the per-page slice of outputs/consensus-{print,hand}/consensus.json  -> inputs/readings/consensus/<page>.consensus.json
- the medoid reader's run JSON for that page                           -> inputs/readings/medoid/<page>.json
- the hybrid reading (Gemini 3.8 Flash on Kraken's line crops)         -> inputs/readings/segmentation/<page>.json

Nothing is changed in the copies. inputs/readings/provenance.json lists origin path and sha256 of every file.

    uv run python 01-use-cases/transcription/04-reading-room/operations/00-collect-inputs.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "01-use-cases" / "transcription" / "03-layout-and-hybrid"
CASE = ROOT / "01-use-cases" / "transcription" / "04-reading-room"

PAGES = {
    "real-grimm-khm-1812-i-p093": ("print", "print-20261105"),
    "real-schiller-musenalmanach-1796-p093": ("print", "print-20261105"),
    "real-kaskel-to-schnorr-1864": ("hand", "hand-20261105"),
}
SEGMENTATION = ("hybrid", "google/gemini-3.8-flash")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def slug(model: str) -> str:
    return model.replace("/", "_")


def main() -> None:
    prov = {"collected_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "source_case": str(SRC.relative_to(ROOT)), "files": {}}
    for d in ("pages", "readings/consensus", "readings/medoid", "readings/segmentation"):
        (CASE / "inputs" / d).mkdir(parents=True, exist_ok=True)

    def copy(src: Path, dst: Path, role: str) -> None:
        shutil.copy2(src, dst)
        prov["files"][str(dst.relative_to(CASE))] = {"role": role, "from": str(src.relative_to(ROOT)), "sha256": sha(src)}

    for pid, (kind, run) in PAGES.items():
        img = next(SRC.glob(f"inputs/pages-{kind}/{pid}.*"))
        copy(img, CASE / "inputs" / "pages" / img.name, "page image")
        cons_path = SRC / "outputs" / f"consensus-{kind}" / "consensus.json"
        cons = json.loads(cons_path.read_text(encoding="utf-8"))
        pg = cons["pages"][pid]
        slice_ = {"page_id": pid, "run_id": cons["run_id"], "min_weight": cons["min_weight"], "page": pg,
                  "from": str(cons_path.relative_to(ROOT)), "from_sha256": sha(cons_path)}
        dst = CASE / "inputs" / "readings" / "consensus" / f"{pid}.consensus.json"
        dst.write_text(json.dumps(slice_, ensure_ascii=False, indent=1), encoding="utf-8")
        prov["files"][str(dst.relative_to(CASE))] = {"role": "consensus (per-page slice)", "from": str(cons_path.relative_to(ROOT)), "sha256": sha(cons_path)}
        backend, model = pg["medoid"]["overall"].split(":", 1)
        med = SRC / "outputs" / "runs" / run / backend / slug(model) / f"{pid}.json"
        copy(med, CASE / "inputs" / "readings" / "medoid" / f"{pid}.json", f"medoid reading {pg['medoid']['overall']}")
        seg = SRC / "outputs" / "runs" / run / SEGMENTATION[0] / slug(SEGMENTATION[1]) / f"{pid}.json"
        copy(seg, CASE / "inputs" / "readings" / "segmentation" / f"{pid}.json", f"segmentation with boxes {SEGMENTATION[0]}:{SEGMENTATION[1]}")
        print(f"{pid}: medoid {pg['medoid']['overall']} ({len(pg['spans'])} spans, agreement {pg['agreement']}); segmentation {SEGMENTATION[0]}:{SEGMENTATION[1]}")
    (CASE / "inputs" / "readings" / "provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(prov['files'])} files -> {CASE / 'inputs'}; provenance in inputs/readings/provenance.json")


if __name__ == "__main__":
    sys.exit(main())
