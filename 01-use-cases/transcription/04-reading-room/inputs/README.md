# Inputs

Copies, with their origins. Nothing here is written by a model; the
readings are the files the earlier cases produced, copied unchanged.

- `pages/real-grimm-khm-1812-i-p093.jpg`: *Kinder- und Haus-Märchen*,
  Erster Band (Berlin, 1812), p. 93. Wikimedia Commons
  `File:Kinder_und_Hausmärchen_(Grimm)_1812_I_093.jpg`, public domain.
- `pages/real-schiller-musenalmanach-1796-p093.jpg`: *Musen-Almanach für
  das Jahr 1796*, ed. Schiller (Neustrelitz, 1796), p. 93. Commons
  `File:Schiller_Musenalmanach_1796_093.jpg`, public domain.
- `pages/real-kaskel-to-schnorr-1864.jpg`: letter from Carl Kaskel to
  Julius Schnorr von Carolsfeld, 1864, leaf numbered 84. Deutsche Fotothek
  (SLUB Dresden), Commons
  `File:Fotothek_Df_hauptkatalog_0280537_&_0280538.jpg`, public domain.
- `metadata.json`: the bibliographic record of each document, hand-written,
  used for every citation the page produces; `image_sha256` is the hash of
  the copy in `pages/`.
- `readings/consensus/<page>.consensus.json`: the page's entry in
  `03-layout-and-hybrid/outputs/consensus-{print,hand}/consensus.json`,
  with the run id and threshold.
- `readings/medoid/<page>.json`: the run JSON of the reader that consensus
  named the medoid (raw lines, model, prompt hash, cost).
- `readings/segmentation/<page>.json`: the hybrid reading of the page
  (Gemini 3.8 Flash on Kraken's line crops), whose every line has a box.
- `readings/provenance.json`: for every file above, the path it was copied
  from and its sha256, written by `operations/00-collect-inputs.py`.

Where the pages came from and under what licence is recorded in the
earlier cases: `01-fraktur-print-bakeoff/inputs/README.md` and
`02-kurrent-handwriting/inputs/README.md`, with Wikisource and Commons
revision ids in their `gt/provenance.json`.
