# Historical map overlay: file guide

- `README.md`, `summary.md`, `allmaps.md` (the three lines of code).
- `operations/01-find-georeferenced-maps.py`.
- `outputs/georeferenced-maps.csv`: every (place, sheet) match with scale
  and containment check. The responses are cached in `cache/gazetteer_allmaps/`.
