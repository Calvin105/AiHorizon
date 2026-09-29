# Evaluation

Measures the real pipeline — the same `run_vision`, `rank_causes` and
`compute_stars` the API calls — on thousands of synthetic cases where the
right answer is known. No API, database or LLM; deterministic seeds.

```bash
uv run python evaluation/run_eval.py                  # ~30 s → results/latest.json, results/summary.md
uv run --with matplotlib python evaluation/plot.py    # → results/*.png (slide charts)
```

`results/summary.md` holds every table. Re-run both after any change to
`vision/` or `ranking/rules.py` — the numbers go stale otherwise.

`uv run python evaluation/compare.py` writes `results/before_after.md`,
comparing `results/before_fixes.json` (the run before the 2026-09-29
vision fixes: per-dot irregular count, lighting flattening, glare and
clutter checks in the quality gate) with the latest run.

## The three parts

| Part | Question | Truth comes from | Circular? |
|---|---|---|---|
| **A. Measurement** | Put a known defect in the photo: does the right signal fire? Does a good photo stay quiet? | The generator (`vision/synth`) | No |
| **B. Diagnosis** | Photo + a simulated operator's answers: is the top cause right, and do the stars track how often? | Scenario cards (`scenarios.py`) | Partly — see below |
| **C. Stress** | Damage the photo like a real camera would: does it stay right, or refuse, rather than silently mis-measure? | The generator | No |

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
- **Gate B, Pass 2 and the troubleshooting loop are not exercised.** Part B
  scores the first ranking only (Pass 1 + stars), before any check is run.
  So these numbers are a floor for the full workflow, not its accuracy.
- **Chance is 14%** (one cause in seven).

## Third-party tools

numpy and OpenCV (already project dependencies) for image generation and
degradation; matplotlib (BSD-style licence), fetched only for `plot.py`.
