"""Embed the shared review interface without changing a report's evidence.

The HTML retains its original content as a no-JavaScript fallback. CSS and JS
are inline so explorers still work when opened directly from the filesystem.
"""

import json
import os
import re
from pathlib import Path

from mueser import REPO_ROOT

ASSETS = Path(__file__).parent / "web"
START = "<!-- mueser-review:start -->"
END = "<!-- mueser-review:end -->"


def enhance_html(document: str, out: Path, kind: str) -> str:
    document = re.sub(re.escape(START) + r".*?" + re.escape(END), "", document, flags=re.S)
    settings = {
        "kind": kind,
        "home": os.path.relpath(REPO_ROOT / "index.html", out.resolve().parent),
    }
    if kind == "report" and (out.parent / "consensus" / "index.html").exists():
        settings["consensus"] = "consensus/index.html"
    config = json.dumps(settings).replace("<", "\\u003c")
    css = (ASSETS / "review.css").read_text(encoding="utf-8")
    js = (ASSETS / "review.js").read_text(encoding="utf-8")
    block = f'{START}\n<style>{css}</style>\n<script>window.REVIEW_CONFIG={config};\n{js}</script>\n{END}'
    return document.replace("</body>", block + "\n</body>")
