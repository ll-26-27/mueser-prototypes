---
title: Kurrent handwriting — seven readers on six pages
description: Three synthetic letters in a Kurrent typeface and three real letters and album pages from Commons → Kraken's open German handwriting model, Tesseract as a control, and five vision-language models → CER per page, an explorer, and a consensus with a check-in list.
author: claude
created: 2026-11-04
---

# Kurrent handwriting: seven readers on six pages

Open **`outputs/index.html`**.

## What happened

| backend | model | pages | CER | WER | CER norm | WER norm | $/page | s/page |
|---|---|---|---|---|---|---|---|---|
| openrouter | `google/gemini-3.8-flash` | 5 of 6 | 0.171 | 0.259 | **0.163** | 0.216 | 0.0125 | 80 |
| openrouter | `google/gemini-3.1-pro-preview` | 6 | 0.175 | 0.306 | **0.161** | 0.234 | 0.0097 | 9 |
| openrouter | `anthropic/claude-sonnet-5.5` | 6 | 0.279 | 0.411 | 0.269 | 0.352 | 0.0169 | 6 |
| kraken | `german_handwriting.mlmodel` | 6 | 0.329 | 0.677 | 0.315 | 0.635 | 0 | 11 |
| openrouter | `qwen/qwen3-vl-235b-a22b-instruct` | 6 | 0.347 | 0.548 | 0.342 | 0.521 | 0.0015 | 10 |
| openrouter | `anthropic/claude-haiku-5.5` | 6 | 0.367 | 0.538 | 0.358 | 0.493 | 0.0011 | 7 |
| tesseract | `frak2021` (control) | 6 | 0.850 | 0.998 | 0.849 | 0.998 | 0 | 1 |

Run `20261105-090715`, $0.24 for the five vision models. Per page, normalised CER:

| page | Kraken | Gemini 3.8 Flash | Gemini 3.1 Pro | Sonnet 5.5 | Qwen3-VL 235B | Haiku 5.5 |
|---|---|---|---|---|---|---|
| real: Kaskel to Schnorr von Carolsfeld, 1864 (a clean secretary hand) | 0.207 | **0.060** | **0.060** | 0.082 | 0.365 | 0.203 |
| real: Schnitzler to Beer-Hofmann, 1896 (a fast private hand) | 0.429 | failed | **0.176** | 0.680 | 0.600 | 0.696 |
| real: Poesiealbum von Hedwig, 1901, p. 2 (photograph, slanted, bracketed ground truth) | 0.819 | 0.710 | 0.708 | 0.799 | 0.743 | 0.804 |
| synth-01 (Wiegel Kurrent regular) | 0.068 | 0.002 | 0.007 | 0.013 | 0.078 | 0.115 |
| synth-02 (regular, blurred, rotated) | 0.213 | 0.027 | 0.011 | 0.025 | 0.168 | 0.245 |
| synth-03 (bold) | 0.156 | 0.019 | 0.004 | 0.013 | 0.097 | 0.084 |

Three readings of the result:

- **On the clean 1864 hand the two Gemini models read at one wrong
  character in seventeen** where the open Kraken model has one in five. On
  the fast 1896 hand Gemini 3.1 Pro is at one in six and everything else
  at one in two or worse. This is the gap a hosted Kurrent model
  (Transkribus, or a Kraken model trained on Ben's own lines) would have to
  close.
- **The album photograph defeats every reader** (0.71 at best). The layout
  pass in use case 03 says why: text written over a chromolithograph, a torn
  corner, uneven light. The ground truth also carries the uploader's own
  square brackets, which count as errors against any reader. This page is
  the argument for a photography standard before a model choice.
- **One failure is recorded, not hidden.** Gemini 3.8 Flash returned an
  empty, non-JSON reply five times on the Schnitzler letter and the run
  lists the page as an error for that backend; its mean is over five pages.
  Gemini 3.8 Flash was also slow (80 s a page, against 9 s for 3.1 Pro).

Read the Kaskel readings in the explorer side by side: Kraken has
"ſochgeehrteſtir rennd" for "Hochverehrter Freund", Haiku invents
"hochverfluchten Sohn", and the two Geminis differ from the ground truth
mostly in "Hochgeehrter" against "Hochverehrter", which a person should
settle from the image. The consensus page puts that span on the check-in
list; on the two harder real pages it says plainly that the readers
disagree too much for a span-level check-in.

**A model that did not load.** Zenodo 10.5281/zenodo.21747522
(`german_handwriting_kurrent_v3`, fine-tuned on twelve pages of Louise Le
Beau's diaries, 2026) downloads but Kraken 7.1.1 reports "not loadable by
any parser"; it is a newer serialisation. Recorded here rather than dropped.

## The pipeline

0. **`operations/00-make-synthetic-pages.py`** (deterministic code). Renders
   `inputs/synthetic-text/briefe.txt` (two invented letters and an accounts
   page, 1786) in Wiegel Kurrent regular and bold.
1. **`operations/01-fetch-ground-truth.py`** (deterministic code). Fetches
   the transcriptions that accompany the three Commons images (written by
   the uploaders or the holding institution), with revision ids, into
   `inputs/gt/`.
2. **The bake-off:**

   ```sh
   uv run python -m mueser.text.bakeoff run \
     --pages 01-use-cases/transcription/02-kurrent-handwriting/inputs/pages \
     --gt    01-use-cases/transcription/02-kurrent-handwriting/inputs/gt \
     --backends kraken,tesseract,openrouter:google/gemini-3.8-flash,openrouter:google/gemini-3.1-pro-preview,openrouter:qwen/qwen3-vl-235b-a22b-instruct,openrouter:anthropic/claude-haiku-5.5,openrouter:anthropic/claude-sonnet-5.5 \
     --out   01-use-cases/transcription/02-kurrent-handwriting/outputs --mode hand
   ```

   `--mode hand` picks Kraken's handwriting model and tells the vision
   models they are reading Kurrent.
3. **The explorer and the consensus:** `uv run python -m mueser.text.report build …`
   and `uv run python -m mueser.text.compare run …` as in the Fraktur use case.

## What a font is not

The synthetic pages test whether a backend knows Kurrent letterforms at all;
they say nothing about real hands, where every "e" is different, lines
drift, and the writer corrects themself. Hence the three real pages, and
hence the gap between 0.07 and 0.82.

## Inputs and rights

- Synthetic: text by Claude (Fable 5.1), invented, 4 November 2026; Wiegel
  Kurrent by Peter Wiegel (SIL OFL 1.1; licence text in `models/fonts/`).
- Kaskel letter: Deutsche Fotothek / SLUB Dresden, Mscr.Dresd.n.Inv.15.Bd.21,
  Bl. 84, public domain; transcription from the Commons description.
- Schnitzler letter: private collection, rights released by the owner on
  Commons; transcription from the Commons description (the Schnitzler-Briefe
  edition at acdh.oeaw.ac.at has the letter as L00539).
- Poesiealbum von Hedwig p. 2: photograph by a Commons user, **CC BY 4.0**
  (not public domain), downscaled here to 3000 px; transcription from the
  uploader, square brackets are theirs. Not a checked edition.
