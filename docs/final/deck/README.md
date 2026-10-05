# Rebuilding the deck

`../AI-Dispensing-Defect-Detective.pptx` is the deck; edit it in PowerPoint.
This folder regenerates it from scratch — which overwrites any edits — when
the numbers change:

```bash
cd docs/final/deck
npm install pptxgenjs react-icons react react-dom sharp   # once
node build_deck.js                                        # writes AI-Dispensing-Defect-Detective.pptx here
```

The deck is **7 pitch slides** (title · problem · solution · the AI ·
third-party declaration · limitations · close) followed by **7 backup slides**
for Q&A. The spoken script, with timings per slide, is
[`../pitch-script.md`](../pitch-script.md) — keep the two in step, and note the
speaker notes on each slide repeat it.

`AI-Dispensing-Defect-Detective.pptx` is written here; copy it (and a PDF
export) up to `docs/final/` to publish it.

Numbers on the slides come from `evaluation/results/latest.json` (2026-10-05).
`assets/` holds the UI crops and the phone-photo pair; the annotated phone
photo is drawn from `detect()`'s own output on a simulated phone photo of a
printed sample card (the evaluation's `on_desk` condition).
