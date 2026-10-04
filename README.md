# AI Dispensing Defect Detective

**AI Horizon Solution Challenge 2026 — Challenge 2, NSW Automation**

An AI troubleshooting assistant for fluid dispensing defects. An operator describes
what went wrong and photographs it if they can — a phone photo of the part is enough.
The system measures the deposits, interviews the operator, ranks the possible causes
with every reason shown, recommends what to check first, and produces a printable
report.

The submission is **`pipeline/`**. Everything else in this repo is the exploration
that led to it — see [Repository layout](#repository-layout).

> **The design bet:** most of this system deliberately does *not* ask a language
> model what the cause is. Percentages come from a weighted fault tree over measured
> evidence, so every number can be traced to the rule and the manual page that
> produced it. The LLM is optional and never sets a likelihood: it is a second
> opinion that can *disagree*, it maps an operator's own words onto an option, and it
> writes the final explanation. Why, and what it costs, is in
> [The design bet](#the-design-bet).

---

## Running it

Requires [uv](https://docs.astral.sh/uv/), Node 20+ and pnpm.

```bash
# 1. Python environment (uv workspace: backend + vision metrology package)
uv sync

# 2. The demo database, in one offline command: schema, catalog, four showcase
#    cases driven through the real API, and 29 closed history cases.
#    A copy of any existing pipeline.db goes to pipeline/backend/backups/ first.
#    Run it again at any time to start over, with the demo running or not.
scripts/reset-demo.sh
cp pipeline/backend/.env.example pipeline/backend/.env   # optional: add a GROQ_API_KEY

# 3. Frontend dependencies, once
(cd pipeline/frontend && pnpm install --frozen-lockfile)

# 4. Run everything: backend on localhost:8001, frontend on :3001
scripts/start-demo.sh                # LLM_ENABLED=false for a fully offline run
```

Open **http://localhost:3001**. The launcher also prints a phone URL and a QR code.
The frontend forwards `/api` to the backend, so a phone on the same Wi-Fi or hotspot
can open the app and photograph a part with its own camera.

Without a `GROQ_API_KEY`, or with `LLM_ENABLED=false`, everything still runs. The
LLM-backed steps say "unavailable" on screen, and measurement, the rule engine, the
gates and tiering are unaffected. One failed LLM call switches it off for two minutes,
so a dead venue network costs one short wait, not one per click.

<details>
<summary>Starting the two servers by hand</summary>

```bash
cd pipeline/backend && uv run uvicorn app.main:app --port 8001     # API docs at /docs
cd pipeline/frontend && pnpm build && pnpm exec next start -H 0.0.0.0 -p 3001
```
</details>

### Where to look first

| Page | What it shows |
|---|---|
| `/troubleshoot` | Open a case — this is the main flow |
| `/troubleshoot/[id]` | The wizard: photo → interview → follow-up → ranking with reasons → troubleshooting loop → report → close |
| `/cases/1` | **CONFIRMED**: size varies → air in the syringe; one purge, re-measured back in spec |
| `/cases/2` | A **T1** diagnosis (a check confirmed carryover; the photo's pattern, p = 0.010, and four agreeing precedents back it too) that still closed **PLAUSIBLE** — the fix wasn't proved, one deposit still missing |
| `/cases/3` | **UNVERIFIED**: closed with nothing proved, and the gap list says so |
| `/cases/4` | Escalated: the operator said the checks don't match what they see |
| `/cases/1/report` | The printable report (Print → Save as PDF) |
| `/` | Line status, proven vs unproven fixes, cases waiting for an engineer |

---

## What it does

The brief's five steps, its dynamic-questions bonus, and all four bonus challenges.

| Brief requirement | Where |
|---|---|
| Step 1 — ~5 smart questions | Five-axis interview, with "Don't know" and "Other (describe)" on every axis |
| Step 1 bonus — dynamic follow-ups | Up to two more questions per case. Each one is chosen because its answer would change the ranking most, and the reason is shown ("would put pressure-time variability at 84%, now 59%") |
| Step 2 — identify the defect | Defect signature + deviation magnitude. Confidence is the tier (T1–T4), stated with its reason and the number of reasons backing the top cause |
| Step 3 — cause analysis | 7 causes from the manual, each reason citing its page |
| Step 4 — troubleshooting score | Likelihood per cause, derived in log-odds, never asserted. "Why 59%?" opens every rule that fired; the *Ranking rules* page lists all 42, and an engineer can change a weight there, with a reason |
| Step 5 — action plan | Ordered checks, observations before changes |
| **Bonus 1** — image recognition | OpenCV metrology: size dispersion, shape, position, missing deposits. The photo is lined up with the recipe first, so a phone photo of the part — zoomed, off-centre, tilted, on a desk — measures |
| **Bonus 2** — quality score | The brief's layout, from the photo: completeness, size consistency, shape consistency and dispensing position, each ★ from a count of deposits ("3 of 15 within 15% of the nominal size"), and an overall score out of 100. It rates the deposits, not the diagnosis |
| **Bonus 3** — learning database | *"Similar problems occurred 12 times previously. In 8 cases, the main cause was air trapped in the syringe or material supply."* — what case 1 shows |
| **Bonus 4** — PDF report | 8-section printable report at `/cases/[id]/report`, including the fix verification |

### Two things that are unusual

**Closing a case is not the same as fixing it.** A case closes **CONFIRMED** only if
all five hold:

1. A check confirmed the cause, and no check confirmed a different one.
2. Exactly one thing was changed, and it was aimed at that cause.
3. The deciding signal was re-measured against a photo taken before the change.
4. The re-measurement is in spec on everything a photo can check: size spread, missing
   deposits, irregular deposits, and the carryover pattern.
5. The fix held for at least 20 shots, as reported by the operator.

Anything less closes **PLAUSIBLE** or **UNVERIFIED**, with the gap named. The
one-change rule is the point: if an operator re-primed the syringe *and* raised the
pressure, the record can't say which one worked, so it isn't allowed to claim either.
That keeps guesswork out of the case database later cases learn from. The fields close
depends on can't be set through the API's generic update; only the step endpoints
write them.

**Precedent can lower confidence, never raise it.** Past cases are counted and shown
to the operator, but the only path from history into the ranking (Gate B) can only
demote a cause that similar confirmed cases contradict. A system that promoted causes
because it had seen them before would grow more confident the longer it ran, whether
or not it was right.

---

## The design bet

Both halves of a dispensing fingerprint are non-text: the operator's answers are
categorical, and the measurements are numeric. So retrieval matches structurally
and by distance rather than by embedding similarity — a similarity score nobody can
explain is worth little in front of an engineer who disagrees with it.

Each cause starts at a prior. Every matching rule adds a weight in **log-odds**,
scaled by how far a measurement sits from its chance or nominal baseline, and the
sum is squashed back to a probability. Every contributing term is shown on the
ranking card, and every rule cites the page it came from in the NPL guide or the NSW
brief.

The LLM gets the jobs it is actually good at, and each is optional, runs at most once
per case and can't move a likelihood:

- mapping an operator's own words onto a fixed option;
- writing the final explanation, with every citation checked against the rules it was
  given;
- acting as a **second opinion that can disagree**. When the rule engine and the
  critic pick different causes, the case is tiered T3/T4 and says so rather than
  hiding the split.

**Known cost of this bet:** the fault tree covers seven causes. A defect outside
those seven is reported as "no cause is ahead" and can be escalated to an engineer,
rather than guessed at. That is the intended failure mode, but it is a real limit.

---

## Testing evidence

```bash
# Backend: close conditions, gates, photo persistence, follow-ups, spec parsing,
# LLM fail-fast — 52 tests, offline, each on a throwaway database
cd pipeline/backend && uv run pytest

# Vision metrology oracle — each synthetic sample encodes a known defect
cd vision && uv run python test_metrology.py          # 27/27 passed

# End-to-end golden cases — fingerprint in, expected cause ranking out
uv run python golden/check_golden.py                  # 2 of 2 passed

# The full pipeline over the real API, with the backend running.
# Exits non-zero unless the case closes CONFIRMED.
cd pipeline/backend && uv run python -m app.seed_demo_case

# The real UI in a browser: one case from photo to CONFIRMED, every step
# waiting for the text it should produce (start the demo first)
uv run --with playwright python scripts/e2e_wizard.py

# Evaluation at scale, through the real vision and ranking code: ~6,600
# synthetic photos and 420 simulated cases, in about a minute
uv run python evaluation/run_eval.py                  # → evaluation/results/summary.md
uv run --with matplotlib python evaluation/plot.py    # → evaluation/results/*.png
```

The evaluation ([evaluation/README.md](evaluation/README.md)) is where the
confidence claims are measured rather than asserted:

- **Calibration:** with three or more reasons behind it, the top cause was right 96% of the time;
  with one, 48%. Every reason is listed under *Why X%?*, so an operator can count them.
- **Accuracy:** the top cause was right 66% of the time with photo and questions and an
  operator whose answers are 75% reliable. That rises to 81% at 100% reliability; chance
  is 14%.
- **Photos:** phone-style photos are measured as well as clean ones (89%), with zero
  false alarms. That covers zoomed 0.6–1.6×, framed up to 300 px off-centre, rotated,
  and lying on a desk with the camera tilted.
- **The remaining weak spot:** busy board backgrounds, with 9% false alarms under light
  clutter. That is the only damage tested that still causes false alarms.

Each fix is recorded as a before/after table in `evaluation/results/`:

- `before_after.md` — the 2026-09-29 vision fixes;
- `before_after_registration.md` — photo registration: framing 0% → 89%;
- `before_after_card_photos.md` — a phone photo of the part on a desk: 0% → 89%.

`seed_demo_case.py` is the API integration test: it opens a case, measures a real
defect photo, saves an interview, ranks, logs one observation and exactly one
change, re-measures with a photo that comes back in spec, and closes. Every step
goes through the endpoints the frontend calls — no direct database writes.

The oracle set is generated by a composable synthetic pipeline
(`vision/synth/`): layouts (5 dispense pattern types) → defect operators (16
classes) → renderer, with each defect applying as an independent mutation to a
shared per-dot spec, so classes compose into mixed-defect images with a per-dot
ground-truth sidecar.

The oracle deliberately includes **cases the system fails**, asserted as failures
rather than hidden — e.g. a contamination speck below the area-noise floor, and a
line-start defect on a single-row layout with no wider row to compare against.

---

## Third-party technologies and sources

All declared per competition rule c.2. **Everything else in this repository is the
team's own work** — specifically the fault tree and its weighted rules, the
two-pass ranking and its gates, the tiering and close-condition logic, the
five-axis intake model and the follow-up selection, the retrieval and precedent
counting, the photo registration, the metrology measurements and signal derivation,
and the synthetic sample generator.

| Component | Used for | Licence |
|---|---|---|
| **NPL Report MATC(A)82**, *A Guide to Best Practice for Electronic Materials Dispensing* (Brewin, Zou & Hunt, National Physical Laboratory, 2001) | The knowledge every rule cites by section and page ("NPL guide §3.5, p.18–19" on screen) | © Crown copyright; extracts reproduced with acknowledgement, as the report permits |
| NSW Automation challenge brief | Rules citing "NSW brief p.N", and the brief's own example questions | Challenge material |
| FastAPI, Uvicorn, Pydantic | Backend API | MIT / BSD |
| SQLAlchemy, Alembic | ORM and migrations | MIT |
| OpenCV (`opencv-python-headless`), NumPy | Deposit measurement and photo registration | Apache-2.0 / BSD |
| Next.js, React | Frontend | MIT |
| Tailwind CSS, shadcn/ui, Base UI, lucide-react, sonner, TanStack Table | UI components and icons | MIT |
| **Groq API** — `openai/gpt-oss-20b` | Critic, free-text mapping and the written explanation (each optional, at most once per case) | Hosted API, Apache-2.0 model |
| pytest, Playwright, matplotlib, qrcode | Tests, the browser check, evaluation charts, the launcher's QR code — development only | MIT / Apache-2.0 / PSF-style / BSD |

No model was trained or fine-tuned for this project. The computer vision is
classical — Otsu thresholding and morphology to find deposits, then a
scale/rotation/shift and perspective fit to line the recipe up with the photo. It
uses **no training data**, and every measurement is reproducible by an engineer with
a microscope.

### Demonstration data

`app/seed_history.py` generates **29 synthetic closed cases** so the learning
database has a past to count. Each family's signals are measured from one of the
project's sample photos through the same `run_vision()` the API uses. These are
**generated demo data, not real production history**, marked in the database with
`rules_version = 'nsw-pack@1-history'`. The retrieval, matching and counting logic
operating on them is real, and is what the bonus-3 claim demonstrates. No real NSW
Automation production data was used; none was provided.

`app/reset_demo.py` builds the four showcase cases differently: it drives the live
API in-process, so their measurements, ranking, check log and close tier are all
produced by the real pipeline rather than written into the database.

---

## Known limitations

Stated up front rather than left to be discovered.

- **Seven causes.** A defect outside the modelled set is reported as unranked, not
  guessed. Stringing, smearing and satellites — the NPL guide puts them down to up
  height (§3.3) — have no cause of their own yet.
- **Measurements are in pixels, not microns.** Absolute volume needs a scale
  reference or known pitch.
- **No real-photo validation set.** NSW provided no production photos and none are
  obtainable open-source, so the vision thresholds are tuned against synthetic
  ground truth only. The stress test measures how far past clean synthetic images the
  measurement holds instead of claiming real-photo accuracy. Its "phone photo on a desk"
  case is simulated from a printed sample. This is the single biggest gap between this
  prototype and a production tool.
- **Registration needs the whole pattern in the photo**, on one plain substrate,
  rotated less than 15°. A deposit cropped out of frame reads as missing. On a
  registered photo, an offset shared by every deposit can't be told apart from
  framing. A photo already framed like the recipe isn't registered, so a pattern
  dispensed off-position still reads as misaligned there.
- **Busy board backgrounds.** Pads and traces the size of a deposit are refused by the
  quality gate, but a trace *touching* a deposit merges into it and can read as an
  irregular shape: 8–9% false alarms under light clutter in the stress test. The
  intended fix is subtracting a bare-board reference photo, standard in automated
  optical inspection.
- **Gate B only engages with similar history.** It needs at least three *confirmed*
  cases on the same material and dispenser whose signals sit within one spread of
  this case's. A case run without a photo has no signals to match on, never reaches
  it, and says so.
- **Holding for 20 shots is the operator's report.** A photo shows one moment; the
  verification records how many deposits it measured next to the operator's shot
  count, and labels which is which.
- **The follow-up answers aren't in the evaluation.** The scenario cards answer the
  five spine questions only, so the follow-up rules are tested by unit tests, not
  measured at scale.
- **The LLM steps are not reproducible.** The critic and the written explanation can
  differ between runs. Both are labelled in the UI, and neither can change a
  likelihood — the critic only affects the confidence tier.
- **Rules are code, not data.** Adding a new manual section currently requires a
  developer. The intended fix is to make rules declarative rows that an LLM can
  *propose* and an engineer approves — keeping the runtime deterministic.

---

## Repository layout

```
pipeline/            ← THE SUBMISSION
  backend/           FastAPI + SQLite. Domain-per-folder:
                     intake · vision · ranking · retrieval · checks · report · cases
    tests/           pytest suite (offline, throwaway database per test)
  frontend/          Next.js wizard, case history, catalog, printable report
vision/              OpenCV metrology package (imported by the backend in-process):
                     segmentation, registration, classification
                     + synthetic sample generator + oracle tests
evaluation/          The at-scale evaluation, its results and before/after tables
golden/              End-to-end fixtures and the cause vocabulary (causes.json)
scripts/             start-demo.sh (launcher) and e2e_wizard.py (browser check)
docs/                The challenge brief, rules, the NPL guide, demo and Q&A notes
DESIGN.md            Design rationale, open questions, and what is still unbuilt
web/                 Earlier exploration: four prototypes across both tracks,
                     testing where reasoning should live (model vs. instrument).
                     Superseded by pipeline/ — kept as development history.
```

`DESIGN.md` is the honest version: it records what is built, what is next, and the
arguments behind each decision — including the ones still unresolved.
