# Image prompts — technical brief, portrait

For trying looks before the print version is built. ChatGPT (image generation)
and Gemini render text far better than Midjourney, so start with one of those.

**Settings.** Portrait, A4 proportions: 2:3 in ChatGPT (1024 × 1536), 3:4 or 2:3
in Gemini, `--ar 210:297` in Midjourney.

**Round 1: pick a look.** Generate the cover with each of the four prompts
below, twice each if you can, because results vary a lot between runs.

**Round 2: the inside pages.** In the same chat as the cover you liked, paste
the page 2–6 prompts; they begin "Same style as the cover you just made". Each
also ends with a style fallback, so it works in a new chat too.

Pages 2–4 are a three-page deep dive on the dual-brain ranking, each written
from the code with its real thresholds and a real case. They carry a lot of
small text. Generate them at the highest resolution your tool offers, since
Gemini can output 2K or 4K, and expect to regenerate a few times. Pages 5 and
6 are the feedback loop and the knowledge system.

**Before printing anything generated:** image models misspell small text and
invent numbers. Check every number against the list at the end. The safer
route is to build the chosen look as a print PDF with exact text and the
system's real figures. Those are the annotated phone photo, the 59% build-up,
the dot strips behind p = 0.010 and the calibration chart.

---

## Round 1 — the cover, four looks

### A · Industrial datasheet (matches the slide deck)

```
Design one A4 portrait page (210 × 297 mm): the cover of a printed technical brief for an industrial AI system that diagnoses glue-dispensing defects on electronics assembly lines. Show the page flat, straight-on and edge to edge, as finished print artwork — not a photo of paper on a table.

Layout, top to bottom:
1. Small label: "AI HORIZON 2026 · CHALLENGE 2 · NSW AUTOMATION · TECHNICAL BRIEF"
2. Large title: "AI Dispensing Defect Detective"
3. Subtitle: "From a phone photo to the likely cause, the reasons behind it, and proof the fix worked."
4. Hero image, about a third of the page: a phone photo of a white card lying slightly tilted on a grey desk, with 15 dark round glue dots in 3 rows of 5. Thin rings are drawn over the dots: green on normal dots; red rings labelled "MISSING" on three empty positions, each followed by a much bigger dot with an orange ring labelled "OVERSIZED". Caption beneath: "Carryover pattern found · p = 0.010"
5. Six numbered steps in a row, each with a simple line icon: "1 Photograph", "2 Interview", "3 Rank", "4 Check", "5 Verify", "6 Learn"
6. Four big-number tiles: "96%" — "right when 3+ reasons back it"; "89%" — "phone photos measured correctly"; "66%" — "right even when a quarter of answers are guesses"; "0" — "training data · runs offline"
7. Three small boxes previewing the inside: "① Dual-brain ranking", "② Feedback loop", "③ Knowledge system"
8. Footer in small type: "Knowledge source: NPL Best Practice Guide MATC(A)82 · All test images are synthetic"

Render every quoted text exactly as written, spelled correctly. Add no other words, numbers, logos, people or watermarks.

Style: a premium industrial datasheet. White page, wide margins, a strict grid. Deep solder-mask green #0E3B2E for headings, PCB green #1F7A4D for diagrams and icons, pale green #EEF5F1 for rounded panels, and copper #C8742B used only for the big numbers. Serif headings in the manner of Cambria, a clean sans-serif body in the manner of Calibri. Flat vector diagrams with thin, even strokes; simple line icons in small green circles. Calm, precise, credible. No gradients, no 3D, no clip-art.
```

### B · Engineering blueprint

```
Design one A4 portrait page (210 × 297 mm): the cover of a printed technical brief for an industrial AI system that diagnoses glue-dispensing defects on electronics assembly lines. Show the page flat, straight-on and edge to edge, as finished print artwork — not a photo of paper on a table.

Layout, top to bottom:
1. Small label: "AI HORIZON 2026 · CHALLENGE 2 · NSW AUTOMATION · TECHNICAL BRIEF"
2. Large title: "AI Dispensing Defect Detective"
3. Subtitle: "From a phone photo to the likely cause, the reasons behind it, and proof the fix worked."
4. Hero image, about a third of the page: a phone photo of a white card lying slightly tilted on a grey desk, with 15 dark round glue dots in 3 rows of 5. Thin rings are drawn over the dots: green on normal dots; red rings labelled "MISSING" on three empty positions, each followed by a much bigger dot with an orange ring labelled "OVERSIZED". Caption beneath: "Carryover pattern found · p = 0.010"
5. Six numbered steps in a row, each with a simple line icon: "1 Photograph", "2 Interview", "3 Rank", "4 Check", "5 Verify", "6 Learn"
6. Four big-number tiles: "96%" — "right when 3+ reasons back it"; "89%" — "phone photos measured correctly"; "66%" — "right even when a quarter of answers are guesses"; "0" — "training data · runs offline"
7. Three small boxes previewing the inside: "① Dual-brain ranking", "② Feedback loop", "③ Knowledge system"
8. Footer in small type: "Knowledge source: NPL Best Practice Guide MATC(A)82 · All test images are synthetic"

Render every quoted text exactly as written, spelled correctly. Add no other words, numbers, logos, people or watermarks.

Style: an engineering drawing. Deep blueprint-navy background #0B2545 with a faint square grid, crisp white and pale-cyan linework, dimension arrows and leader-line callouts, labels in a technical monospaced font, and copper-orange #E9B07C only on the big numbers. A drafting title block in the bottom-right corner reading "AI DISPENSING DEFECT DETECTIVE · SHEET 1 OF 6 · REV A". The photo sits in a thin white frame, like a reference image pinned to the drawing. Precise, schematic, memorable from across a room.
```

### C · Scientific journal

```
Design one A4 portrait page (210 × 297 mm): the cover of a printed technical brief for an industrial AI system that diagnoses glue-dispensing defects on electronics assembly lines. Show the page flat, straight-on and edge to edge, as finished print artwork — not a photo of paper on a table.

Layout, top to bottom:
1. Small label: "AI HORIZON 2026 · CHALLENGE 2 · NSW AUTOMATION · TECHNICAL BRIEF"
2. Large title: "AI Dispensing Defect Detective"
3. Subtitle: "From a phone photo to the likely cause, the reasons behind it, and proof the fix worked."
4. Hero image, about a third of the page: a phone photo of a white card lying slightly tilted on a grey desk, with 15 dark round glue dots in 3 rows of 5. Thin rings are drawn over the dots: green on normal dots; red rings labelled "MISSING" on three empty positions, each followed by a much bigger dot with an orange ring labelled "OVERSIZED". Caption beneath: "Carryover pattern found · p = 0.010"
5. Six numbered steps in a row, each with a simple line icon: "1 Photograph", "2 Interview", "3 Rank", "4 Check", "5 Verify", "6 Learn"
6. Four big-number tiles: "96%" — "right when 3+ reasons back it"; "89%" — "phone photos measured correctly"; "66%" — "right even when a quarter of answers are guesses"; "0" — "training data · runs offline"
7. Three small boxes previewing the inside: "① Dual-brain ranking", "② Feedback loop", "③ Knowledge system"
8. Footer in small type: "Knowledge source: NPL Best Practice Guide MATC(A)82 · All test images are synthetic"

Render every quoted text exactly as written, spelled correctly. Add no other words, numbers, logos, people or watermarks.

Style: a page from a leading scientific journal. White paper, an elegant high-contrast serif title, small-caps section labels, a disciplined two-column grid, figure panels labelled a, b, c with thin black axes and hairline frames, captions in small italic. Palette restrained to charcoal, forest green #1F7A4D and one copper accent #C8742B. Generous white space. Authoritative and quiet; no icons in circles, no gradients, no decorative shapes.
```

### D · Bold editorial infographic

```
Design one A4 portrait page (210 × 297 mm): the cover of a printed technical brief for an industrial AI system that diagnoses glue-dispensing defects on electronics assembly lines. Show the page flat, straight-on and edge to edge, as finished print artwork — not a photo of paper on a table.

Layout, top to bottom:
1. Small label: "AI HORIZON 2026 · CHALLENGE 2 · NSW AUTOMATION · TECHNICAL BRIEF"
2. Large title: "AI Dispensing Defect Detective"
3. Subtitle: "From a phone photo to the likely cause, the reasons behind it, and proof the fix worked."
4. Hero image, about a third of the page: a phone photo of a white card lying slightly tilted on a grey desk, with 15 dark round glue dots in 3 rows of 5. Thin rings are drawn over the dots: green on normal dots; red rings labelled "MISSING" on three empty positions, each followed by a much bigger dot with an orange ring labelled "OVERSIZED". Caption beneath: "Carryover pattern found · p = 0.010"
5. Six numbered steps in a row, each with a simple line icon: "1 Photograph", "2 Interview", "3 Rank", "4 Check", "5 Verify", "6 Learn"
6. Four big-number tiles: "96%" — "right when 3+ reasons back it"; "89%" — "phone photos measured correctly"; "66%" — "right even when a quarter of answers are guesses"; "0" — "training data · runs offline"
7. Three small boxes previewing the inside: "① Dual-brain ranking", "② Feedback loop", "③ Knowledge system"
8. Footer in small type: "Knowledge source: NPL Best Practice Guide MATC(A)82 · All test images are synthetic"

Render every quoted text exactly as written, spelled correctly. Add no other words, numbers, logos, people or watermarks.

Style: a bold editorial infographic, like a premium consulting report. Big confident sans-serif headings, oversized numbers, colour-blocked bands in deep green #0E3B2E, mint #9CC9B1 and white, copper #C8742B highlights, rounded cards with soft shadows, line icons in circles, and arrows that lead the eye from top to bottom. Readable in ten seconds from a metre away, yet clearly technical. No stock photos of people, no 3D clip-art.
```

---

## Round 2 — the inside pages

### Page 2 · The dual-brain ranking: how it decides

```
Same style as the cover you just made — same colours, fonts, icons and diagram style. Design page 2 of the brief: one A4 portrait page (210 × 297 mm), flat, straight-on and edge to edge, finished print artwork. If the style has a drawing title block, it reads "SHEET 2 OF 6".

This page explains in detail how the system's dual-brain ranking reaches a decision. It is dense but orderly: clear hierarchy, generous gutters, every label legible.

TOP BAND (about 12% of the page)
- Section heading: "① The dual-brain ranking"
- Intro, two lines: "Two independent readers judge every case, and two gates can only lower its confidence. The output is a ranked list of causes plus an honest label for how sure it is."

MAIN DIAGRAM (about half the page): a left-to-right flowchart in four columns, joined by arrows.
Column 1, headed "INPUTS": five stacked boxes, each with a bold name and a small description.
- "Photo measurements" — "size spread, missing dots, irregular shapes, dispense-order pattern"
- "Five fixed answers" — "what it looks like · how it behaves · what it follows · material state · what helps"
- "Up to 2 follow-up answers" — "asked only if the answer could change the ranking"
- "Check results" — "logged while troubleshooting: confirms or rules out"
- Set apart at the bottom: "Operator's own words" — "the complaint as typed, plus dispenser type and material"
Column 2, headed "THE TWO BRAINS": two large boxes.
- Top: "BRAIN 1 · THE INSTRUMENT" — "A rule engine: 42 rules from the NPL guide and the NSW brief, each citing its section and page. Same input, same answer, every time." The first four inputs point here. Its output arrow is labelled "7 causes, each with its own %, every reason listed".
- Bottom: "BRAIN 2 · THE CRITIC (LLM)" — "A language model that reads only the operator's words, never the measurements or answers, and ranks the 7 causes its own way." Only "Operator's own words" points here. Its output arrow is labelled "its top pick, or abstain".
Column 3, headed "CHECKS ON CONFIDENCE": a diamond and two gate boxes.
- Diamond: "Do the brains agree?" with a small note "an abstaining critic counts as no objection"
- "GATE A · CHANCE" — "Is the deciding measurement more than coincidence? Exact binomial test, p < 0.05"
- "GATE B · PRECEDENT" — "Do proved past cases contradict the lead? Can demote, never promote"
Column 4, headed "THE TIER": four stacked badges, strongest (green) to weakest (grey).
- "T1" — "agree · measurement beats chance · proved precedent agrees → one lead cause, with its evidence and past cases"
- "T2" — "agree · no decisive measurement or no proved precedent → lead cause, marked provisional"
- "T3" — "disagree · measurement beats chance → both candidates, the measurement keeps the top slot"
- "T4" — "disagree · measurement at chance → no lead cause; shows the check that separates them"

BOTTOM LEFT (about 60% of the width): a numbered list titled "One ranking, step by step":
"1  Brain 1 scores all 7 causes from the photo and the answers."
"2  It asks up to 2 follow-ups, choosing those whose answers would move the ranking most."
"3  Brain 2 reads only the operator's words and names a cause, or abstains."
"4  Gate B checks the lead against proved past cases, and may demote it."
"5  Gate A asks whether the deciding measurement beats chance."
"6  Agreement and the gates set the tier. Each logged check re-runs the ranking."

BOTTOM RIGHT: three stacked principle cards, each with a small icon.
- "Agreement never raises confidence" — "two readers can agree on the same mistake, so agreement is not evidence"
- "The critic can object, never add" — "its numbers are never merged into Brain 1's"
- "Every % traces to a page" — "each reason shows its weight and its source"

Render every quoted text exactly as written, spelled correctly. Add no other words, numbers, logos or watermarks. If space is tight, shrink the descriptions rather than dropping them.

Style fallback if there is no cover in this chat: a premium industrial datasheet. White page, deep green #0E3B2E headings, PCB green #1F7A4D diagrams and icons, pale green #EEF5F1 rounded panels, copper #C8742B only for key numbers, serif headings, clean sans-serif body, flat vector diagrams with thin even strokes.
```

### Page 3 · Brain 1, the Instrument: how a percentage is built

```
Same style as the cover you just made — same colours, fonts, icons and diagram style. Design page 3 of the brief: one A4 portrait page (210 × 297 mm), flat, straight-on and edge to edge, finished print artwork. If the style has a drawing title block, it reads "SHEET 3 OF 6".

This page explains in detail how Brain 1 turns evidence into a percentage, using a real case. Dense but orderly; every label legible.

TOP BAND
- Heading: "Brain 1 · The Instrument"
- Subheading: "How a percentage is built, and how it chooses the next question."

PANEL 1, full width, titled "Evidence adds up in log-odds":
- A horizontal ruler with two aligned scales: log-odds "−1.73", "0", "+1.73" on top, and the matching percentages "15%", "50%", "85%" underneath.
- Four short notes beside it:
  "Every cause starts at 15%."
  "Each rule that fires adds its weight: +1 multiplies the odds by 2.7; −0.6 roughly halves them."
  "Measurements count more the further past normal: a size spread of 0.16 barely counts; 0.49 counts in full."
  "Each cause gets its own %, so they don't add up to 100%."

PANEL 2, full width, titled "Why 59%? A real case": two horizontal waterfall charts side by side on the same percentage scale.
- Left, "Air trapped in the syringe": a bar "start 15%"; a step "+1.0 comes and goes · NSW brief p.3" reaching "32%"; a step "+1.1 purging helps · NSW brief p.4" reaching a highlighted total "59%".
- Right, "Pressure-time variability": a bar "start 15%"; one step "+2.1 measured size spread 0.49, limit 0.15 · NPL §2.1 p.6" reaching a highlighted total "59%".
- Between them, a bold tag: "A tie."

PANEL 3, left half, titled "Which question next?":
- One line: "Brain 1 runs every possible answer to every eligible question, and asks the one that could change the lead."
- A small table headed "Does the pressure gauge move while it dispenses?" with three rows:
  "It wanders" → "pressure-time 84% · takes the lead"
  "Steady" → "pressure-time 44% · air leads at 59%"
  "Can't see a gauge" → "adds no evidence"
- A chat bubble, as it appears on screen: "Asked because the answer can change the lead: 'It wanders or dips during a run' would put pressure-time dispensing variability at 84% (now 59%)."
- Small note: "At most 2 follow-ups, and none if no answer would move any cause by 10 points."

PANEL 4, right half, titled "Checks settle it":
- One line: "A check that confirms a cause adds +3.0; one that rules it out adds −3.0."
- A sequence with arrows: "Air 59%" → "Syringe held to the light: air slug seen · confirms" → "97%" → "Line purged, dots even again · confirms" → "99.8%".

FOOTER LINE: "On screen, 'Why 59%?' lists every reason behind a cause, with its weight and page, and the tier says how many back the lead."

Render every quoted text exactly as written, spelled correctly. Add no other words, numbers, logos or watermarks. If space is tight, shrink the notes rather than dropping them.

Style fallback if there is no cover in this chat: a premium industrial datasheet. White page, deep green #0E3B2E headings, PCB green #1F7A4D diagrams and icons, pale green #EEF5F1 rounded panels, copper #C8742B only for key numbers, serif headings, clean sans-serif body, flat vector diagrams with thin even strokes.
```

### Page 4 · Brain 2 and the two gates: how sure it is

```
Same style as the cover you just made — same colours, fonts, icons and diagram style. Design page 4 of the brief: one A4 portrait page (210 × 297 mm), flat, straight-on and edge to edge, finished print artwork. If the style has a drawing title block, it reads "SHEET 4 OF 6".

This page explains in detail how the critic and the two gates decide how sure the system should be. Dense but orderly; every label legible.

TOP BAND
- Heading: "Brain 2 · The Critic, and the two gates"
- Subheading: "How the system decides how sure to be."

PANEL 1, left column, titled "The Critic (an LLM)":
- Two short lists side by side. "Reads": "the operator's own words", "dispenser type", "material". "Never sees": "the measurements", "the five answers", "Brain 1's scores".
- Callout: "Two readers that share their inputs share their mistakes."
- A small bar graphic for the vote rule: "Its top cause must be at least 25% and at least 10 points ahead of its second. Otherwise it abstains."
- Three short notes:
  "Abstaining is not disagreeing."
  "LLM off or offline: treated as abstaining, and the app carries on."
  "Disagreeing can lower the tier to T3 or T4. It can never change a percentage."

PANEL 2, right column, titled "Gate A · Chance":
- One line: "The only photo pattern the NPL guide ties to a single cause is carryover (§3.5): a small or missing dot, then an oversized one."
- Strip (a): a row of 15 dots in dispense order — empty, BIG, normal, normal, normal, normal, empty, BIG, normal, empty, BIG, normal, normal, normal, normal — with a curved arrow from each empty dot to the big dot after it. Caption: "3 of 3 small dots followed by an oversized one. 3 of 14 dots are oversized, so by chance: (3/14)³ ≈ 0.010." Green verdict tag: "Beats chance · carryover rule fires".
- Strip (b): a row of 15 dots — small, normal, normal, BIG, normal, normal, small, normal, small, small, BIG, normal, BIG, normal, normal — with one arrow, from the tenth dot (small) to the eleventh (big). Caption: "1 of 4 small dots followed by an oversized one: p = 0.62." Grey verdict tag: "Coincidence · ignored".
- Note: "A size spread is real, but several causes produce it, so it never counts as deciding."

PANEL 3, left column, titled "Gate B · Precedent":
- "Compares the lead with past cases that closed CONFIRMED: same material and dispenser type, measurements within one spread."
- "Needs at least 3 such cases."
- "More than half caused by something else → the lead is demoted by up to 0.4 log-odds."
- "All agree → nothing is added; agreement only unlocks T1."
- Pull quote: "If history could promote a cause, the system would grow more certain of whatever it diagnosed first."

PANEL 4, right column, titled "Setting the tier": a decision tree.
- Start: "Did a check on this case confirm the lead?" → Yes: "T1 · one lead cause". No → "Do the brains agree?"
- Yes → "Measurement beats chance, and at least 3 proved cases, none contradicting?" → Yes: "T1 · one lead cause"; No: "T2 · lead cause, provisional".
- No → "Measurement beats chance?" → Yes: "T3 · both candidates, measurement on top"; No: "T4 · no lead: run the check that separates them".

BOTTOM BAND, titled "Is the confidence honest?":
- A bar chart of four bars labelled "1 reason", "2", "3", "4+" with values "48%", "72%", "95%", "100%"; axis caption "top cause correct, by reasons backing it".
- Beside it: "In every confidence band it is right at least as often as the % it shows." And in small grey type: "Simulated cases, photo + answers · chance 14% · measured on Brain 1 and the reasons behind its lead; the critic and gates were not part of this test."

Render every quoted text exactly as written, spelled correctly. Add no other words, numbers, logos or watermarks. If space is tight, shrink the notes rather than dropping them.

Style fallback if there is no cover in this chat: a premium industrial datasheet. White page, deep green #0E3B2E headings, PCB green #1F7A4D diagrams and icons, pale green #EEF5F1 rounded panels, copper #C8742B only for key numbers, serif headings, clean sans-serif body, flat vector diagrams with thin even strokes.
```

### Page 5 · The feedback loop

```
Same style as the cover you just made — same colours, fonts and diagram style. Design page 5 of the brief: one A4 portrait page (210 × 297 mm), flat, straight-on and edge to edge, finished print artwork. If the style has a drawing title block, it reads "SHEET 5 OF 6".

Layout, top to bottom:
1. Section heading: "② The feedback loop"
2. Intro line: "Closing a case is not the same as fixing it."
3. A circular loop diagram with five stations joined by arrows: "Rank" → "Check: look first" → "Change one thing" → "Verify with a fresh photo" → "Close", and an arc from "Close" back to "Rank" labelled "Learn".
4. A before/after panel: two small photos of a white card with 15 dark glue dots in 3 rows of 5. Left, uneven dot sizes, labelled "Before · size spread 0.49". Right, even dots, labelled "After · 0.05 · in spec". Beneath them, four green ticks: "Spread ≤ 0.15", "0 missing", "0 irregular", "No carryover pattern".
5. A checklist titled "Five things must be proved": "A check confirmed the cause", "Exactly one change, aimed at it", "Re-measured against a before photo", "Back in spec on every check", "Held for 20+ shots".
6. Three outcome badges in a row: green "CONFIRMED · all five · teaches future cases", amber "PLAUSIBLE · some · context only", grey "UNVERIFIED · none · gaps named".
7. A large pull quote: "Three changes at once? Then nobody can say which one worked."
8. Short paragraphs of body text drawn as neat grey placeholder lines.

Render every quoted text exactly as written. Add no other words, numbers, logos or watermarks.

Style fallback if there is no cover in this chat: a premium industrial datasheet. White page, deep green #0E3B2E headings, PCB green #1F7A4D diagrams and icons, pale green #EEF5F1 rounded panels, copper #C8742B only for key numbers, serif headings, clean sans-serif body, flat vector diagrams with thin even strokes.
```

### Page 6 · The knowledge system

```
Same style as the cover you just made — same colours, fonts and diagram style. Design page 6 of the brief: one A4 portrait page (210 × 297 mm), flat, straight-on and edge to edge, finished print artwork. If the style has a drawing title block, it reads "SHEET 6 OF 6".

Layout, top to bottom:
1. Section heading: "③ The knowledge system"
2. Intro line: "What it knows from the manual, and what it remembers from proved fixes."
3. A two-column diagram:
   • Left, titled "FROM THE MANUAL": a book icon labelled "NPL Best Practice Guide MATC(A)82", with an arrow to a card "7 causes · 42 rules · every rule cites its section and page".
   • Right, titled "FROM PAST CASES": a database icon labelled "Case history", splitting into two arrows. One leads to a speech-bubble card: "Similar problems occurred 12 times previously. In 8 cases, the main cause was air trapped in the syringe or material supply." tagged "shown to people · never moves the ranking". The other leads to a shield icon: "Precedent gate · CONFIRMED cases only · can only lower confidence".
   • Only the manual card and the shield send arrows down into a box labelled "Ranking"; the speech bubble has no arrow onward.
4. A band titled "No embeddings, no model training — every match can be explained", with short placeholder text.
5. A bottom strip titled "Evidence" with three stat tiles: "66% vs 54%" — "top cause right: photo + answers vs answers alone"; "96%" — "right when 3+ reasons back it"; "0%" — "false alarms on phone photos". Under it, in small grey type: "All test images are synthetic · next step: validate on real NSW photos".
6. Short paragraphs of body text drawn as neat grey placeholder lines.

Render every quoted text exactly as written. Add no other words, numbers, logos or watermarks.

Style fallback if there is no cover in this chat: a premium industrial datasheet. White page, deep green #0E3B2E headings, PCB green #1F7A4D diagrams and icons, pale green #EEF5F1 rounded panels, copper #C8742B only for key numbers, serif headings, clean sans-serif body, flat vector diagrams with thin even strokes.
```

---

## Optional — text-free hero images

For the cover, a banner or slide 1. Caption these "Illustration" wherever they
appear: a generated circuit board must never be mistaken for the system's
measured output.

```
Macro product photograph, portrait orientation, shallow depth of field: a fine stainless-steel dispensing needle just above a green circuit board, laying down a neat row of glossy dark epoxy dots. One position in the row is empty and the dot right after it is noticeably oversized. Cool white studio light with a warm copper rim light, deep green out-of-focus background. Photoreal and crisp. No text, no logos, no people.
```

```
Minimal conceptual illustration, portrait orientation: two glowing outlines of a human head in profile facing each other — one filled with precise circuit-board traces and small gauges, the other with soft overlapping speech bubbles — and between them a small balance scale. Dark solder-mask green background #0E3B2E, fine copper #C8742B and mint #9CC9B1 linework, lots of empty space. Elegant, no text, no logos.
```

---

## Numbers to check before printing

Every figure below comes from the code or `evaluation/results/summary.md`
(run of 2026-10-02).

- **Log-odds scale**: −1.73 = 15%, 0 = 50%, +1.73 = 85%. A weight of +1
  multiplies the odds by 2.7; −0.6 multiplies them by 0.55.
- **59%**: air trapped in the syringe. It goes 15% → **32%** after "comes and
  goes" (+1.0, brief p.3), then → 59% after "purging helps" (+1.1, brief p.4).
- **Also 59%**: pressure-time variability, from 15% plus +2.1 for the
  measured size spread of 0.49 against a 0.15 limit (NPL §2.1 p.6). The
  follow-up question breaks that tie.
- **Size-spread weight**: 0.16 adds 0.07 ("barely counts"); 0.49 adds the full
  2.1.
- **Pressure gauge answers**: "wanders" puts pressure-time at **84%**;
  "steady" puts it at **44%**, leaving air leading at 59%.
- **Follow-ups**: at most 2, and only if some answer would move a cause by at
  least 10 points.
- **Checks**: a confirming check adds +3.0 and ruling out adds −3.0. Air goes
  59% → **97%** → **99.8%** after two confirming checks.
- **Critic vote**: its top cause must be at least 25% and at least 10 points
  ahead of its second; otherwise it abstains.
- **p = 0.010**: carryover, where all 3 small dots are each followed by an
  oversized one; 3 of 14 dots are oversized, and (3/14)³ = 0.0098. The rule
  then adds about +4.0.
- **p = 0.62**: 1 of 4 small dots is followed by an oversized one, so it is
  treated as noise.
- **Honesty claim**: in every band of shown percentage (0–40, 40–55, 55–70,
  70–85, 85–100), the share actually right is at least the mean shown: 46 vs
  35, 60 vs 49, 63 vs 62, 76 vs 76, 98 vs 91.
- **1 reason 48% · 2 reasons 72% · 3 reasons 95% · 4+ reasons 100%** (three or
  more together: 96%): how often the top cause is right, by the reasons backing it.
- **66% vs 54%**: photo + answers vs answers alone, when a quarter of the
  answers are guesses. With perfect answers it is 80.5% vs 71.4%. Chance is
  14% (1 in 7).
- **89%**: phone-style photos measured correctly, with **0%** false alarms. This
  covers zoomed, off-centre, handheld, on a desk and tilted photos.
- **7 causes, 42 rules**: each rule cites a section and page of NPL
  MATC(A)82 or the NSW brief.
- **Gate A**: p < 0.05.
- **Gate B**: needs at least 3 matching CONFIRMED cases, lowers the lead by at
  most 0.4 log-odds, and never raises it.
- **Verification**: size spread ≤ 0.15, 0 missing, 0 irregular, no carryover
  pattern, held for at least 20 shots.
- **Example fix**: size spread 0.49 → 0.05.
- **Precedent sentence**: "Similar problems occurred 12 times previously. In 8
  cases, the main cause was air trapped in the syringe or material supply."
- **No real-photo accuracy is claimed.** Every test image is synthetic.
