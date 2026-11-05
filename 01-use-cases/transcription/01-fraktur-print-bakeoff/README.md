---
title: Fraktur print — nine readers on eight pages
description: Synthetic 1786 journal pages with exact ground truth plus three real pages from Wikisource → four Tesseract models, Kraken and four vision-language models read every page → CER raw and normalised, cost and time per page → an explorer with image, reading and diff, and a consensus with a check-in list.
author: claude
created: 2026-11-04
---

# Fraktur print: nine readers on eight pages

Open **`outputs/index.html`** to see every page beside every reading.

## What happened

| backend | model | pages | CER | WER | CER norm | WER norm | $/page | s/page |
|---|---|---|---|---|---|---|---|---|
| openrouter | `google/gemini-3.8-flash` | 8 | 0.011 | 0.048 | **0.006** | 0.022 | 0.0099 | 23 |
| openrouter | `google/gemini-3.1-pro-preview` | 8 | 0.012 | 0.052 | **0.006** | 0.019 | 0.0163 | 13 |
| openrouter | `anthropic/claude-haiku-5.5` | 8 | 0.025 | 0.125 | 0.007 | 0.028 | 0.0009 | 4 |
| openrouter | `qwen/qwen3-vl-235b-a22b-instruct` | 8 | 0.020 | 0.096 | 0.009 | 0.031 | 0.0019 | 21 |
| kraken | `german_print.mlmodel` | 8 | 0.026 | 0.120 | 0.018 | 0.080 | 0 | 10 |
| tesseract | `frak2021` | 8 | 0.043 | 0.139 | 0.032 | 0.095 | 0 | 1 |
| tesseract | `deu_latf` | 8 | 0.049 | 0.153 | 0.042 | 0.120 | 0 | 2 |
| tesseract | `Fraktur` (script) | 8 | 0.051 | 0.167 | 0.043 | 0.135 | 0 | 2 |
| tesseract | `deu_frak` | 8 | 0.077 | 0.266 | 0.060 | 0.183 | 0 | 4 |

Run `20261105-090715`; the four vision models cost $0.23 for the eight
pages. Skipped with a stated reason: `escriptorium` (no instance),
`mistral` and `transkribus` (optional, no key).

Per page, normalised CER:

| page | frak2021 | deu_latf | Kraken | Gemini 3.8 Flash | Gemini 3.1 Pro | Qwen3-VL 235B | Haiku 5.5 |
|---|---|---|---|---|---|---|---|
| synth-01 (clean) | 0.009 | 0.004 | 0.011 | 0.004 | 0.000 | 0.009 | 0.004 |
| synth-02 (blur 0.8) | 0.011 | 0.001 | 0.010 | 0.000 | 0.000 | 0.004 | 0.004 |
| synth-03 (blur + speckle) | 0.009 | 0.000 | 0.009 | 0.000 | 0.000 | 0.003 | 0.005 |
| synth-04 (rotated 0.8°) | 0.009 | 0.004 | 0.011 | 0.001 | 0.000 | 0.007 | 0.001 |
| synth-05 (bold Cook face) | 0.022 | 0.012 | 0.023 | 0.000 | 0.000 | 0.000 | 0.000 |
| real: Schiller, Musen-Almanach 1796, p. 93 (Antiqua) | 0.026 | 0.052 | **0.015** | 0.021 | 0.018 | 0.020 | 0.021 |
| real: Grimm, Kinder- und Haus-Märchen 1812, I p. 93 | 0.093 | 0.180 | 0.029 | 0.010 | 0.018 | 0.011 | **0.009** |
| real: Die Gartenlaube 1853, p. 1 (two columns, masthead) | 0.074 | 0.082 | 0.034 | 0.014 | **0.013** | 0.017 | 0.015 |

Three things the table says. The vision models read the two real Fraktur
pages at one wrong character in sixty to a hundred, two to three times
better than Kraken and seven to ten times better than Tesseract, for about
a cent a page. The raw column is where they lose: Haiku's raw CER (0.025)
is four times its normalised one because it modernises ſ to s on every
line, which the prompt forbids and the diff makes visible. And on the
Antiqua Schiller page Kraken is still the best reader, so the family that
wins depends on the page, which is what the consensus step is for.

One correction the layout pass (use case 03) made to this README: the
Schiller page is set in **Antiqua**, not Fraktur, which is part of why every
backend reads it well. The Grimm and Gartenlaube pages are Fraktur.

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
     --backends tesseract,tesseract:deu_latf,tesseract:Fraktur,tesseract:deu_frak,kraken,openrouter:google/gemini-3.8-flash,openrouter:google/gemini-3.1-pro-preview,openrouter:qwen/qwen3-vl-235b-a22b-instruct,openrouter:anthropic/claude-haiku-5.5 \
     --out   01-use-cases/transcription/01-fraktur-print-bakeoff/outputs --mode print
   ```

   Writes `outputs/bakeoff_<run_id>.csv` and `.json`, and
   `outputs/runs/<run_id>/<backend>/<model>/<page>.{txt,xml,json}`.
3. **The explorer** (deterministic code):

   ```sh
   uv run python -m mueser.text.report build --bakeoff outputs/bakeoff_<run_id>.json \
     --pages inputs/pages --gt inputs/gt --out outputs/index.html
   ```

4. **The consensus and the check-in list** (deterministic code; needs no
   ground truth):

   ```sh
   uv run python -m mueser.text.compare run --bakeoff outputs/bakeoff_<run_id>.json \
     --out outputs/consensus --gt inputs/gt --pages-dir inputs/pages
   ```

   `outputs/consensus/index.html` shows the agreement matrix, each reader's
   reliability, the medoid text with every disagreement marked, and the
   check-in list; `checkin.csv` is the same list with a `decision` column.
   `compare apply` writes corrected texts from the decisions.

The prompt the vision models receive is
`src/mueser/text/backends/prompts/transcribe_de.md`; its SHA-256 is recorded
with every reading, and the explorer prints it. Every call is cached by
(model, prompt, image), so reruns cost nothing. Any other OpenRouter vision
model is one more `openrouter:<id>` in `--backends`.

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
