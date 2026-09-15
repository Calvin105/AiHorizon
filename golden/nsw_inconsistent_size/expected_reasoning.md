# Expected reasoning -- nsw_inconsistent_size

Hand-authored expectation for whatever engine eventually consumes
`user_input.json` + `signals.json` (or `cv_output.json` directly) +
`rag_output.json` for this case. Not a strict schema to assert equality
against -- `Analysis.causes` ranking is a probability distribution, not a
single right answer -- but the following should hold for any engine that is
actually using all three inputs rather than ignoring one of them.

## What a correct analysis should surface

- **Top-line symptom**: array-level size scatter -- both oversized and
  undersized deposits present in the same image, not a one-directional
  shift. `cv_output.json` (the real `detect()` output for `inconsistent.png`)
  encodes this directly (`counts.oversized == 3`, `counts.undersized == 4`,
  `counts.inconsistent == 8` out of 15 dots); `signals.json`'s
  `size_cv = 0.486` is the scalar summary of the same fact. Visually this is
  what `inconsistent_annotated.png` shows: a 5x3 array with dots of
  noticeably different sizes scattered with no row/column pattern.
- **Grounded mechanism**: the reasoning should cite the marginal-wetting /
  carryover mechanism from `rag_output.json` (matc82 secs 3.5/4.5/5.5) --
  a shot that fails to wet reads small, and the undeposited material
  carries onto the next shot, which reads oversized. This is what
  distinguishes "inconsistent" from a systemic bias like
  `parameter_drift` (which the existing pack already down-weights for this
  deviation, matching only "Too much"/"Too little") or a pure air-in-line
  explanation.
- **Discriminating negative**: `mean_circularity = 0.896` is above the 0.8
  threshold the existing pack uses for `nozzle_blockage`, so that cause
  should rank low -- shape is fine, only size scatters.

## A gap worth knowing about before building the real pipeline

`web/packs/nsw/index.ts`'s `air_entrapment` cause already fires on this
exact case today (deviation = "Inconsistent...", `size_cv = 0.486 > 0.15`,
weight 0.9 + 0.9), and would currently come out on top for engine B. But the
document this case's RAG output is grounded in never mentions air
entrapment in this context at all -- matc82's own explanation for
alternating small/big dots is the wetting-carryover mechanism in secs
3.5/4.5/5.5, not a compressible void. (Air is discussed only for underfills
in sec 7.2, which is a different material class and a different defect --
air bubble, class #4 in `docs/personal/visual signature.md`, not class #11
"inconsistent size".)

That means one of two things needs to happen when the RAG-grounded
reasoning is actually built, and this golden case exists partly to force
that decision rather than let it default silently:

1. Add a `dispense_volume_carryover` (or similarly named) cause to
   `NSW_CAUSES`, grounded in matc82 3.5/4.5/5.5, so the fault tree has a
   correct top hypothesis to converge on for this defect -- not just a
   plausible-sounding existing one.
2. Or, if `air_entrapment` is kept as the label, its `rules[].detail` text
   for the "Inconsistent" deviation should be rewritten to actually match
   what matc82 says, rather than asserting a compressible-void mechanism
   the source document doesn't support for this defect class.

Either way: an engine that reads `rag_output.json` and still concludes
"air entrapment" for the wrong reason (citing air, not carryover) has
failed this golden case even if the *label* happens to rank first --
grounding is being scored here, not just the final ranking.
