# Evaluation

Measures the real pipeline — the same `run_vision`, `rank_causes` and
`backing` the API calls — on thousands of synthetic cases where the
right answer is known. No API, database or LLM; deterministic seeds.

```bash
uv run python evaluation/run_eval.py                  # ~1 min → results/latest.json, results/summary.md
uv run --with matplotlib python evaluation/plot.py    # → results/*.png (slide charts)
```

`results/summary.md` holds every table. Re-run both after any change to
`vision/` or `ranking/rules.py` — the numbers go stale otherwise.

`uv run python evaluation/compare.py` writes `results/before_after.md`,
comparing `results/before_fixes.json` (the run before the 2026-09-29
vision fixes: per-dot irregular count, lighting flattening, glare and
clutter checks in the quality gate) with the latest run. Two later
changes have their own tables, each against the run just before it:

- `before_after_registration.md` — lining the recipe up with the photo
  (2026-10-02): zoomed, off-centre and handheld framing 0% → 89% correct.
- `before_after_card_photos.md` — masking a desk around the part and
  correcting camera tilt (2026-10-02): a phone photo of the part on a desk
  0% → 89% correct.

## The three parts

| Part | Question | Truth comes from | Circular? |
|---|---|---|---|
| **A. Measurement** | Put a known defect in the photo: does the right signal fire? Does a good photo stay quiet? | The generator (`vision/synth`) | No |
| **B. Diagnosis** | Photo + a simulated operator's answers: is the top cause right, and does the number of reasons backing it track how often? | Scenario cards (`scenarios.py`) | Partly — see below |
| **C. Stress** | Damage the photo like a real camera would — blur, noise, light, glare, JPEG, clutter, and since 2026-10-02 framing: zoom, off-centre, handheld, a part on a desk with the camera tilted. Does it stay right, or refuse, rather than silently mis-measure? | The generator | No |

Outcome words used throughout:

- **Missed** — the defect's signal didn't fire. The ranking falls back on the interview. Not dangerous, but the photo added nothing.
- **False alarm** — a signal fired that the image does not contain. This is the outcome that misleads.
- **Refused** — the quality gate rejected the photo. The safe failure.

## What these numbers can and cannot claim

- **Every image is synthetic.** Flat, high-contrast deposits on a plain
  background — cleaner than any real board. Part C is how far past that
  the measurement holds; it is not a real-photo result. No real photos
  were available (see the root README).
- **The operator answers are team judgement.** `scenarios.py` was written
  from how each fault behaves physically (manual sections cited per card),
  *not* from the rule triggers, and deliberately includes plausible
  answers no rule rewards. Part B therefore measures whether the rule set
  is consistent with our own reading of the manual — not whether that
  reading matches NSW's floor. An engineer's review of the cards is the
  cheapest way to make Part B stronger.
- **Gate B, Pass 2, the follow-up questions and the troubleshooting loop
  are not exercised.** Part B scores the first ranking only (Pass 1 and
  the reasons behind its top cause), from the five spine answers, before
  any check is run. So these
  numbers are a floor for the full workflow, not its accuracy.
- **Chance is 14%** (one cause in seven).

## Third-party tools

numpy and OpenCV (already project dependencies) for image generation and
degradation; matplotlib (BSD-style licence), fetched only for `plot.py`.
