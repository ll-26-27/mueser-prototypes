# Accounts and keys

Every external service this repository can call, what it costs, how to sign
up with the Learning Lab account, and where the key goes. Nothing here is
required to run the keyless baseline (Tesseract, Kraken, GOV, Wikidata, WHG);
each key switches on one more backend or resolver. Checked 4 November 2026.

Keys go in `.env` at the repository root (copy `.env.example`). Git ignores
`.env`. Never paste a key into a prompt, a notebook, or a Markdown file.

| Service | Used for | Free tier | Sign up | Key variable |
|---|---|---|---|---|
| **OpenRouter** | every vision-language model (Qwen3-VL, Gemini, Claude, GPT) and the extraction model, through one API | small starting allowance; `:free` vision models at 50 requests/day (1,000/day after a $10 top-up) | https://openrouter.ai/sign-up → Keys | `OPENROUTER_API_KEY` |
| **Mistral** | Mistral OCR (`mistral-ocr-latest`), a dedicated document-OCR endpoint | "Experiment" plan: free API use after phone verification, no card; whether OCR pages are included is not confirmed | https://console.mistral.ai/ → API keys; Admin Console → La Plateforme → Subscription → "Experiment for free" | `MISTRAL_API_KEY` |
| **Transkribus** (READ-COOP) | the strongest public Kurrent and Fraktur HTR models, in a GUI with correction and training | 50 credits/month in the app (1 credit = 1 page); **the API needs the Scholar plan (€99/year, 900 credits)** | https://app.transkribus.org/ | `TRANSKRIBUS_USER`, `TRANSKRIBUS_PASSWORD`, `TRANSKRIBUS_HTR_ID` |
| **GeoNames** | fourth gazetteer, strong on alternate names | 10,000 credits/day, 1,000/hour; no card | https://www.geonames.org/login → confirm email → https://www.geonames.org/manageaccount → **"Click here to enable"** free web services (a separate step that is easy to miss) | `GEONAMES_USERNAME` |
| **Hugging Face** | only for gated models or to upload a fine-tune later | free | https://huggingface.co/join → Settings → Access tokens | `HF_TOKEN` |
| **World Historical Gazetteer** | third gazetteer | free; most endpoints now want a token from the profile page, though the index search answered without one | https://whgazetteer.org/ → profile | not wired yet; add `WHG_TOKEN` if the index search starts refusing |

## What to pay for, if anything

- **Transkribus Scholar** is the one paid tier worth testing. Its German
  Kurrent models are the reference point every open backend is measured
  against, and the API is what lets the bake-off include it. Use the free
  in-app credits first to see the quality on three or four real pages; buy
  Scholar only if the pages Ben cares about are handwritten.
- **OpenRouter credit** of $10 buys thousands of pages through Qwen3-VL
  (about $0.15 per million input tokens; a page image is a few thousand
  tokens) and raises the free-model limit. The Gemini models are also here
  (`google/gemini-2.5-flash`, `google/gemini-2.5-flash-lite`, and newer
  `gemini-3.x` ids as OpenRouter lists them); pass any of them with
  `--backends openrouter:<model id>`.
- **Mistral OCR** is $4 per 1,000 pages at list price. Cheap enough to run on
  every page once the Experiment plan question is settled.

## Signing up

The five signup pages were opened in Chrome tabs on 4 November 2026. Account
creation and password entry are for a person to do; after each one, paste the
key into `.env` and run

```sh
uv run python -m mueser.text.bakeoff run --pages 01-use-cases/transcription/01-fraktur-print-bakeoff/inputs/pages \
  --gt 01-use-cases/transcription/01-fraktur-print-bakeoff/inputs/gt --backends openrouter,mistral \
  --out 01-use-cases/transcription/01-fraktur-print-bakeoff/outputs
```

The run lists which backends ran and which were skipped, with the reason.

## Verification emails

Signups send a confirmation to the Learning Lab Gmail. Transkribus and
GeoNames will not work until the link in that email is clicked; GeoNames then
needs the extra "enable web services" click above.
