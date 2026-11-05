"""Refresh embedded review assets in existing HTML, preserving all stored results.

Run from the repo root: uv run python scripts/refresh_review_ui.py
This does not rerun transcription, segmentation, reconciliation, or API calls.
"""

from pathlib import Path

from mueser.shared.review import enhance_html


def main() -> None:
    targets = [(Path("index.html"), "home")]
    for path in sorted(Path("01-use-cases").glob("**/outputs/**/*.html")):
        # Timestamped run folders are immutable evidence, not presentation targets.
        if "runs" in path.parts:
            continue
        doc = path.read_text(encoding="utf-8")
        if 'class="matrix"' in doc:
            kind = "consensus"
        elif 'id="map"' in doc and 'id="yearMin"' in doc:
            kind = "map"
        elif 'class="fig"' in doc:
            kind = "layout"
        elif 'class="pane"' in doc:
            kind = "report"
        else:
            continue
        targets.append((path, kind))
    for path, kind in targets:
        original = path.read_text(encoding="utf-8")
        updated = enhance_html(original, path, kind)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
        print(f"{kind:10} {path}")


if __name__ == "__main__":
    main()
