"""Fetch the model files and fonts this repo needs but does not commit (they are large or separately licensed).

    uv run python -m mueser.text.models fetch tesseract   # frak2021 + deu_frak into models/tesseract/
    uv run python -m mueser.text.models fetch fonts       # Fraktur + Kurrent fonts into models/fonts/
    uv run python -m mueser.text.models fetch kraken      # kraken get <DOI> into models/kraken/

Every URL below was checked on the date in SOURCES_CHECKED; if one moves, the error says which.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import httpx
import typer

from mueser import REPO_ROOT

app = typer.Typer(help="Download model files and fonts.")


@app.callback()
def _root():
    """Sub-commands below."""
MODELS = REPO_ROOT / "models"
SOURCES_CHECKED = "2026-11-04"

TESSERACT = {
    # UB Mannheim frak2021 (GT4HistOCR-trained), and Tesseract's stock Fraktur models
    "frak2021.traineddata": "https://ub-backup.bib.uni-mannheim.de/~stweil/tesstrain/frak2021/tessdata_best/frak2021-0.905.traineddata",
    "deu_frak.traineddata": "https://github.com/tesseract-ocr/tessdata/raw/main/deu_frak.traineddata",
    "Fraktur.traineddata": "https://github.com/tesseract-ocr/tessdata_best/raw/main/script/Fraktur.traineddata",
    "deu_latf.traineddata": "https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/deu_latf.traineddata",
}
FONTS = {
    # Fraktur (OFL): UnifrakturMaguntia from Google Fonts' repo
    "UnifrakturMaguntia-Book.ttf": "https://github.com/google/fonts/raw/main/ofl/unifrakturmaguntia/UnifrakturMaguntia-Book.ttf",
    "UnifrakturCook-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/unifrakturcook/UnifrakturCook-Bold.ttf",
}
FONT_ZIPS = {
    # Kurrent / Latin handwriting-style fonts by Peter Wiegel (OFL 1.1 for Wiegel Kurrent; CC for Wiegel Latein; the
    # licence text is inside each zip). Unpacked into models/fonts/<zip stem>/.
    "WiegelKurrent.unz1t.zip": "https://www.peter-wiegel.de/Fonts/WiegelKurrent.unz1t.zip",
    "WiegelLateinTT.zip": "https://www.peter-wiegel.de/Fonts/WiegelLateinTT.zip",
}
KRAKEN_DOIS = {
    # kraken get <DOI> fetches a model from Zenodo's OCR/HTR model repository (https://zenodo.org/communities/ocr_models/).
    # Checked against the Zenodo API on SOURCES_CHECKED; see 01-use-cases/transcription/README.md for what each was trained on.
    "print": "10.5281/zenodo.10519596",   # german_print.mlmodel: German prints, several datasets (UB Mannheim, CC0)
    "hand": "10.5281/zenodo.7933463",     # german_handwriting.mlmodel: German manuscripts, several datasets (CC BY-SA 4.0)
    "kurrent": "10.5281/zenodo.21747522", # german_handwriting_kurrent_v3.mlmodel: fine-tuned on Kurrent diaries (CC BY 4.0)
}


def _download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        typer.echo(f"exists  {dest.relative_to(REPO_ROOT)}")
        return dest
    typer.echo(f"fetch   {url}")
    with httpx.Client(follow_redirects=True, timeout=120) as c:
        with c.stream("GET", url) as r:
            r.raise_for_status()
            with dest.open("wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
    typer.echo(f"saved   {dest.relative_to(REPO_ROOT)} ({dest.stat().st_size // 1024} KB)")
    return dest


@app.command()
def fetch(what: str):
    if what == "tesseract":
        for name, url in TESSERACT.items():
            try:
                _download(url, MODELS / "tesseract" / name)
            except Exception as e:  # noqa: BLE001
                typer.echo(f"FAILED  {name}: {e}")
    elif what == "fonts":
        for name, url in FONTS.items():
            try:
                _download(url, MODELS / "fonts" / name)
            except Exception as e:  # noqa: BLE001
                typer.echo(f"FAILED  {name}: {e}")
        for name, url in FONT_ZIPS.items():
            zpath = MODELS / "fonts" / name
            try:
                _download(url, zpath)
                shutil.unpack_archive(str(zpath), str(MODELS / "fonts" / zpath.stem))
            except Exception as e:  # noqa: BLE001
                typer.echo(f"FAILED  {name}: {e}")
    elif what == "kraken":
        if not shutil.which("kraken"):
            raise typer.Exit("kraken not installed: uv sync --extra htr")
        (MODELS / "kraken").mkdir(parents=True, exist_ok=True)
        for mode, doi in KRAKEN_DOIS.items():
            if not doi:
                typer.echo(f"no DOI configured for {mode}; run `kraken list` and set KRAKEN_DOIS in models.py")
                continue
            subprocess.run(["kraken", "get", doi], cwd=MODELS / "kraken", check=True)
    else:
        raise typer.BadParameter("what must be tesseract | fonts | kraken")


if __name__ == "__main__":
    app()
