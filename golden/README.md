# Golden test cases

Fixture-only harness for validating NSW-automation reasoning logic before it
exists as real code. **Not an app** — no server, no UI, no dependency on
`web/` or `vision/`, and nothing here is imported by either. It exists so the
combination logic (user input + RAG knowledge + CV output → diagnosis) can be
exercised against fixed, hand-verified inputs while that logic is still being
built, instead of needing a live PDF-RAG pipeline, a live CV model, and a live
user in the loop all at once.

## Why "golden"

Each case fixes all three inputs to the NSW reasoning pipeline so the only
thing left to test is the combination logic itself:

1. **User input** — the operator always reports the defect the same way.
2. **RAG output** — retrieval is assumed 100% correct (that's what makes this
   a *golden* case rather than an evaluation of the retriever), so the RAG
   output is a fixed, pre-verified extract of `docs/personal/matc82.pdf`
   rather than something an actual retriever produces at test time.
3. **CV output** — a fixed JSON detection result, shaped exactly like
   `vision/detect/report.py`'s `detect()` return value, captured from an
   actual run against a real image that contains the defect in question
   (not hand-typed).

Nothing here is *called* live — no model, no retriever, no CV pipeline runs
when you check a golden case. The CV fixture was generated once, by running
the real pipeline against a real image, then frozen; the RAG fixture was
written once, by reading the real source PDF, then frozen. Every fixture is
static and versioned so runs stay reproducible without any of those systems
being available.

## Structure

```
golden/
  README.md                       -- this file
  check_golden.py                  -- stdlib-only sanity check over every case
  nsw_inconsistent_size/           -- the one case that exists so far
    README.md                      -- case-specific notes, citations, caveats
    user_input.json                 -- Answer[] (web/core/types.ts contract)
    inconsistent.png                 -- raw CV input image (real, not synthetic-only-in-JSON)
    inconsistent_profile.json        -- nominal dot-position recipe fed to detect()
    inconsistent_annotated.png       -- visualize.py's rendering of cv_output.json over the image
    cv_output.json                   -- real detect() output (vision/detect/report.py contract)
    signals.json                     -- Signal[] derived from cv_output.json (web/core/types.ts contract)
    rag_output.json                  -- golden retrieval result from matc82.pdf
    expected_reasoning.md            -- hand-authored expectation to check a real engine against
```

More cases (other defect classes, other tracks) get their own sibling folder
under `golden/` following the same five-file shape. Run all current checks
with:

```bash
python3 golden/check_golden.py
```
