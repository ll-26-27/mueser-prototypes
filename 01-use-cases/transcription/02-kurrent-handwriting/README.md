---
title: Kurrent handwriting — what runs without a key
description: Three synthetic letters in a Kurrent typeface and three real letters and album pages from Commons → Kraken's open German handwriting model and Tesseract as a negative control → CER per page → an explorer; the vision models and Transkribus are wired and waiting for keys.
author: claude
created: 2026-11-04
---

# Kurrent handwriting: what runs without a key

Open **`outputs/index.html`**.

## What happened

| backend | model | pages | CER | WER | CER norm | WER norm | s/page |
|---|---|---|---|---|---|---|---|
| kraken | `german_handwriting.mlmodel` | 6 | 0.329 | 0.677 | 0.315 | 0.635 | 23 |
| tesseract | `frak2021` | 6 | 0.850 | 0.998 | 0.849 | 0.998 | 1 |

Run `20261104-181312`. Per page, normalised CER, Kraken:

| page | CER norm | what it is |
|---|---|---|
| synth-01 | 0.068 | letter, Wiegel Kurrent regular |
| synth-02 | 0.213 | letter, regular, blurred and rotated |
| synth-03 | 0.156 | accounts page, Wiegel Kurrent bold |
| real: Carl von Kaskel to Julius Schnorr von Carolsfeld, 1864 | **0.207** | a clean secretary's hand, SLUB Dresden |
| real: Arthur Schnitzler to Richard Beer-Hofmann, 1896 | 0.429 | a fast private hand |
| real: Poesiealbum von Hedwig, 1901, p. 2 | 0.819 | photographed album page, uneven lighting, text on a slant |

Tesseract is in the table as a control: a print model on handwriting gives
CER 1.0, which is what "wrong tool" looks like in numbers.

Read Kraken's Kaskel reading in the explorer: "Hochverehrter Freund" comes
out as "ſochgeehrteſtir rennd", then whole lines are right ("So herrlich und
unvergleichlich, als / geſtern im unſterblichen Werke"). A CER of 0.21 means
the model gets the shapes but not the word; it is the point where a
Kurrent-specific model (Transkribus's, or the fine-tuned Kraken model below)
or a vision model with a language sense should pull ahead. That comparison
is the one this use case is set up to make once a key is in `.env`.

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
     --backends kraken,tesseract,openrouter,mistral,transkribus \
     --out   01-use-cases/transcription/02-kurrent-handwriting/outputs --mode hand
   ```

   `--mode hand` picks Kraken's handwriting model and tells the vision
   models they are reading Kurrent.
3. **The explorer:** `uv run python -m mueser.text.report build …` as in the
   Fraktur use case.

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
