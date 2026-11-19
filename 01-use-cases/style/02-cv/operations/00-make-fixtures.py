"""Write the synthetic CV used by the tests and the worked example. Run from the repository root:

    uv run python 01-use-cases/style/02-cv/operations/00-make-fixtures.py
"""
from pathlib import Path

from mueser.style.fixtures import synth_cv

print(synth_cv(Path(__file__).resolve().parents[1] / "inputs/fixtures/synth-cv.docx"))
