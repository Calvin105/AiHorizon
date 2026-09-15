# Golden case: nsw_inconsistent_size

One fixed defect scenario for the NSW track: the user always reports
**"Inconsistent size shot to shot"**, the CV pipeline always sees the same
real 15-dot array (`inconsistent.png`, actually run through `detect()`, not
hand-typed) with a scattered-size signature, and RAG retrieval against
`docs/personal/matc82.pdf` is treated as 100% correct and pinned to a
hand-verified extract. This isolates the one thing that doesn't exist yet --
the logic that combines the three -- from the three retrieval/inference
systems that could each independently be wrong or not-yet-built.

## Files

| File | Contract | Notes |
|---|---|---|
| `user_input.json` | `Answer[]` from `web/core/types.ts` | Matches the `deviation` question's real option string from `web/packs/nsw/index.ts` (`NSW_QUESTIONS`), so it's usable verbatim wherever that pack is loaded. |
| `inconsistent.png` | raw CV input | Copied from `vision/samples/inconsistent.png` -- the actual synthetic-but-rendered image fed to `detect()`, a 5x3 grid. |
| `inconsistent_profile.json` | `detect()`'s `--profile` argument | Copied from `vision/samples/inconsistent.json` -- the nominal dot-position recipe (and this sample's generator ground truth) used to align blobs against. Kept so the run below is reproducible from this folder alone, without needing `vision/samples/`. |
| `inconsistent_annotated.png` | visualization | Copied from `vision/detect/annotated/inconsistent_annotated.png` -- `visualize.py`'s rendering of `cv_output.json` over `inconsistent.png`, right/wrong colour-coded per `vision/detect/expected.py`. |
| `cv_output.json` | `detect()` return value from `vision/detect/report.py` | **Not hand-typed** -- the literal output of running `.venv/bin/python -m detect.run samples/inconsistent.png --profile samples/inconsistent.json` from `vision/`. `classify_array`'s array-level scatter rule tags 4 dots `undersized`, 3 `oversized`, and 8 otherwise-clean dots `inconsistent`. |
| `signals.json` | `Signal[]` from `web/core/types.ts` | Derived by hand from `cv_output.json` (see the `note` field on each entry for the exact arithmetic). **No code in this repo currently computes this aggregation** -- `vision/detect/` returns per-dot tags, not the `size_cv`/`mean_circularity` scalars `web/packs/nsw/index.ts`'s rules key off. Something will need to compute `signals.json` from `cv_output.json` when NSW automation is actually wired up; this file is what that function's output should look like for this case. |
| `rag_output.json` | ad hoc golden-retrieval shape | Six passages, all page/section-verified by reading the PDF directly, plus one curated cross-reference to `docs/personal/visual signature.md` row 11. |
| `expected_reasoning.md` | prose | What a correct combined analysis should conclude, and a specific gap it surfaces in the current hardcoded `NSW_CAUSES` pack (see below). |

## Reproducing cv_output.json

```bash
cd vision && .venv/bin/python -m detect.run samples/inconsistent.png --profile samples/inconsistent.json
```

Deterministic (classical CV, no model) -- re-running this should reproduce
`cv_output.json` exactly.

## The one finding this case already surfaced

The existing `air_entrapment` cause in `web/packs/nsw/index.ts` already
matches this exact input (deviation = "Inconsistent...", `size_cv = 0.486 >
0.15`) and would rank first today under engine B. But matc82 never attributes
alternating small/big dots to air -- its own explanation is the
wetting/carryover mechanism in secs 3.5/4.5/5.5. Full writeup in
`expected_reasoning.md`. Worth resolving (new cause vs. rewritten
justification text) before or while building the RAG-grounded reasoning
this folder is a rehearsal for.

## Running the check

From the repo root:

```bash
python3 golden/check_golden.py
```

Validates shapes and the internal arithmetic (`size_cv`/`mean_circularity`
in `signals.json` actually follow from `cv_output.json`), not any reasoning
output -- there's no reasoning engine to call yet.
