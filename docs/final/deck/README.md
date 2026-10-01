# Rebuilding the deck

`../AI-Dispensing-Defect-Detective.pptx` is the deck; edit it in PowerPoint.
This folder regenerates it from scratch — which overwrites any edits — when
the numbers change:

```bash
cd docs/final/deck
npm install pptxgenjs react-icons react react-dom sharp   # once
node build_deck.js                                        # writes AI-Dispensing-Defect-Detective.pptx here
```

Numbers on the slides come from `evaluation/results/latest.json` (2026-10-02).
`assets/` holds the UI crops and the phone-photo pair; the annotated phone
photo is drawn from `detect()`'s own output on a simulated phone photo of a
printed sample card (the evaluation's `on_desk` condition).
