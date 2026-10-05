# Final pitch — 3-minute script

Seven slides, then straight into the live demo. Target **2 min 50 s**, leaving a
few seconds of slack. Times are speaking time; the `~` figures are also in the
PowerPoint speaker notes.

Delivery notes: the **bold** phrases are the ones to land. Everything in
brackets is a stage direction, not speech. If you are running long, the two
safest cuts are marked `[CUT IF LONG]`.

---

## 1 · Title — Team Lithium (~18 s)

> Good morning. We're **Team Lithium**, three of us from **Universiti Sains
> Malaysia**, and we took NSW Automation's challenge for advanced level and all 4 bonus challenges.

---

## 2 · The problem (~26 s)

> When dots come out wrong, an experienced engineer knows where to look. A new
> technician doesn't — **inconsistent size alone has five plausible causes**, and
> a wrong guess can mean stripping a valve for a whole shift.
>
> So people change three things at once. The defect goes away, and **nobody can
> say which change fixed it**. The next case starts from zero.
>
> Meanwhile what the senior engineer knows is written down nowhere the next case
> can reach. And a confidence score an engineer can't check is a score they'll
> ignore.

---

## 3 · The solution (~42 s)

> So here's what actually happens. The operator just takes a photo of the
> deposits — doesn't matter how it's framed — answers five questions, and maybe
> one or two follow-ups. And here's the thing: **we don't ask random follow-ups**.
> The system only asks the question that would actually change its mind.
>
> From that, it ranks seven possible causes, and — this is important — **every
> percentage comes with a reason you can actually read**. Not a black box. The
> operator checks the top one first, changes one thing, and watches the ranking
> update live. Then a fresh photo proves whether it actually worked.
>
> So what does that mean in practice? A new technician's first move is already
> **ranked and explained** — not a guess. Every case ends with a report you could
> hand to an auditor. And the history only remembers fixes that were **actually
> proven** — not ones someone just assumed worked. All of this, by the way, runs
> **offline**, on a line PC. A phone camera is all you need.

---

## 4 · The AI (~50 s)

> Three parts make that work.
>
> A **knowledge database** — seven causes and forty-two weighted rules, every one
> citing NPL's Best Practice Guide by section and page.
>
> A **dual-brain ranking system**. Pass one is a deterministic rule engine: it
> does the arithmetic in log-odds and sets every percentage. Pass two is an LLM
> critic that reads the same evidence and **can disagree**. When they disagree we
> drop the confidence tier and say so, instead of hiding the split. The language
> model never sets a number.
>
> And a **senior-engineer feedback loop** — the operator escalates, the senior
> answers inside the case, and can change a rule's weight, with a reason.
>
> We measured this rather than asserting it. With **three or more reasons behind
> it, the top cause is right 96% of the time**; with one reason, 48 — a coin flip.
> And precedent can only *lower* confidence, never raise it, so the system can't
> talk itself into being right.

---

## 5 · What we used (~16 s)

> Declared under rule c.2. The knowledge is **NPL Report MATC(A)82**, Crown
> copyright, cited on screen wherever it's used. **Groq** runs the optional LLM.
> FastAPI, Next.js, OpenCV.
>
> Everything else is ours — the fault tree, the two-pass ranking, the gates, the
> close rule, the photo registration, the metrology. **No model was trained or
> fine-tuned**, and the vision uses no training data at all.

---

## 6 · Limitations (~22 s)

> What it doesn't do.
>
> NSW had no production photos to give us, so **every threshold is tuned on
> synthetic images** — validating on real ones is step one of a pilot. That's our
> biggest gap, and we'd rather say it than have you find it.
>
> Seven causes: anything outside them is reported as "no cause ahead" and
> escalated, **not guessed**. On a busy board, a trace touching a deposit can
> still read as a bad shape. `[CUT IF LONG]` And measurements are in pixels, not
> microns — absolute volume needs a scale reference. `[CUT IF LONG]`

---

## 7 · Close → demo (~8 s)

> That's the system. Let me show you one case, from a phone photo to a confirmed
> fix.

[Switch to the browser. Do not read the closing slide aloud.]

---

## If a judge interrupts

Backup slides are in the same deck, after slide 7, in this order:

| Ask | Slide |
|---|---|
| "How accurate is it?" | B1 — calibration chart and the 66% / 14% numbers |
| "Does it work on a real photo?" | B2 — phone photo, 0% → 89% after registration |
| "How do you know a fix worked?" | B3 — the five close conditions |
| "How is confidence decided?" / "What if the AI disagrees?" | B4 — the four tiers, Gate A and Gate B |
| "What if the operator answers badly?" | B5 — photo vs questions-only at three reliability levels |
| "What if the photo is bad?" | B6 — the stress test; it refuses rather than misleads |
| "Could NSW actually deploy this?" | B7 — value on day one and the four-step pilot plan |

Fuller answers are in [qa-bank.md](qa-bank.md); the demo steps are in
[demo-runbook.md](demo-runbook.md).
