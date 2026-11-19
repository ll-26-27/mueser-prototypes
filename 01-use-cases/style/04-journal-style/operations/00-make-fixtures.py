"""Write the synthetic draft and the three synthetic journal articles. Run from the repository root:

    uv run python 01-use-cases/style/04-journal-style/operations/00-make-fixtures.py
"""
from pathlib import Path

from mueser.style.fixtures import synth_article, synth_samples

fixtures = Path(__file__).resolve().parents[1] / "inputs/fixtures"
print(synth_article(fixtures / "synth-article.docx"))
for p in synth_samples(fixtures):
    print(p)
