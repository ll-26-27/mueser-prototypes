# Inputs

The five synthetic Fraktur pages (`synth-01.png` … `synth-05.png`) and the
**machine transcriptions** of them by Kraken's `german_print` model, copied
unchanged from `01-use-cases/transcription/01-fraktur-print-bakeoff/outputs/runs/20261104-171047/kraken/german_print.mlmodel/`.
Each `.json` is the bake-off's sidecar for that page: backend, model, line count,
seconds.

These are OCR output, **not** the ground truth: they carry the model's
reading errors ("Verlin" for Berlin, "Lieqnitz", "Rönigsberg", "Ahr" for Uhr).
That is the point of this use case: what happens to a place name between the
page and the map when the transcription is imperfect.
