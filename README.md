# AI Dispensing Defect Detective

**AI Horizon Solution Challenge 2026 — Challenge 2, NSW Automation**

An AI troubleshooting assistant for fluid dispensing defects. An operator describes
what went wrong (and photographs it if they can); the system measures the deposits,
interviews them, ranks the possible causes with its reasoning shown, recommends what
to check first, and produces a printable report.

The submission is **`pipeline/`**. Everything else in this repo is the exploration
that led to it — see [Repository layout](#repository-layout).

> **The design bet:** most of this system deliberately does *not* ask a language
> model what the cause is. Percentages come from a weighted fault tree over measured
> evidence, so every number can be traced to the rule and manual section that
> produced it. The LLM is used twice per case — as a second opinion that can
> *disagree*, and to write the final explanation. Why, and what it costs, is in
> [The design bet](#the-design-bet).

---

## Running it

Requires [uv](https://docs.astral.sh/uv/) and Node 20+.

```bash
# 1. Python environment (uv workspace: backend + vision metrology package)
uv sync

# 2. Database: schema, then catalog, then past-case history
cd pipeline/backend
uv run alembic upgrade head
uv run python -m app.seed            # one station, material, profile
uv run python -m app.seed_history    # 24 closed cases, so retrieval has a past
cp .env.example .env                 # optional: add a GROQ_API_KEY

# 3. Backend  → http://localhost:8001  (API docs at /docs)
uv run uvicorn app.main:app --reload --port 8001

# 3b. Optional, with the backend running: drive one case end-to-end to
#     CONFIRMED over the real API. Doubles as an integration test.
uv run python -m app.seed_demo_case

# 4. Frontend → http://localhost:3001   (in a second terminal)
cd pipeline/frontend
npm install
cp .env.local.example .env.local
npm run dev -- --port 3001
```

Open **http://localhost:3001**. Without a `GROQ_API_KEY` everything still runs —
the two LLM-backed steps report "unavailable" on screen and the measurement, rule
engine, gates and tiering are unaffected.

### Where to look first

| Page | What it shows |
|---|---|
| `/troubleshoot` | Open a case — this is the main flow |
| `/troubleshoot/[id]` | The wizard: photo → interview → ranking → troubleshooting loop → report |
| `/cases/4` | A case with past-case history behind it |
| `/cases/4/report` | The printable report (Print → Save as PDF) |
| `/cases` | Case list — compare a **CONFIRMED** close against a **PLAUSIBLE** one |
| `/catalog` | Materials, stations and dispense profiles |

---

## What it does

The brief's five steps, plus all four bonus challenges.

| Brief requirement | Where |
|---|---|
| Step 1 — ~5 smart questions | Five-axis interview, with "Don't know" and "Other (describe)" on every axis |
| Step 2 — identify the defect | Defect signature + deviation magnitude + ★ confidence |
| Step 3 — cause analysis | 7 causes from the manual, each with cited evidence |
| Step 4 — troubleshooting score | Likelihood per cause, derived in log-odds, never asserted |
| Step 5 — action plan | Ordered checks, observations before changes |
| **Bonus 1** — image recognition | OpenCV metrology: size dispersion, shape, position, missing deposits |
| **Bonus 2** — quality score | ★ rating from evidence strength and the #1–#2 gap |
| **Bonus 3** — learning database | *"Similar problems occurred 14 times previously. In 8 cases, the main cause was air trapped in the syringe or material supply."* |
| **Bonus 4** — PDF report | 7-section printable report at `/cases/[id]/report` |

### Two things that are unusual

**Closing a case is not the same as fixing it.** A case closes **CONFIRMED** only if
five things were *proved*: a check confirmed the cause, **exactly one thing was
changed**, the deciding signal was re-measured, it came back in spec, and it held for
at least 20 shots. Anything less closes **PLAUSIBLE** or **UNVERIFIED**, with the gap
named. The one-change rule is the point: if an operator re-primed the syringe *and*
raised the pressure, the record cannot say which one worked, so it is not allowed to
claim either. This is what keeps guesswork out of the case database that later cases
learn from.

**Precedent can lower confidence, never raise it.** Past cases are counted and shown
to the operator, but the only path from history into the ranking (Gate B) can only
demote a cause that past confirmed cases contradict. A system that promoted causes
because it had seen them before would get more confident the longer it ran, whether
or not it was right.

---

## The design bet

Both halves of a dispensing fingerprint are non-text: the operator's answers are
categorical, and the measurements are numeric. So retrieval matches structurally
and by distance rather than by embedding similarity — a similarity score nobody can
explain is worth little in front of an engineer who disagrees with it.

Each cause starts at a prior. Every matching rule adds a weight in **log-odds**,
scaled by how far a measurement sits from its chance or nominal baseline, and the
sum is squashed back to a probability. Every contributing term is inspectable in the
UI, and every rule carries the manual section it came from.

The LLM's two jobs are the ones it is actually good at: mapping an operator's free
text onto a fixed option, and writing the final explanation. It also runs as a
**second opinion that can disagree** — when the rule engine and the critic pick
different causes, the case is tiered T3/T4 and says so rather than hiding the split.

**Known cost of this bet:** the fault tree covers seven causes. A defect outside
those seven is reported as "no cause is ahead" rather than guessed at. That is the
intended failure mode, but it is a real limit.

---

## Testing evidence

```bash
# Vision metrology oracle — each synthetic sample encodes a known defect
cd vision && uv run python test_metrology.py          # 25/25 passed

# End-to-end golden cases — fingerprint in, expected cause ranking out
uv run python golden/check_golden.py                  # 2 of 2 passed

# Full pipeline over the real API, with the backend running.
# Exits non-zero unless the case closes CONFIRMED.
cd pipeline/backend && uv run python -m app.seed_demo_case
```

`seed_demo_case.py` is the integration test: it opens a case, measures a real
defect photo, saves an interview, ranks, logs one observation and exactly one
change, re-measures with a photo that comes back in spec, and closes. Every step
goes through the endpoints the frontend calls — no direct database writes — so a
break anywhere in intake, vision, ranking, the loop or close fails the run.

The oracle set is generated by a composable synthetic pipeline
(`vision/synth/`): layouts (5 dispense pattern types) → defect operators (16
classes) → renderer, with each defect applying as an independent mutation to a
shared per-dot spec, so classes compose into mixed-defect images with a per-dot
ground-truth sidecar.

The oracle deliberately includes **cases the system fails**, asserted as failures
rather than hidden — e.g. a contamination speck below the area-noise floor, and a
line-start defect on a single-row layout with no wider row to compare against.

---

## Third-party technologies

All declared per competition rule c.2. **Everything else in this repository is the
team's own work** — specifically the fault tree and its weighted rules, the
two-pass ranking and its gates, the tiering and close-condition logic, the
five-axis intake model, the retrieval and precedent counting, the metrology
measurements and signal derivation, and the synthetic sample generator.

| Component | Used for | Licence |
|---|---|---|
| FastAPI, Uvicorn, Pydantic | Backend API | MIT / BSD |
| SQLAlchemy, Alembic | ORM and migrations | MIT |
| OpenCV (`opencv-python-headless`), NumPy | Deposit measurement | Apache-2.0 / BSD |
| Next.js, React | Frontend | MIT |
| Tailwind CSS, shadcn/ui, Base UI, lucide-react, sonner | UI components and icons | MIT |
| **Groq API** — `openai/gpt-oss-20b` | Pass-2 critic + free-text mapping (2 calls/case, optional) | Hosted API, Apache-2.0 model |

No model was trained or fine-tuned for this project. The computer vision is
classical (Otsu thresholding, morphology, least-squares lattice fitting) and uses
**no training data** — every measurement is reproducible by an engineer with a
microscope.

### Demonstration data

`app/seed_history.py` generates **24 synthetic closed cases** so the learning
database has a past to count. These are **generated demo data, not real production
history** — they are marked in the database with `rules_version =
'nsw-pack@1-history'`. The retrieval, matching and counting logic operating on them
is real and is what the bonus-3 claim demonstrates. No real NSW Automation
production data was used; none was provided.

`app/seed_demo_case.py` builds one further case, but does it differently: it drives
the live API end to end with the project's own synthetic sample photos, so that
case's measurements, ranking, check log and close tier are all produced by the real
pipeline rather than written into the database.

---

## Known limitations

Stated up front rather than left to be discovered.

- **Seven causes.** A defect outside the modelled set is reported as unranked, not
  guessed.
- **Measurements are in pixels, not microns.** Absolute volume needs a scale
  reference or known pitch.
- **Nominal deposit area is inferred from the median** when no recipe target is
  supplied, which assumes most deposits are in spec.
- **`spread_index` over-reports.** It reads high on images that are not smeared, so
  it can push a false signal into the dispense-height cause. Known, not yet fixed.
- **Gate B only engages once there is history.** It needs at least three past
  *confirmed* cases matching on measured signals, so a case run without a photo —
  which has no signals to match on — never reaches it and says so.
- **No real-photo validation set.** NSW provided no production photos and none are
  obtainable open-source, so the vision thresholds are tuned against synthetic
  ground truth only. This is the single biggest gap between this prototype and a
  production tool.
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
  frontend/          Next.js wizard, case history, catalog, printable report
vision/              OpenCV metrology package (imported by the backend in-process)
                     + synthetic sample generator + oracle tests
golden/              End-to-end fixtures and the cause vocabulary (causes.json)
docs/                The challenge brief and working notes
DESIGN.md            Design rationale, open questions, and what is still unbuilt
web/                 Earlier exploration: four prototypes across both tracks,
                     testing where reasoning should live (model vs. instrument).
                     Superseded by pipeline/ — kept as development history.
```

`DESIGN.md` is the honest version: it records what is built, what is next, and the
arguments behind each decision — including the ones still unresolved.
