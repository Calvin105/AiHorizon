# Image prompts — technical brief, portrait

For trying looks before the print version is built. ChatGPT (image generation)
and Gemini render text far better than Midjourney, so start with one of those.

**Settings.** Portrait, A4 proportions: 2:3 in ChatGPT (1024 × 1536), 3:4 or 2:3
in Gemini, `--ar 210:297` in Midjourney.

**Round 1: pick a look.** Generate the cover with each of the four prompts
below, twice each if you can, because results vary a lot between runs.

**Round 2: the inside pages.** In the same chat as the cover you liked, paste
the page 2, 3 and 4 prompts; they begin "Same style as the cover you just made".
In a new chat, swap that opening for the cover's `Style:` paragraph.

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
6. Four big-number tiles: "95%" — "right when it shows ★★★"; "89%" — "phone photos measured correctly"; "66%" — "right even when a quarter of answers are guesses"; "0" — "training data · runs offline"
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
6. Four big-number tiles: "95%" — "right when it shows ★★★"; "89%" — "phone photos measured correctly"; "66%" — "right even when a quarter of answers are guesses"; "0" — "training data · runs offline"
7. Three small boxes previewing the inside: "① Dual-brain ranking", "② Feedback loop", "③ Knowledge system"
8. Footer in small type: "Knowledge source: NPL Best Practice Guide MATC(A)82 · All test images are synthetic"

Render every quoted text exactly as written, spelled correctly. Add no other words, numbers, logos, people or watermarks.

Style: an engineering drawing. Deep blueprint-navy background #0B2545 with a faint square grid, crisp white and pale-cyan linework, dimension arrows and leader-line callouts, labels in a technical monospaced font, and copper-orange #E9B07C only on the big numbers. A drafting title block in the bottom-right corner reading "AI DISPENSING DEFECT DETECTIVE · SHEET 1 OF 4 · REV A". The photo sits in a thin white frame, like a reference image pinned to the drawing. Precise, schematic, memorable from across a room.
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
6. Four big-number tiles: "95%" — "right when it shows ★★★"; "89%" — "phone photos measured correctly"; "66%" — "right even when a quarter of answers are guesses"; "0" — "training data · runs offline"
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
6. Four big-number tiles: "95%" — "right when it shows ★★★"; "89%" — "phone photos measured correctly"; "66%" — "right even when a quarter of answers are guesses"; "0" — "training data · runs offline"
7. Three small boxes previewing the inside: "① Dual-brain ranking", "② Feedback loop", "③ Knowledge system"
8. Footer in small type: "Knowledge source: NPL Best Practice Guide MATC(A)82 · All test images are synthetic"

Render every quoted text exactly as written, spelled correctly. Add no other words, numbers, logos, people or watermarks.

Style: a bold editorial infographic, like a premium consulting report. Big confident sans-serif headings, oversized numbers, colour-blocked bands in deep green #0E3B2E, mint #9CC9B1 and white, copper #C8742B highlights, rounded cards with soft shadows, line icons in circles, and arrows that lead the eye from top to bottom. Readable in ten seconds from a metre away, yet clearly technical. No stock photos of people, no 3D clip-art.
```

---

## Round 2 — the inside pages

### Page 2 · The dual-brain ranking

```
Same style as the cover you just made — same colours, fonts and diagram style. Design page 2 of the brief: one A4 portrait page (210 × 297 mm), flat, straight-on and edge to edge, finished print artwork. If the style has a drawing title block, it reads "SHEET 2 OF 4".

Layout, top to bottom:
1. Section heading: "① The dual-brain ranking"
2. Intro line: "Two independent readers, and two gates that can only lower confidence."
3. A large flow diagram, left to right:
   • Four small input boxes on the left — "Photo measurements", "Five answers", "Follow-up answers", "Check results" — with arrows into a big box "BRAIN 1 · THE INSTRUMENT", subtitle "42 rules, each citing a manual page". Its output: "7 causes, each with a %".
   • Underneath, one input box, "Operator's own words", with an arrow into a second big box "BRAIN 2 · THE CRITIC (LLM)", subtitle "sees no measurements · can only object".
   • Both brains feed a diamond, "Agree?", then two gates side by side: "GATE A · CHANCE" with "more than coincidence? p < 0.05", and "GATE B · PRECEDENT" with "can demote, never promote".
   • Output on the right: four stacked badges from strongest to weakest: "T1 · one lead cause, backed", "T2 · lead cause, provisional", "T3 · both candidates shown", "T4 · no lead — the check that separates them".
4. Bottom left, a panel titled "Why 59%?": a small waterfall chart for "Air trapped in the syringe" — a bar "start 15%", a step "+ comes and goes (brief p.3)", a step "+ purging helps (brief p.4)", ending at a highlighted total "59%".
5. Bottom right, a panel titled "Is the confidence honest?": four bars labelled "★", "★★", "★★★", "★★★★" with values "52%", "75%", "95%", "97%" and the caption "top cause correct, by stars shown".
6. Short paragraphs of body text drawn as neat grey placeholder lines.

Render every quoted text exactly as written. Add no other words, numbers, logos or watermarks.
```

### Page 3 · The feedback loop

```
Same style as the cover you just made — same colours, fonts and diagram style. Design page 3 of the brief: one A4 portrait page (210 × 297 mm), flat, straight-on and edge to edge, finished print artwork. If the style has a drawing title block, it reads "SHEET 3 OF 4".

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
```

### Page 4 · The knowledge system

```
Same style as the cover you just made — same colours, fonts and diagram style. Design page 4 of the brief: one A4 portrait page (210 × 297 mm), flat, straight-on and edge to edge, finished print artwork. If the style has a drawing title block, it reads "SHEET 4 OF 4".

Layout, top to bottom:
1. Section heading: "③ The knowledge system"
2. Intro line: "What it knows from the manual, and what it remembers from proved fixes."
3. A two-column diagram:
   • Left, titled "FROM THE MANUAL": a book icon labelled "NPL Best Practice Guide MATC(A)82", with an arrow to a card "7 causes · 42 rules · every rule cites its section and page".
   • Right, titled "FROM PAST CASES": a database icon labelled "Case history", splitting into two arrows. One leads to a speech-bubble card: "Similar problems occurred 12 times previously. In 8 cases, the main cause was air trapped in the syringe or material supply." tagged "shown to people · never moves the ranking". The other leads to a shield icon: "Precedent gate · CONFIRMED cases only · can only lower confidence".
   • Only the manual card and the shield send arrows down into a box labelled "Ranking"; the speech bubble has no arrow onward.
4. A band titled "No embeddings, no model training — every match can be explained", with short placeholder text.
5. A bottom strip titled "Evidence" with three stat tiles: "66% vs 54%" — "top cause right: photo + answers vs answers alone"; "95%" — "right when it shows ★★★"; "0%" — "false alarms on phone photos". Under it, in small grey type: "All test images are synthetic · next step: validate on real NSW photos".
6. Short paragraphs of body text drawn as neat grey placeholder lines.

Render every quoted text exactly as written. Add no other words, numbers, logos or watermarks.
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

- **59%**: air trapped in the syringe. It starts at 15% and adds "comes and
  goes" (brief p.3) and "purging helps" (brief p.4). Pressure-time
  variability also sits at 59%, from the measured size spread. The follow-up
  question breaks that tie.
- **84%**: pressure-time variability if the operator answers that the gauge
  wanders.
- **p = 0.010**: carryover, where all 3 small dots are each followed by an
  oversized one. **p = 0.62**: 1 of 4, so it is treated as noise.
- **★ 52% · ★★ 75% · ★★★ 95% · ★★★★ 97%**: how often the top cause is right,
  by stars shown.
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
