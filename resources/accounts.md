# Accounts and keys

Every external service this repository can call, what it costs, how to sign
up with the Learning Lab account, and where the key goes. Nothing here is
required to run the keyless baseline (Tesseract, Kraken, GOV, Wikidata, WHG);
each key switches on one more backend or resolver. Checked 4 November 2026.

Keys go in `.env` at the repository root (copy `.env.example`). Git ignores
`.env`. Never paste a key into a prompt, a notebook, or a Markdown file.

| Service | Used for | Free tier | Sign up | Key variable |
|---|---|---|---|---|
| **OpenRouter** · **in place** | every vision-language model (Gemini 3.8 Flash and 4 Argon, Qwen3-VL, Claude, GPT) and the extraction model, through one API | the Learning Lab's existing account and key are in `.env` | https://openrouter.ai/keys | `OPENROUTER_API_KEY` |
| **eScriptorium** | the open HTR platform (Kraken inside) with a GUI for correction, training and PAGE-XML export; the backend drives any instance through its REST API | free; self-hosted with Docker (`gitlab.com/scripta/escriptorium`) or a lab-hosted instance with an account | run or join an instance → profile → API token | `ESCRIPTORIUM_URL`, `ESCRIPTORIUM_TOKEN` |
| **Google AI Studio** (optional) | a direct Gemini key, only if a Gemini model appears there before OpenRouter lists it | free tier | https://aistudio.google.com/ | not wired; say so and a `google` backend is a small addition |
| **Mistral** (optional, not needed) | Mistral OCR, a dedicated document-OCR endpoint | "Experiment" plan after phone verification | https://console.mistral.ai/ | `MISTRAL_API_KEY` |
| **Transkribus** (optional) | READ-COOP's hosted HTR; strongest public Kurrent models | 50 pages/month in the app; **API only on Scholar (€99/year)** | https://app.transkribus.org/ | `TRANSKRIBUS_USER`, `TRANSKRIBUS_PASSWORD`, `TRANSKRIBUS_HTR_ID` |
| **GeoNames** | fourth gazetteer, strong on alternate names | 10,000 credits/day, 1,000/hour; no card | https://www.geonames.org/login → confirm email → https://www.geonames.org/manageaccount → **"Click here to enable"** free web services (a separate step that is easy to miss) | `GEONAMES_USERNAME` |
| **Hugging Face** | only for gated models or to upload a fine-tune later | free | https://huggingface.co/join → Settings → Access tokens | `HF_TOKEN` |
| **World Historical Gazetteer** | third gazetteer | free; most endpoints now want a token from the profile page, though the index search answered without one | https://whgazetteer.org/ → profile | not wired yet; add `WHG_TOKEN` if the index search starts refusing |

## What to pay for, if anything

- **Nothing yet.** With the OpenRouter key the whole bake-off runs: Gemini
  3.8 Flash reads a page for about a cent, Qwen3-VL 235B for under one,
  Claude Haiku 5.5 for a tenth of one. The first Kurrent run put Gemini 3.8
  Flash at CER 0.06 on the 1864 letter where Kraken had 0.21.
- **eScriptorium costs time, not money:** Docker Desktop on a laptop, or a
  small server for the lab. It is where Ben corrects pages and trains a model
  on his own hand-corrected lines; the Kraken models here load into it.
- **Transkribus Scholar** only if a direct comparison with its Kurrent models
  is wanted; the free in-app credits show their quality without the API.

## Signing up

The remaining signups (GeoNames, and eScriptorium once an instance exists)
are for a person to do; after each one, paste the key into `.env` and run

```sh
uv run python -m mueser.text.bakeoff run --pages 01-use-cases/transcription/01-fraktur-print-bakeoff/inputs/pages \
  --gt 01-use-cases/transcription/01-fraktur-print-bakeoff/inputs/gt --backends openrouter:google/gemini-3.8-flash,hybrid:google/gemini-3.8-flash \
  --out 01-use-cases/transcription/01-fraktur-print-bakeoff/outputs
```

The run lists which backends ran and which were skipped, with the reason.

## Verification emails

Signups send a confirmation to the Learning Lab Gmail. GeoNames will not
work until the link in that email is clicked and the extra "enable web
services" click above is done.
