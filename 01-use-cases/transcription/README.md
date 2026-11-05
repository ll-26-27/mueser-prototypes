# Transcription

Two worked examples, one per kind of source Ben works with: Fraktur **print**
and Kurrent **handwriting**. Both run the same bake-off: several backends read
the same pages, each reading is scored against ground truth, and the
explorer page shows the image, every reading, the character-level diff and
the exact prompt that was sent.

| Use case | Pages | Backends that ran here | Best result | Open |
|---|---|---|---|---|
| [`01-fraktur-print-bakeoff/`](01-fraktur-print-bakeoff/) | 5 synthetic (exact ground truth) + 3 real (Wikisource) | Kraken `german_print`; Tesseract `frak2021`, `deu_latf`, `Fraktur`, `deu_frak` | Kraken: CER 0.018 normalised over 8 pages; 0.015 on the 1796 Schiller page | [explorer](01-fraktur-print-bakeoff/outputs/index.html) |
| [`02-kurrent-handwriting/`](02-kurrent-handwriting/) | 3 synthetic (Kurrent typeface) + 3 real (Commons) | Kraken `german_handwriting`; Tesseract (as a negative control) | Kraken: CER 0.21 on the 1864 Kaskel letter, 0.43 on Schnitzler 1896, 0.82 on a 1901 album page | [explorer](02-kurrent-handwriting/outputs/index.html) |

The vision-language models (Qwen3-VL, Gemini, Claude), Mistral OCR and
Transkribus are wired in and skipped with a stated reason until a key is in
`.env` (see [`resources/accounts.md`](../../resources/accounts.md)). Adding a
key and rerunning the one command in each README adds that backend to the
table and the explorer.

## How a bake-off works

1. **Pages** sit in `inputs/pages/`; **ground truth** in `inputs/gt/`, one
   text file per page with the same stem, and a `provenance.json` saying
   where each ground truth came from (rendered text, or a Wikisource revision
   id).
2. `uv run python -m mueser.text.bakeoff run …` asks each backend to read
   each page. A backend is a small class with `check()` (can it run here? if
   not, why not) and `transcribe()` (image in, lines out). Tesseract and
   Kraken return line boxes; vision models return text only.
3. Every reading is written three ways under `outputs/runs/<run_id>/<backend>/<model>/`:
   plain text, PAGE-XML (the interchange format Transkribus and eScriptorium
   read) and a JSON sidecar with model, seconds, cost and prompt hash.
   `run.json` records the whole run.
4. `evaluate.score()` computes the **character error rate** (edits per
   ground-truth character) and word error rate, twice: raw, and after a
   declared normalisation (ſ→s, superscript umlauts, hyphenation, whitespace)
   so a model that silently modernises is neither punished nor rewarded
   without the reader seeing both numbers.
5. `mueser.text.report` builds `outputs/index.html`: the summary table, the
   skipped backends, the prompt, and for each page every backend's reading
   with the diff against ground truth.

## What the numbers mean

A CER of 0.02 is one wrong character in fifty: usable for search, not for an
edition. 0.20 is one in five: the text is recognisable but every line needs
a hand. Synthetic pages give an upper bound (a typeface is cleaner than any
press or pen); the real pages are the measurement, and three of them are
too few. Ben's own corrected pages, exported as PAGE-XML into `inputs/gt/`,
are what the table should finally be built on.
