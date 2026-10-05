# Q&A bank — likely judge questions, short answers

Three minutes of Q&A goes fast: answer in one or two sentences, then stop. Each answer
names the backup slide (8–14) or the screen that shows it. The judges are industry
people from NSW Automation, so lead with what it does on a line, then how.

---


```mermaid
flowchart TD
    A["Open case: complaint + profile"] --> B["Upload defect photo"]
    B --> C["Vision measures signals: size_cv, missing, carryover"]
    C --> D{"Quality gate ok?"}
    D -- No --> D1["Reject: retake photo"]
    D -- Yes --> E["Save 5 fixed interview answers"]
    E --> F["Pass 1: rule engine ranks 7 causes"]
    F --> G["Pass 2: critic LLM votes or abstains"]
    G --> H["Gate B: check precedent"]
    H --> I["Gate A: check chance"]
    I --> J["Compute tier T1-T4"]
    J --> K["Ask up to 2 follow-ups if useful"]
    K --> L["Log observation check: confirms cause"]
    L --> M["Log the one allowed change"]
    M --> N["Re-rank after change"]
    N --> O["Upload verify photo, hold N shots"]
    O --> P{"Back in spec?"}
    P -- No --> P1["Cannot close CONFIRMED"]
    P -- Yes --> Q["Add engineer notes"]
    Q --> R["Close case"]
    R --> S{"Verdict == CONFIRMED?"}
    S -- Yes --> T["CONFIRMED: report + evidence"]
    S -- No --> P1
```

**1. Why not just ask ChatGPT, or a vision model, what's wrong?**
Because an engineer can't argue with a number nobody can trace. Every percentage here is
built from cited rules (*Why 59%?*). We also benchmarked small local vision-language
models on our defect images: 13.6%, every real defect missed. The LLM is used where it's
good — a second opinion, mapping free text, writing the summary — and can never set a
likelihood.

**2. Where do the weights come from? Did you fit them?**
From the NPL Best Practice Guide's sections and the NSW brief, with team judgement on
size. They were deliberately *not* fitted, because fitting to synthetic data would just
learn the generator. We measure calibration instead: with three or more reasons behind the top cause it's
right 96% of the time, with one reason 48% (slide 8).

**3. You have no real photos. How do you know the vision works?**
We don't claim real-photo accuracy, and say so on the slides. What we measured:
- 6,600 synthetic photos, damaged the way cameras damage them;
- framing, tilt and a desk in the shot measure as well as clean photos;
- glare and heavy clutter are refused rather than misread (slide 13).

Validating on 50–100 real NSW photos is step one of the pilot.

**4. What if the cause isn't one of your seven?**
It says "no cause is ahead" instead of guessing, and the operator can escalate to an
engineer; the home page lists cases waiting for one. Stringing and smearing (up height, NPL §3.3) is the next cause we'd add (slide 6).

**5. Isn't the "learning database" just counting?**
The count is descriptive on purpose. What makes it trustworthy is what gets *in*: only
cases where one change was made and the fix was re-measured close CONFIRMED. History can
lower confidence in a cause past cases contradict, never raise it, so it can't grow
overconfident by repetition (slides 10 and 11).

**6. What if the LLM hallucinates, or there's no internet?**
It can't change a likelihood, and every source it cites is checked against the rules it
was given; if not, the code-written explanation is shown instead. Without internet, one
failed call switches it off for two minutes. The whole system runs fully offline, and we
can demo it that way.

**7. How would NSW deploy it? What does it need?**
A line PC or a laptop. No GPU, no training data, no cloud required. Operators use any
browser, including a phone on the line's Wi-Fi. Data stays in one database file on site.
Next steps would be a recipe import from the dispenser program and a hook to open cases
from SPC alarms.

**8. What if the operator answers badly?**
The evaluation simulates exactly that. With half the answers random, the photo still
keeps it at 57% versus 40% without (slide 12). "Don't know" is always allowed and adds
no evidence, instead of a guess entering as fact.

**9. Isn't this just a 1990s expert system?**
The rule core, yes — on purpose, because it's auditable. What's new around it:
- the photo is measured and lined up with the recipe automatically;
- follow-ups are chosen by how much each answer would move the ranking;
- a chance test stops it reading patterns into noise;
- a critic can veto, and confidence is measured against outcomes;
- the case history only learns from proved fixes.

**10. Can an operator just mark a case as fixed?**
No. The verdict is computed from the check log and the re-measurement, and the
API refuses direct edits to it. Three changes at once, or a change aimed at a different
cause than the one confirmed, can't close CONFIRMED.

**11. Your accuracy numbers come from your own scenario cards — isn't that circular?**
Partly, and the evaluation README says so. The cards were written from the manual, not
from the rules, and include answers no rule rewards; the numbers test consistency with our
reading of the manual. The measurement and stress results aren't circular: their truth
comes from the image generator. An NSW engineer reviewing the cards would make the
diagnosis numbers much stronger.

**12. Can it predict defects before they happen?**
Not yet. The pieces are there, though: every case stores measured size spread with a
timestamp, so a line's spread can be trended and a case opened before it leaves spec.
That's on the pilot plan (slide 14).

**13. What does "p = 0.010" mean on the carryover case?**
The chance of seeing that many small-then-big pairs if oversized dots fell at random.
Below 0.05 we treat the pattern as real; at 0.62, as in another sample, it's noise, and
the system says so.

**14. How is this different from automated optical inspection (AOI)?**
AOI says *what* is wrong with a board. This says *why*, what to check first, and whether
the fix worked. It could take an AOI result as its photo input.

**15. What about other materials and patterns — lines, underfill, silicone?**
Profiles carry the recipe's geometry. Dots, grids, perimeters and custom patterns are
supported, and material and dispenser type are case metadata. Lines measure, but
start/end defects on a single row are a known gap. The causes come from the NPL guide's
dot-dispensing sections.

**16. What would you do with another month?**
Real photos from NSW, a bare-board reference to remove clutter false alarms, rules as data that engineers approve, and the up-height cause.

**17. Who did what? / Is this your own work?**
Slide 5 separates our work from what we used, as rule c.2 asks. Have each team member name the part they can explain in depth — the briefing asks that every member understands the solution.

**18. Every rule belongs to one cause — isn't that rigid?**
Less than it looks. One answer can move several causes up or down: "it has always been like this" raises board bending and lowers blockage and wear. A rule can also read combinations,such as missing dots *without* the carryover pattern. The real limit is that we set the weights from the manual. Next, the rules become a table NSW engineers can edit. Once there are enough proved cases, the weights get fitted from them in the same structure, so every % still shows its reasons.

**19. Air is confirmed — why does pressure-time still show a high %?**
Each % is per cause, as in the brief's own table, because two faults can happen together.
Confirming air doesn't prove the pressure is stable. The fresh photo does: size spread back
from 0.49 to 0.05.

**20. Junior and senior use the same app and the same workflow — so what does the senior actually add?**
There are no logins or roles, on purpose: a line tool that gates screens behind accounts
gets one shared login by Friday. What differs is what the case asks of each person.
- **The tool solves a different problem for each.** For the junior it supplies the
  knowledge they don't have yet — ranked causes, the reasons behind each, and the check to
  run first. For the senior it supplies the record-keeping they'd otherwise skip: the
  measurement, the one-change rule, the verification photo.
- **Handover without losing the trail.** *Ask an engineer* captures the operator's question
  in their own words and puts the case on the home page under *Needs review*, oldest first.
  The senior arrives with the photo, the measurements, the five answers, the ranking and
  every check already logged — instead of "it's doing something weird on line 3".
- **The senior's judgement becomes part of the record.** Engineer notes and *Mark reviewed*
  are written in the case, shown to the operator next time they open it, and printed in the
  report. Today that knowledge is spoken and lost.
- **Only the senior changes the system.** On the *Ranking rules* page they can change any of
  the 42 weights, and the change **requires a written reason**, is stored with a timestamp,
  and applies to every future case. That is the one path where a senior's experience gets
  into the tree instead of staying in their head.

A senior also reaches a confident answer faster through the same screens: a check that
confirms the top cause takes the case to T1 in one step. The junior gets the same plan laid
out — *Step 1, look; Step 2, change* — and takes longer. That is the intended difference.

**21. Only 7 causes and 42 rules. What about an 8th cause, or a combination no rule covers?**
Two different questions, and the honest answers differ.

**A cause outside the seven.** Nothing fires, so all seven stay on the same starting odds —
and the system detects exactly that rather than ranking whichever cause the list happens to
show first. It says so in words: *"nothing you told me, and nothing in the photo, matches
any of the rules in the tree… that usually means the defect is real but outside what this
tree models"*, then suggests a check and says it's worth telling an engineer. It never
invents a cause. The evaluation excludes these from accuracy, because "no cause is ahead"
makes no claim to be right or wrong. The LLM critic is the second net: it reads the same
evidence without the tree's vocabulary and can disagree, which drops the tier.

**A combination outside the 42 rules.** This one is a misunderstanding worth correcting
politely: the 42 are not a lookup table of combinations. Each rule is **independent and
additive** — one answer can move several causes at once, and the log-odds sum handles any
combination of the rules that fire. So there is no "unmatched combination"; there is only
*fewer reasons fired*, which shows on screen as a lower tier and a smaller reason count.
That is precisely what the calibration measures: one reason behind the top cause means 48%
right, three or more means 96%. A thin combination is visible as thin, not disguised as
confident.

**Adding the 8th cause today is a code change** — rules are code, not data, and we list that
as a limitation (slide 6). The structure to fix it is already there: the 42 rules are one
table, each with a weight and a manual citation, and an engineer can already edit a weight
with a reason. Making the rows themselves editable, with an LLM *proposing* and an engineer
approving, is the next step — the runtime stays deterministic either way.
