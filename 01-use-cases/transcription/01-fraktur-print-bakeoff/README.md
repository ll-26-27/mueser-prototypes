---
title: Fraktur print — five backends on eight pages
description: Synthetic 1786 journal pages with exact ground truth plus three real Fraktur pages from Wikisource → Tesseract (four models) and Kraken read every page → CER raw and normalised, cost and time per page → an explorer with image, reading and diff.
author: claude
created: 2026-11-04
---

# Fraktur print: five backends on eight pages

Open **`outputs/index.html`** to see every page beside every reading.

## What happened

| backend | model | pages | CER | WER | CER norm | WER norm | $/page | s/page |
|---|---|---|---|---|---|---|---|---|
| kraken | `german_print.mlmodel` | 8 | 0.026 | 0.120 | **0.018** | 0.080 | 0 | 9.9 |
| tesseract | `frak2021` | 8 | 0.043 | 0.139 | 0.032 | 0.095 | 0 | 0.9 |
| tesseract | `deu_latf` | 8 | 0.049 | 0.153 | 0.042 | 0.120 | 0 | 1.6 |
| tesseract | `Fraktur` (script) | 8 | 0.051 | 0.167 | 0.043 | 0.135 | 0 | 1.6 |
| tesseract | `deu_frak` | 8 | 0.077 | 0.266 | 0.060 | 0.183 | 0 | 3.4 |

Run `20261104-171047`, Apple Silicon laptop, no API calls. Skipped with a
stated reason: `openrouter` (no key), `mistral` (no key), `transkribus` (no
account; API needs the Scholar plan).

Per page, normalised CER:

| page | kraken | frak2021 | deu_latf | Fraktur | deu_frak |
|---|---|---|---|---|---|
| synth-01 (clean) | 0.011 | 0.009 | 0.004 | 0.003 | 0.026 |
| synth-02 (blur 0.8) | 0.010 | 0.011 | 0.001 | 0.004 | 0.030 |
| synth-03 (blur + speckle) | 0.009 | 0.009 | 0.000 | 0.006 | 0.013 |
| synth-04 (rotated 0.8°) | 0.011 | 0.009 | 0.004 | 0.010 | 0.018 |
| synth-05 (bold Cook face) | 0.023 | 0.022 | 0.012 | 0.011 | 0.000 |
| real: Schiller, Musen-Almanach 1796, p. 93 | **0.015** | 0.026 | 0.052 | 0.039 | 0.080 |
| real: Grimm, Kinder- und Haus-Märchen 1812, I p. 93 | **0.029** | 0.093 | 0.180 | 0.185 | 0.208 |
| real: Die Gartenlaube 1853, p. 1 (two columns, masthead) | **0.034** | 0.074 | 0.082 | 0.087 | 0.108 |

The pattern is the finding. On the synthetic pages Tesseract's `deu_latf`
is nearly perfect, because a typeface is exactly what it was trained on; on
the three real pages Kraken's `german_print` is two to six times better than
any Tesseract model. Scores on clean renderings say little about an 1812
impression. Kraken pays for it with ten seconds a page on CPU.

Three real-page caveats, visible in the explorer: the Wikisource ground truth
normalises ſ to s (so raw CER punishes every long s the backends read
correctly; use the normalised column); it does not keep prose line breaks
(scored on flattened text, so this does not matter); and the Gartenlaube
page is a two-column newspaper front with a decorated masthead, where
reading order is part of the error.

## The pipeline

0. **`operations/00-make-synthetic-pages.py`** (deterministic code). Renders
   `inputs/synthetic-text/reisetagebuch-1786.txt`, an invented journal written
   for this repository, into five pages in UnifrakturMaguntia (one in
   UnifrakturCook Bold) with recorded blur, speckle and rotation. The
   rendered lines are the ground truth, so CER on these pages is exact.
1. **`operations/01-fetch-ground-truth.py`** (deterministic code). Fetches
   the Wikisource proofread transcriptions of the three real pages, records
   the revision id and proofread level in `inputs/gt/provenance.json`, and
   strips the wiki markup.
2. **The bake-off** (deterministic for Tesseract and Kraken; model judgment
   for the vision models once keys exist):

   ```sh
   uv run python -m mueser.text.bakeoff run \
     --pages 01-use-cases/transcription/01-fraktur-print-bakeoff/inputs/pages \
     --gt    01-use-cases/transcription/01-fraktur-print-bakeoff/inputs/gt \
     --backends tesseract,tesseract:deu_latf,tesseract:Fraktur,tesseract:deu_frak,kraken,openrouter,mistral,transkribus \
     --out   01-use-cases/transcription/01-fraktur-print-bakeoff/outputs --mode print
   ```

   Writes `outputs/bakeoff_<run_id>.csv` and `.json`, and
   `outputs/runs/<run_id>/<backend>/<model>/<page>.{txt,xml,json}`.
3. **The explorer** (deterministic code):

   ```sh
   uv run python -m mueser.text.report build --bakeoff outputs/bakeoff_<run_id>.json \
     --pages inputs/pages --gt inputs/gt --out outputs/index.html
   ```

To add a vision model: put `OPENROUTER_API_KEY` in `.env` and add
`openrouter:qwen/qwen3-vl-30b-a3b-instruct,openrouter:google/gemini-2.5-flash,openrouter:anthropic/claude-haiku-5.5`
to `--backends`. The prompt they receive is
`src/mueser/text/backends/prompts/transcribe_de.md`; its SHA-256 is recorded
with every reading, and the explorer prints it. Every call is cached by
(model, prompt, image), so reruns cost nothing.

## Inputs and rights

- Synthetic pages: text by Claude (Fable 5.1), 4 November 2026, invented;
  fonts UnifrakturMaguntia and UnifrakturCook (SIL OFL 1.1). See
  `inputs/synthetic-text/README.md`.
- Real pages, from Wikimedia Commons, public domain: Schiller (ed.),
  *Musen-Almanach für das Jahr 1796*, p. 93; Grimm, *Kinder- und
  Haus-Märchen* I (1812), p. 93; *Die Gartenlaube* 1853, No. 1, p. 1. Ground
  truth from de.wikisource.org proofread pages (CC BY-SA 3.0), revision ids
  in `inputs/gt/provenance.json`.
- Models: `frak2021` (UB Mannheim, Stefan Weil), Tesseract `tessdata`
  models (Apache-2.0), Kraken `german_print` (Zenodo 10.5281/zenodo.10519596,
  CC0). Fetched by `uv run python -m mueser.text.models fetch tesseract|kraken`
  into `models/`, which git ignores.
