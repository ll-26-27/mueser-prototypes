"""mueser: faculty research prototypes for German Fraktur/Kurrent transcription and historical place mapping.

Two subpackages share one data shape (``mueser.shared.record.Record``):

- ``mueser.text``: ingest page images, run several OCR/HTR backends, evaluate against ground truth,
  extract place/person/date mentions as records.
- ``mueser.maps``: load records (or any CSV), resolve place names against historical gazetteers,
  store in DuckDB, export GeoJSON/SQLite, build a web map.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
