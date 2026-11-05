# Inputs

- `pages/synth-01.png` … `synth-05.png`: rendered from
  `synthetic-text/reisetagebuch-1786.txt` by `operations/00-make-synthetic-pages.py`.
  The JSON beside each image records the font and the degradation applied.
- `pages/real-schiller-musenalmanach-1796-p093.jpg`,
  `pages/real-grimm-khm-1812-i-p093.jpg`,
  `pages/real-gartenlaube-1853-p001.jpg`: Wikimedia Commons, public domain.
  Commons file pages: `File:Schiller_Musenalmanach_1796_093.jpg`,
  `File:Kinder_und_Hausmärchen_(Grimm)_1812_I_093.jpg`,
  `File:Die_Gartenlaube_(1853)_001.jpg`.
- `gt/<page>.txt`: ground truth, one line per text line for the synthetic
  pages; Wikisource's text for the real pages. `gt/provenance.json` records
  the Wikisource revision ids and proofread levels (all level 4).
