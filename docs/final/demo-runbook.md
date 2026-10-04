# Demo runbook — AI Horizon final, Tuesday 6 October 2026

Format (briefing deck): **10 minutes per team — 3 min presentation, 2 min live demo,
3 min Q&A, 2 min judges scoring.** Judging 9:00–12:00 and 13:00–14:30, booth set-up
from 8:00. The rules PDF says 7 October; the briefing deck says Tuesday 6 October —
confirm on the WhatsApp group.

Slides: `docs/final/AI-Dispensing-Defect-Detective.pptx`. The first 8 slides are the
3-minute pitch, with timed speaker notes; slides 9–13 are backup for Q&A. The PDF next
to it is the offline backup.

---

## The night before

1. `git pull` (or copy the repo) onto the demo laptop, then from the repo root:
   `uv sync`, `cd pipeline/frontend && pnpm install --frozen-lockfile && pnpm build`.
2. `scripts/start-demo.sh --reset` — rebuilds the demo database (cases 1–4 + history)
   and starts everything. Open http://localhost:3001 and click through once.
3. Run the browser check: `uv run --with playwright python scripts/e2e_wizard.py`
   (set `CHROMIUM_PATH` if Playwright's own browser isn't installed). It should end
   `OK — case #N driven through the UI to CONFIRMED`. Then reset again so the
   database is clean: `scripts/reset-demo.sh` (no need to stop the demo).
4. **Phone test.** Turn on your phone's hotspot and join it with the laptop, start
   the demo, and scan the QR code the launcher prints. Take a photo of a printed sample
   card (step 6) and check it measures.
5. Decide the LLM. With the hotspot's data, the critic gives a second opinion on screen
   and the report gets a written explanation. If the data is unreliable, run
   `LLM_ENABLED=false scripts/start-demo.sh`; everything else is identical.
6. Print sample cards: `vision/samples/inconsistent.png`, `missing_carryover.png`,
   `ghost.png`, `good.png`, each on its own A5 or A4 sheet, white paper, no scaling
   fuss — registration handles size. They are props for the booth, and the input for
   the phone moment.
7. Record the backup video of the 2-minute path below (screen recording), and put it
   with the PDF deck on a USB stick. The deck says to bring an offline demo.
8. Charge the laptop and phone; pack the charger, an extension cord and an HDMI adapter.

## At the booth (8:00–9:00)

- Power in, launcher running in a terminal: `scripts/start-demo.sh`. If the database
  gets messy, run `scripts/reset-demo.sh` in a second terminal. It takes a few seconds,
  the demo keeps running, and the next page load shows cases 1–4 fresh.
- Browser tabs, in this order: **home** (`/`), a **new case already opened at the photo
  step** (open `/troubleshoot`, pick *Line 3 Dispenser* and *Standard Dot · 15-point
  grid*, Open case), **`/cases/1/report`**, **`/cases/2`**.
- Zoom the browser to 110–125% so the judges can read it across the table.
- Slides in presenter view on the same laptop, or on a second screen if there is one.
- Between judging slots, open a fresh case for the next team of judges, so every demo
  starts at the photo step.
- **Ranking rules** (button at the top right of the home page) is the answer to "how
  does it rank?" and "where do the weights come from?". The *List* shows all 42 rules
  with their pages. On the *Map* tab, click *Load the demo case*: air and pressure-time
  tie at 59%. Hover the two answers under *Follow-up · Pressure gauge* to show how each
  would break the tie, then click the *Air in syringe* column to show how its 59% is built.
- If a judge edits a weight to try it, *Restore all* on the List tab puts every rule
  back to the manual's (so does `scripts/reset-demo.sh`). An edited weight changes the live demo's
  numbers, so check for the "edited" count before the next slot.

## The 2-minute demo — clicks and lines

Start on the pre-opened case at the photo step. Talk while it works; don't wait on it.

| Time | Do | Say |
|---|---|---|
| 0:00 | Attach `inconsistent.png` — or photograph the printed card with the phone | "A photo of the deposits. It lines the recipe up with the picture and measures every dot." |
| 0:10 | Signature is pre-ticked **Size varies** → *That's right* | "The photo already answered question one; I just confirm it." |
| 0:15 | *Random* → *The material* → *New lot or syringe* → *Confirm* → *Purging or priming* | "Five questions an operator can answer — 'Don't know' is always allowed." |
| 0:35 | The follow-up appears — point at "Asked because…" → *Steady at the set value* | "Air and pressure-time were tied at 59%. It simulated every answer and asked the one that could break the tie." |
| 0:42 | A second follow-up, "Where on the board…" → *Everywhere, about the same* | Keep talking; this answer leaves air at 59%. |
| 0:45 | Ranking appears — point at the chat line, then **Why 59%?** on the right | "Air leads because the problem comes and goes and purging helps — each reason with its weight and its page in the NPL guide." |
| 1:05 | *Log a check* → **Air trapped…** → *Hold the syringe up to the light* → *Confirms it* → *Log it* | "Look first — it costs nothing. It re-ranks instantly." |
| 1:20 | *Log a check* → **Air trapped…** → *Purge the line, or swap in a fresh syringe* → *Confirms it* → *Log it* | "Now exactly one change — that's what lets it claim the fix." |
| 1:30 | *Continue to report* → attach `good.png` → *50 or more* | "A fresh photo: back in spec on everything it can check." |
| 1:40 | *Close the case* | "CONFIRMED — and only cases like this teach the next one." |
| 1:50 | Switch to the `/cases/1/report` tab | "And a printable report with the sources and the verification." |

Running long? Skip the second check and go straight to the `/cases/2` tab. It shows a
T1 diagnosis next to a fix that wasn't proved — the "closing isn't fixing" point in one
screen.

## If something goes wrong

| Symptom | Do |
|---|---|
| Photo refused ("couldn't measure") | Say "it refuses rather than guess" — then attach the sample file instead. Refusing is the designed safe failure. |
| With the LLM on, the critic disagrees and the tier drops to T3/T4 | Rehearse this case with the LLM on so it isn't a surprise. If it happens: "a second, independent read disagrees — so instead of guessing it names the check that separates them." That *is* the design; carry on with the checks. |
| Venue Wi-Fi dies mid-demo | Nothing to do: one failed LLM call turns it off for two minutes and the code-written explanation shows. Next slot: `LLM_ENABLED=false`. |
| The page shows "Could not reach the API" | The backend stopped: Ctrl+C the launcher and run `scripts/start-demo.sh` again (~5 s). |
| The laptop is unusable | Backup video + the PDF deck from the USB stick. The rules require a *live* demo, so say what failed and show the video only as a last resort. |

## The phone moment (booth, between judging slots)

Hand a visitor a printed card and your phone with the app open (QR code from the
launcher). They take the photo, the app measures it, and the annotated image shows
the rings sitting on their deposits. With `missing_carryover` printed, the system
finds three missing dots each followed by an oversized one and names the carryover
pattern. Say plainly that the cards are printed synthetic samples — real-photo
validation is the pilot's first step.

## Poster / banner (A2) — what to put on it

The briefing says posters support the solution and aren't scored separately, so make
the poster do the talking while you demo:

1. **Hero image:** `docs/final/deck/assets/phone_annotated_slide.png` — a phone photo,
   rings and labels on every deposit.
2. **One line:** "A phone photo and five questions → the likely cause, why, and what to
   check first."
3. **The six steps** from slide 3: Photograph → Interview → Rank → Check → Verify → Learn.
4. **One number with its chart:** "When it says ★★★, it's right 95% of the time"
   (slide 5).
5. **The trust idea:** CONFIRMED / PLAUSIBLE / UNVERIFIED — closing isn't fixing.
6. **Credit line:** knowledge from the NPL Best Practice Guide MATC(A)82
   (© Crown copyright); no model trained, no training data.
