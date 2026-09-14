# Vision Detection — Change Log & Known Issues

Engineering log for `vision/detect/`. Each change-log entry records what
changed and the `evaluate.py` metrics measured right after.

## Reproduce the numbers

```bash
cd vision && .venv/bin/python -m detect.evaluate
```

**Coverage report, not pass/fail** — several defect *causes* share one
*symptom* by design (`classify.py`), so a spread across a few tags can be
the correct answer for a row, not just one tag at 100%.

## Visualize a prediction

```bash
cd vision
.venv/bin/python -m detect.visualize --sample missing_carryover   # one sample
.venv/bin/python -m detect.visualize --all --mixed                # everything
```

Draws a ring on every dot in `vision/detect/annotated/`: **green** = correct,
**red** = wrong (ground-truth tag shown alongside), **teal** = not yet
judgeable (air bubble, satellite, speck), **yellow** = stray unmatched blob.

## Known issues

- **Severe misalignment reads as `missing`, not `misaligned`.** A dot past
  the capture radius (1.8× nominal r) from its expected spot reads as empty
  instead of offset. Our `misaligned` generator's drift grows with column
  index, so the far end of a row can exceed that radius — ~20% of
  `misaligned` dots currently read `missing`. Undecided whether the fix
  belongs in the detector (widen radius) or the generator (cap drift) — it's
  genuinely ambiguous past a point.
- **A defect on one dot drags its clean neighbor down too.** When two dots
  fuse (bridging, dragged), the aligner can't always tell which side is the
  real problem. Confirmed in `dragged_annotated.png`: the untagged, actually
  clean neighbor reads red, `FUSED (gt:ok)`, just for standing next to it.
  Same root cause after the 09-14 fix below, just shows up as `missing`
  instead of `possibly_fused` now — **not resolved, just changed shape.**

## Change log

### 2026-09-14 — Initial profile-aware detector

Added `vision/detect/`: `profile.py` (recipe schema), `segment.py` (Otsu +
contours, factored out of `main.py`), `align.py` (nearest-neighbor match to
profile positions, any pattern shape), `classify.py` (symptom tagging),
`report.py` (`detect()` entry point), `evaluate.py`. Also added
`nominal_cx/cy/r` to `vision/synth`'s `Dot` — a sample's sidecar now carries
a `profile` (recipe) section separate from `dots` (what actually happened),
since a misaligned dot needs something to compare its wrong position to.

**Baseline** (57 images, 916 dot-instances) — solid: `missing` 9/10,
`overrun` 7/7, `carryover_big`'s oversized half 7/10. Not attempted yet:
`air_bubble`, satellite/speck via `extra`, or disambiguating *why*
something's oversized.

<details>
<summary>Full breakdown</summary>

```
generator tag          n     predicted symptom breakdown
------------------------------------------------------------------------------
abnormal_shape         7     irregular=5, (nothing flagged)=1, undersized=1
air_bubble             3     (nothing flagged)=2, possibly_fused=1
bridging               18    missing=6, possibly_fused=3, oversized=3, irregular=3, misaligned=3
carryover_big          10    oversized=7, missing=2, irregular=1
double_dispense        7     oversized=4, (nothing flagged)=2, irregular=1
dragged                8     oversized=2, irregular=2, misaligned=2, missing=1, possibly_fused=1
ghost                  7     missing=4, possibly_fused=3
good                   658   (nothing flagged)=564, possibly_fused=33, oversized=20, irregular=20, misaligned=20, missing=1
inconsistent           68    (nothing flagged)=20, undersized=18, oversized=18, possibly_fused=7, irregular=3, misaligned=1, missing=1
line_end_defect        2     oversized=1, irregular=1
line_start_defect      2     possibly_fused=2
misaligned             90    misaligned=32, missing=22, (nothing flagged)=18, possibly_fused=10, oversized=4, irregular=4
missing                10    missing=9, possibly_fused=1
overrun                7     oversized=5, irregular=2
smearing               12    oversized=5, irregular=5, misaligned=2
stringing              7     irregular=5, oversized=1, misaligned=1

Extra (unmatched) blobs across all images: 27
```

</details>

### 2026-09-14 — Fusion-detection fix, `expected.py`, visualizer

Built `visualize.py` and immediately caught a real bug on the first sample
checked by eye: `bridging_dots` showed **both** positions as `missing` plus
the shared blob a third time as `extra` — `possibly_fused` never fired.

**Root cause:** a fused blob's centroid sits ~65px from each original
position on a 130px pitch — *past* the 47px capture radius — so neither
position ever claimed it, and the old fused-check only looked at
already-claimed blobs.

**Fix** (`align.py`): for an unmatched position, check whether some *other
unmatched* position shares the same nearest blob — mutual sharing, not
claim status, is what fusion actually looks like. That blob is also dropped
from `extra` once explained this way.

Added `expected.py`: one shared correct/incorrect table used by both
`evaluate.py` and `visualize.py`, so they can't silently disagree.

**Improved:** `missing` now 10/10. `bridging` now mostly `possibly_fused`
(was mostly `missing`). `ghost` and `line_start_defect` now clean `missing`
in every instance — the old check was producing false "fused" hints on
these genuinely-isolated cases. Stray `extra` blobs: 27 → 16.

**Still open:** `good`'s unwanted-flag rate didn't drop — it moved from
`possibly_fused` (33) to `missing` (30), same neighbor-contamination cause,
different wrong label. `misaligned`'s missing-instead-of-misaligned rate is
roughly unchanged. Both known issues above reflect this.

<details>
<summary>Full breakdown</summary>

```
generator tag          n     predicted symptom breakdown
------------------------------------------------------------------------------
abnormal_shape         7     irregular=5, (nothing flagged)=1, undersized=1
air_bubble             3     (nothing flagged)=2, possibly_fused=1
bridging               18    possibly_fused=6, missing=3, oversized=3, irregular=3, misaligned=3
carryover_big          10    oversized=7, possibly_fused=2, irregular=1
double_dispense        7     oversized=4, (nothing flagged)=2, irregular=1
dragged                8     possibly_fused=2, oversized=2, irregular=2, misaligned=2
ghost                  7     missing=7
good                   658   (nothing flagged)=564, missing=30, oversized=20, irregular=20, misaligned=20, possibly_fused=4
inconsistent           68    (nothing flagged)=20, undersized=18, oversized=18, possibly_fused=6, irregular=3, missing=2, misaligned=1
line_end_defect        2     oversized=1, irregular=1
line_start_defect      2     missing=2
misaligned             90    misaligned=32, (nothing flagged)=18, missing=18, possibly_fused=14, oversized=4, irregular=4
missing                10    missing=10
overrun                7     oversized=5, irregular=2
smearing               12    oversized=5, irregular=5, misaligned=2
stringing              7     irregular=5, oversized=1, misaligned=1

Extra (unmatched) blobs across all images: 16
```

</details>
