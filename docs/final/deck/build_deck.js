// Builds the AI Horizon final-round deck: 7 slides for the 3-minute pitch,
// then backup slides for Q&A. Native, editable charts; speaker notes on
// every slide. Numbers come from evaluation/results/latest.json (2026-10-05).
// The spoken script is ../pitch-script.md — keep the two in step.
//
//   npm install pptxgenjs react-icons react react-dom sharp
//   node build_deck.js            -> AI-Dispensing-Defect-Detective.pptx

const path = require("path");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const lu = require("react-icons/lu");
const PptxGenJS = require("pptxgenjs");

const ASSETS = path.join(__dirname, "assets");
const asset = (name) => path.join(ASSETS, name);

// ---- design tokens ---------------------------------------------------------
const C = {
  dark: "0E3B2E", // solder-mask green: title and closing slides
  green: "1F7A4D", // PCB green: the dominant accent
  greenLight: "6FB08C",
  mint: "9CC9B1", // secondary text on dark
  mintSoft: "D6E8DE",
  tint: "EEF5F1", // card fill on white
  copper: "C8742B", // the one sharp accent: key numbers
  copperSoft: "E9B07C",
  ink: "14201B",
  ink2: "4A5751",
  muted: "7B8781",
  white: "FFFFFF",
  good: "0CA30C",
  warn: "D08A00",
  warnFill: "FAB219",
  crit: "D03B3B",
  neutral: "B9B8B3",
};
const HEAD = "Cambria";
const BODY = "Calibri";
const W = 13.333;
const MX = 0.6; // side margin

// A missing icon name shouldn't fail the whole build the morning of the final.
const missingIcons = new Set();
async function icon(name, color = "#FFFFFF") {
  let Comp = lu[name];
  if (!Comp) {
    missingIcons.add(name);
    Comp = lu.LuCircle ?? lu.LuInfo ?? Object.values(lu)[0];
  }
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { size: 256, color }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}

function shadow() {
  return { type: "outer", angle: 90, blur: 10, offset: 2, color: "000000", opacity: 0.16 };
}

function kicker(slide, text, color = C.copper, y = 0.42) {
  slide.addText(text, {
    x: MX, y, w: 9, h: 0.3, fontFace: BODY, fontSize: 12, bold: true, color,
    charSpacing: 3, margin: 0, isTextBox: true,
  });
}

function title(slide, text, color = C.ink, y = 0.72, h = 1.1, size = 30) {
  slide.addText(text, {
    x: MX, y, w: W - 2 * MX, h, fontFace: HEAD, fontSize: size, bold: true, color,
    valign: "top", margin: 0, isTextBox: true, fit: "shrink",
  });
}

async function iconCircle(slide, name, x, y, d, fill = C.green, glyph = "#FFFFFF") {
  slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  const s = d * 0.54;
  slide.addImage({ data: await icon(name, glyph), x: x + (d - s) / 2, y: y + (d - s) / 2, w: s, h: s });
}

function footnote(slide, text, color = C.muted, y = 6.95) {
  slide.addText(text, {
    x: MX, y, w: W - 2 * MX, h: 0.35, fontFace: BODY, fontSize: 11, color, italic: true,
    margin: 0, isTextBox: true, valign: "bottom",
  });
}

/** The repeated "row of tinted cards" block: icon, heading, body. */
async function cardRow(s, cards, { top, h, cw, gap, headSize = 20, bodySize = 15, bodyDy = 2.04 }) {
  for (let i = 0; i < cards.length; i++) {
    const [ic, head, body] = cards[i];
    const x = MX + i * (cw + gap);
    s.addShape("roundRect", { x, y: top, w: cw, h, fill: { color: C.tint }, line: { color: C.tint }, rectRadius: 0.12 });
    await iconCircle(s, ic, x + 0.32, top + 0.32, 0.74);
    s.addText(head, {
      x: x + 0.32, y: top + 1.22, w: cw - 0.64, h: 0.78, fontFace: BODY, fontSize: headSize, bold: true,
      color: C.ink, margin: 0, isTextBox: true, valign: "top",
    });
    s.addText(body, {
      x: x + 0.32, y: top + bodyDy, w: cw - 0.64, h: h - bodyDy - 0.26, fontFace: BODY, fontSize: bodySize, color: C.ink2,
      margin: 0, isTextBox: true, valign: "top",
    });
  }
}

async function build() {
  const pres = new PptxGenJS();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "Team Lithium";
  pres.title = "AI Dispensing Defect Detective — AI Horizon 2026 final";

  // ==== 1. Title & team ====================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.dark };
    s.addText("AI HORIZON 2026  ·  CHALLENGE 2  ·  NSW AUTOMATION", {
      x: MX + 0.1, y: 0.7, w: 6.4, h: 0.3, fontFace: BODY, fontSize: 11, bold: true, color: C.mint,
      charSpacing: 2, margin: 0, isTextBox: true,
    });
    s.addText("AI Dispensing\nDefect Detective", {
      x: MX + 0.1, y: 1.2, w: 6.2, h: 1.95, fontFace: HEAD, fontSize: 46, bold: true, color: C.white,
      margin: 0, isTextBox: true, valign: "top",
    });
    s.addText("A phone photo and five questions → the likely cause, the reasons behind it, and what to check first.", {
      x: MX + 0.1, y: 3.3, w: 5.9, h: 1.05, fontFace: BODY, fontSize: 19, color: C.mintSoft,
      margin: 0, isTextBox: true, valign: "top",
    });
    s.addText("And a case history that only learns from fixes that were proved.", {
      x: MX + 0.1, y: 4.4, w: 5.9, h: 0.7, fontFace: BODY, fontSize: 17, italic: true, color: C.copperSoft,
      margin: 0, isTextBox: true, valign: "top",
    });
    // Scope badge: the five steps, the dynamic-questions bonus, all four bonuses.
    s.addShape("roundRect", {
      x: MX + 0.1, y: 5.3, w: 6.1, h: 0.62, fill: { color: C.green }, line: { color: C.green }, rectRadius: 0.31,
    });
    s.addText("All 5 steps  ·  dynamic questions  ·  all 4 bonus challenges", {
      x: MX + 0.1, y: 5.3, w: 6.1, h: 0.62, fontFace: BODY, fontSize: 15, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0, isTextBox: true,
    });
    s.addText("Team Lithium  ·  Universiti Sains Malaysia", {
      x: MX + 0.1, y: 6.25, w: 6.1, h: 0.35, fontFace: BODY, fontSize: 15, color: C.mint, margin: 0, isTextBox: true,
    });
    s.addImage({ path: asset("phone_annotated_slide.png"), x: 6.95, y: 1.05, w: 5.8, h: 4.13, shadow: shadow() });
    s.addText("A phone photo of a printed sample card, lying on a desk. Each missing deposit is followed by an oversized one: the system reads carryover, p = 0.010.", {
      x: 6.95, y: 5.32, w: 5.8, h: 0.8, fontFace: BODY, fontSize: 12, color: C.mint, margin: 0, isTextBox: true, valign: "top",
    });
    s.addNotes(
      "~18 s. Good morning. We're Team Lithium, three of us from Universiti Sains Malaysia, and we took NSW Automation's " +
      "challenge all the way: the five core steps, the dynamic-questions bonus, and all four bonus challenges. " +
      "That's a phone photo of a part lying on a desk. The system lines the recipe up with it and reads the pattern: " +
      "three missing deposits, each one followed by an oversized one. That's carryover.",
    );
  }

  // ==== 2. The problem =====================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "THE PROBLEM");
    title(s, "Dispensing defects are diagnosed by experience — and experience doesn't scale");
    const cards = [
      ["LuUserRound", "New technicians guess",
        "Inconsistent size alone has five plausible causes. The first check becomes a hunch — and a wrong strip-down costs a shift."],
      ["LuShuffle", "Three changes at once",
        "Re-prime, raise the pressure, swap the needle. The defect goes away, and nobody can say which change did it."],
      ["LuHistory", "Knowledge walks out",
        "What the senior engineer knows is written down nowhere the next case can reach."],
      ["LuEyeOff", "A score nobody can check",
        "An engineer who can't see why a number says 85% won't act on it. Black-box confidence gets ignored on the line."],
    ];
    await cardRow(s, cards, { top: 2.1, h: 3.95, cw: 2.853, gap: 0.24, headSize: 19, bodySize: 14 });
    footnote(s, "NSW Automation's brief: help engineers and technicians perform faster preliminary troubleshooting — not replace them.", C.muted, 6.45);
    s.addNotes(
      "~26 s. When dots come out wrong, an experienced engineer knows where to look. A new technician doesn't — " +
      "inconsistent size alone has five plausible causes, and a wrong guess can mean stripping a valve for a whole shift. " +
      "So people change three things at once. The defect goes away, and nobody can say which change fixed it — the next case starts from zero. " +
      "Meanwhile what the senior engineer knows is written down nowhere the next case can reach. " +
      "And a confidence score an engineer can't check is a score they'll ignore.",
    );
  }

  // ==== 3. The solution ====================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "THE SOLUTION");
    title(s, "One guided session, from a phone photo to a proved fix");
    const steps = [
      ["LuCamera", "Photograph", "Measures size spread, shape and missing dots — however the photo is framed"],
      ["LuMessageCircleQuestion", "Interview", "Five questions, then follow-ups picked because their answer changes the ranking"],
      ["LuListOrdered", "Rank", "Seven causes from the manual — every % built from cited reasons"],
      ["LuScanSearch", "Check", "Look first, then change one thing; the ranking updates live"],
      ["LuRuler", "Verify", "Re-photograph: in spec on every check, held 20+ shots"],
      ["LuDatabase", "Learn", "Only proved fixes become precedent for the next case"],
    ];
    const colW = (W - 2 * MX) / steps.length;
    const cy = 2.15, d = 0.95;
    for (let i = 0; i < steps.length; i++) {
      const cx = MX + i * colW + colW / 2;
      if (i < steps.length - 1) {
        s.addShape("line", {
          x: cx + d / 2 + 0.12, y: cy + d / 2, w: colW - d - 0.24, h: 0,
          line: { color: C.greenLight, width: 2, endArrowType: "triangle" },
        });
      }
      await iconCircle(s, steps[i][0], cx - d / 2, cy, d, i === steps.length - 1 ? C.copper : C.green);
      s.addText(`${i + 1}  ${steps[i][1]}`, {
        x: cx - colW / 2 + 0.08, y: cy + d + 0.25, w: colW - 0.16, h: 0.4, fontFace: BODY, fontSize: 18, bold: true,
        color: C.ink, align: "center", margin: 0, isTextBox: true,
      });
      s.addText(steps[i][2], {
        x: cx - colW / 2 + 0.12, y: cy + d + 0.72, w: colW - 0.24, h: 1.4, fontFace: BODY, fontSize: 13.5,
        color: C.ink2, align: "center", margin: 0, isTextBox: true, valign: "top",
      });
    }
    // What the flow above actually enables — the impact row.
    const impact = [
      ["LuGraduationCap", "A technician's first check, ranked with reasons"],
      ["LuFileText", "An audit-ready PDF on every case"],
      ["LuShieldCheck", "Only proved fixes become precedent"],
      ["LuWifiOff", "Offline on a line PC — a phone is enough"],
    ];
    const by = 5.5, bh = 1.0;
    s.addShape("roundRect", { x: MX, y: by, w: W - 2 * MX, h: bh, fill: { color: C.tint }, line: { color: C.tint }, rectRadius: 0.1 });
    s.addText("WHAT IT ENABLES", {
      x: MX + 0.3, y: by + 0.08, w: 3, h: 0.22, fontFace: BODY, fontSize: 9.5, bold: true, color: C.copper,
      charSpacing: 2, margin: 0, isTextBox: true,
    });
    const fw = (W - 2 * MX) / impact.length;
    for (let i = 0; i < impact.length; i++) {
      const fx = MX + i * fw + 0.3;
      await iconCircle(s, impact[i][0], fx, by + 0.36, 0.46);
      s.addText(impact[i][1], {
        x: fx + 0.58, y: by + 0.32, w: fw - 0.95, h: 0.56, fontFace: BODY, fontSize: 13.5, bold: true, color: C.ink,
        valign: "middle", margin: 0, isTextBox: true,
      });
    }
    s.addNotes(
      "~42 s. One guided session does the whole thing. The operator photographs the deposits — any framing, phone in hand. " +
      "Five questions. Then up to two follow-ups, and each follow-up is chosen because its answer would move the ranking most. " +
      "Seven causes come back ranked, every percentage built from reasons you can read. The operator looks first, changes one thing, " +
      "and the ranking updates live. A fresh photo verifies the fix. " +
      "What that enables: a new technician's first check is ranked, with reasons, instead of a hunch. Every case leaves an audit-ready PDF. " +
      "Only fixes that were actually proved become precedent. And it runs offline on a line PC — a phone camera is enough.",
    );
  }

  // ==== 4. The AI ==========================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "THE AI");
    title(s, "Two brains that are allowed to disagree — over a manual you can audit");
    const cards = [
      ["LuBookOpen", "Knowledge database",
        "Seven causes and 42 weighted rules, every one citing NPL's Best Practice Guide by section and page. " +
        "Past confirmed cases are counted as precedent: “similar problems occurred 12 times; in 8, the cause was trapped air.”"],
      ["LuBrain", "Dual-brain ranking",
        "Pass 1 — a deterministic rule engine does the arithmetic in log-odds and sets every percentage. " +
        "Pass 2 — an LLM critic reads the same evidence and can disagree. Disagreement lowers the tier and says so. " +
        "The model never sets a number."],
      ["LuUsers", "Senior-engineer loop",
        "The operator escalates mid-case; the senior answers inside the case, logs the check that settles it, " +
        "and can change a rule's weight — with a reason. It learns from people, not only from data."],
    ];
    await cardRow(s, cards, { top: 1.95, h: 3.6, cw: 3.857, gap: 0.28, headSize: 20, bodySize: 13.5, bodyDy: 1.85 });
    // The proof strip: the innovation claims, measured.
    const stats = [
      ["96%", "top cause correct when three or more reasons back it — 48% on one reason. The operator can count them on screen."],
      ["66% vs 14%", "correct from one photo and five answers, with a quarter of the answers wrong — against a chance baseline of 14%."],
      ["108", "automated checks: 79 backend tests, 27 measurement oracles, 2 end-to-end golden cases."],
    ];
    const sy = 5.75, sh = 0.95, sgap = 0.28, sw = (W - 2 * MX - 2 * sgap) / 3;
    for (let i = 0; i < stats.length; i++) {
      const x = MX + i * (sw + sgap);
      s.addText(stats[i][0], {
        x, y: sy, w: sw, h: 0.45, fontFace: BODY, fontSize: 26, bold: true, color: C.copper, margin: 0, isTextBox: true, valign: "top",
      });
      s.addText(stats[i][1], {
        x, y: sy + 0.45, w: sw, h: sh - 0.4, fontFace: BODY, fontSize: 12, color: C.ink2, margin: 0, isTextBox: true, valign: "top",
      });
    }
    footnote(s, "Precedent can lower confidence, never raise it — so the system cannot talk itself into being right.", C.green, 6.95);
    s.addNotes(
      "~50 s. Three parts make that work. A knowledge database — seven causes and forty-two weighted rules, every one citing " +
      "NPL's Best Practice Guide by section and page. A dual-brain ranking system: pass one is a deterministic rule engine that does " +
      "the arithmetic in log-odds and sets every percentage; pass two is an LLM critic that reads the same evidence and can disagree. " +
      "When they disagree we drop the confidence tier and say so, instead of hiding the split — the language model never sets a number. " +
      "And a senior-engineer feedback loop: the operator escalates, the senior answers inside the case and can change a rule's weight, with a reason. " +
      "We measured this rather than asserting it: with three or more reasons behind it the top cause is right 96 percent of the time; with one, 48 — a coin flip. " +
      "And precedent can only lower confidence, never raise it, so the system can't talk itself into being right.",
    );
  }

  // ==== 5. Third-party declaration =========================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "RULE c.2  ·  THIRD-PARTY DECLARATION");
    title(s, "What we built, and what we used");
    const ours = [
      "The fault tree and its weighted, cited rules",
      "Two-pass ranking, the chance and precedent gates, tiers T1–T4",
      "The five-condition close rule and the verdicts",
      "Five-axis interview and the follow-up selection",
      "Retrieval and precedent counting",
      "Photo registration, desk masking, all metrology",
      "The synthetic defect generator and the evaluation",
    ];
    const theirs = [
      "NPL Report MATC(A)82 — Best Practice for Electronic Materials Dispensing (2001), © Crown copyright, cited on screen",
      "NSW Automation challenge brief — rules citing “NSW brief p.N”",
      "Groq API, openai/gpt-oss-20b — optional critic, free-text mapping, written explanation",
      "FastAPI, Pydantic, SQLAlchemy, Alembic · OpenCV, NumPy",
      "Next.js, React, Tailwind, shadcn/ui, Base UI, lucide",
      "Dev only: pytest, Playwright, matplotlib",
    ];
    const col = (x, head, items, fill, headColor) => {
      s.addShape("roundRect", { x, y: 1.9, w: 5.85, h: 4.5, fill: { color: fill }, line: { color: fill }, rectRadius: 0.12 });
      s.addText(head, {
        x: x + 0.35, y: 2.08, w: 5.15, h: 0.45, fontFace: BODY, fontSize: 19, bold: true, color: headColor,
        margin: 0, isTextBox: true,
      });
      s.addText(items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < items.length - 1 } })), {
        x: x + 0.35, y: 2.64, w: 5.15, h: 3.6, fontFace: BODY, fontSize: 14.5, color: C.ink2,
        paraSpaceAfter: 7, margin: 0, isTextBox: true, valign: "top",
      });
    };
    col(MX, "Our own work", ours, C.tint, C.green);
    col(MX + 6.25, "Third-party, declared", theirs, "F4F4F2", C.ink);
    footnote(s, "No model was trained or fine-tuned, and the vision uses no training data — it is classical OpenCV, reproducible by an engineer with a microscope.", C.muted, 6.6);
    s.addNotes(
      "~16 s. Declared under rule c.2. The knowledge is NPL Report MATC(A)82, Crown copyright, cited on screen wherever it's used. " +
      "Groq runs the optional LLM. FastAPI, Next.js, OpenCV. Everything else is ours — the fault tree, the two-pass ranking, the gates, " +
      "the close rule, the photo registration, the metrology. No model was trained or fine-tuned, and the vision uses no training data at all.",
    );
  }

  // ==== 6. Limitations =====================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "LIMITATIONS");
    title(s, "What it doesn't do — stated before you have to find it");
    const lim = [
      ["No real production photos", "NSW had none to give us, so every threshold is tuned on synthetic images. Validating on real NSW photos is step one of a pilot. This is our biggest gap."],
      ["Seven causes", "Stringing, smearing and satellites (up height, NPL §3.3) have no cause yet. They're reported as “no cause ahead” and escalated — not guessed."],
      ["Busy boards", "A trace touching a deposit can read as a distorted shape: 9% false alarms under light clutter. The fix is a bare-board reference photo."],
      ["Pixels, not microns", "Everything is relative to the recipe; absolute volume needs a scale reference or a known pitch."],
      ["The LLM isn't reproducible", "Critic and explanation can vary between runs — which is exactly why neither is allowed to change a likelihood."],
    ];
    for (let i = 0; i < lim.length; i++) {
      const y = 1.95 + i * 0.97;
      await iconCircle(s, "LuTriangleAlert", MX, y + 0.05, 0.55, "8A8984");
      s.addText(lim[i][0], {
        x: MX + 0.8, y, w: 3.4, h: 0.68, fontFace: BODY, fontSize: 16, bold: true, color: C.ink,
        valign: "middle", margin: 0, isTextBox: true,
      });
      s.addText(lim[i][1], {
        x: MX + 4.35, y, w: 7.75, h: 0.68, fontFace: BODY, fontSize: 13.5, color: C.ink2,
        valign: "middle", margin: 0, isTextBox: true,
      });
    }
    footnote(s, "The measurement oracle deliberately includes cases the system fails, asserted as failures rather than hidden.", C.muted, 6.95);
    s.addNotes(
      "~22 s. What it doesn't do. NSW had no production photos to give us, so every threshold is tuned on synthetic images — " +
      "validating on real ones is step one of a pilot. That's our biggest gap, and we'd rather say it than have you find it. " +
      "Seven causes: anything outside them is reported as 'no cause ahead' and escalated, not guessed. " +
      "On a busy board, a trace touching a deposit can still read as a bad shape. And measurements are in pixels, not microns.",
    );
  }

  // ==== 7. Close → demo ====================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.dark };
    s.addText("Faster first checks.\nAn auditable record.\nA history that only learns from proved fixes.", {
      x: MX + 0.1, y: 1.75, w: 8.6, h: 2.9, fontFace: HEAD, fontSize: 36, bold: true, color: C.white,
      lineSpacingMultiple: 1.25, margin: 0, isTextBox: true, valign: "top",
    });
    s.addText("Live demo  →", {
      x: MX + 0.1, y: 5.0, w: 8.6, h: 0.7, fontFace: HEAD, fontSize: 30, bold: true, color: C.copperSoft,
      margin: 0, isTextBox: true,
    });
    s.addText("Team Lithium  ·  Universiti Sains Malaysia  ·  AI Dispensing Defect Detective", {
      x: MX + 0.1, y: 6.5, w: 11, h: 0.35, fontFace: BODY, fontSize: 13, color: C.mint, margin: 0, isTextBox: true,
    });
    s.addNotes("~8 s. That's the system. Let me show you one case, from a phone photo to a confirmed fix. [Switch to the browser — don't read this slide out.]");
  }

  // ==== B1. Backup: calibration ============================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "BACKUP · EVIDENCE", C.muted);
    title(s, "The more reasons behind it, the more often it's right");
    s.addChart(pres.charts.BAR, [{
      name: "Top cause correct",
      labels: ["1 reason", "2", "3", "4+"],
      values: [48, 72, 95, 100],
    }], {
      x: MX, y: 1.8, w: 6.7, h: 4.55, barDir: "col", chartColors: [C.green], barGapWidthPct: 85,
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0"%"', dataLabelFontSize: 16,
      dataLabelFontFace: BODY, dataLabelColor: C.ink, dataLabelFontBold: true,
      valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 110, valGridLine: { style: "none" },
      catAxisLabelFontSize: 20, catAxisLabelColor: C.ink2, catAxisLabelFontFace: BODY, catAxisLineShow: true,
      catAxisLineColor: "C3C2B7", catGridLine: { style: "none" }, showLegend: false,
      showTitle: true, title: "Top cause correct, by the reasons shown behind it", titleFontSize: 14,
      titleColor: C.ink2, titleFontFace: BODY,
    });
    s.addText("Photo + answers · 420 simulated cases at three answer-reliability levels · chance = 14%", {
      x: MX, y: 6.38, w: 6.7, h: 0.3, fontFace: BODY, fontSize: 12, color: C.muted, margin: 0, isTextBox: true, align: "center",
    });
    const stats = [
      ["66%", "top cause right from one photo and five answers, with an operator whose answers are only 75% reliable — chance is 14%"],
      ["6,600", "synthetic photos and 420 simulated cases through the real code, in every evaluation run (about a minute)"],
      ["108", "automated checks — 79 backend tests, 27 measurement oracles, 2 golden cases — plus a browser run of the whole wizard"],
    ];
    const sx = 7.75, sw = 4.95;
    for (let i = 0; i < stats.length; i++) {
      const sy = 1.95 + i * 1.5;
      s.addText(stats[i][0], {
        x: sx, y: sy, w: sw, h: 0.72, fontFace: BODY, fontSize: 44, bold: true, color: C.copper, margin: 0, isTextBox: true, valign: "top",
      });
      s.addText(stats[i][1], {
        x: sx, y: sy + 0.72, w: sw, h: 0.7, fontFace: BODY, fontSize: 13.5, color: C.ink2, margin: 0, isTextBox: true, valign: "top",
      });
    }
    footnote(s, "All test images are synthetic — NSW provided no production photos. Method, limits and every table: evaluation/README.md.");
    s.addNotes("Backup for 'how accurate is it?'. Three or more reasons → 96% correct; one reason → 48%, a coin flip.");
  }

  // ==== B2. Backup: phone photo ============================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "BACKUP · FEASIBILITY", C.muted);
    title(s, "Works on the photo an operator actually takes");
    const iw = 4.3, ih = iw / 1.405, iy = 2.05;
    s.addImage({ path: asset("phone_input.jpg"), x: MX, y: iy, w: iw, h: ih, shadow: shadow() });
    s.addShape("rightArrow", { x: MX + iw + 0.18, y: iy + ih / 2 - 0.28, w: 0.62, h: 0.56, fill: { color: C.copper }, line: { color: C.copper } });
    const x2 = MX + iw + 0.98;
    s.addImage({ path: asset("phone_annotated_slide.png"), x: x2, y: iy, w: iw, h: ih, shadow: shadow() });
    s.addText("Phone photo: card on a desk, camera tilted and off-centre", {
      x: MX, y: iy + ih + 0.15, w: iw, h: 0.6, fontFace: BODY, fontSize: 13, color: C.ink2, margin: 0, isTextBox: true, valign: "top",
    });
    s.addText("Recipe lined up (scale, rotation, perspective), then measured: 3 missing, 3 oversized, carryover p = 0.010", {
      x: x2, y: iy + ih + 0.15, w: iw, h: 0.6, fontFace: BODY, fontSize: 13, color: C.ink2, margin: 0, isTextBox: true, valign: "top",
    });
    const sx = x2 + iw + 0.35, sw = W - MX - sx;
    s.addText("0% → 89%", {
      x: sx, y: 2.0, w: sw, h: 0.65, fontFace: BODY, fontSize: 30, bold: true, color: C.copper, margin: 0, isTextBox: true,
    });
    s.addText("of phone-style photos measured correctly, before → after registration — the same as perfectly framed ones", {
      x: sx, y: 2.65, w: sw, h: 1.45, fontFace: BODY, fontSize: 13, color: C.ink2, margin: 0, isTextBox: true, valign: "top",
    });
    s.addText("0", {
      x: sx, y: 4.15, w: sw, h: 0.65, fontFace: BODY, fontSize: 30, bold: true, color: C.copper, margin: 0, isTextBox: true,
    });
    s.addText("false alarms from zoom, framing, tilt or a desk in shot", {
      x: sx, y: 4.8, w: sw, h: 0.9, fontFace: BODY, fontSize: 13, color: C.ink2, margin: 0, isTextBox: true, valign: "top",
    });
    footnote(s, "Photo simulated from a printed sample card (the evaluation's 'on desk' condition). Validating on real NSW photos is step one of the pilot.");
    s.addNotes("Backup for 'does it work on a real photo?'. Our own stress test found it only measured recipe-framed photos; registration fixed that.");
  }

  // ==== B3. Backup: proved vs fixed ========================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "BACKUP · TRUST", C.muted);
    title(s, "Closing a case is not the same as fixing it");
    const tiers = [
      ["CONFIRMED", C.good, "All five proved", [
        "a check confirmed one cause",
        "exactly one change, aimed at it",
        "re-measured against a 'before' photo",
        "in spec on every check",
        "held 20+ shots",
      ], "The only cases future rankings learn from"],
      ["PLAUSIBLE", C.warn, "Some proved", [
        "e.g. cause certain (tier T1) — but one deposit is still missing after the fix",
      ], "Shown as context; adjusts nothing"],
      ["UNVERIFIED", "8A8984", "Nothing proved", [
        "filed with the gaps named — e.g. '3 things changed at once: no way to say which one worked'",
      ], "Adjusts nothing"],
    ];
    const cw = 3.85, gap = 0.28, top = 1.95, ch = 3.95;
    for (let i = 0; i < tiers.length; i++) {
      const [name, col, head, lines, foot] = tiers[i];
      const x = MX + i * (cw + gap);
      s.addShape("roundRect", { x, y: top, w: cw, h: ch, fill: { color: C.tint }, line: { color: C.tint }, rectRadius: 0.12 });
      s.addShape("roundRect", { x: x + 0.35, y: top + 0.35, w: 1.95, h: 0.46, fill: { color: col }, line: { color: col }, rectRadius: 0.23 });
      s.addText(name, {
        x: x + 0.35, y: top + 0.35, w: 1.95, h: 0.46, fontFace: BODY, fontSize: 13, bold: true, color: C.white,
        align: "center", valign: "middle", margin: 0, isTextBox: true, charSpacing: 1,
      });
      s.addText(head, {
        x: x + 0.35, y: top + 1.0, w: cw - 0.7, h: 0.45, fontFace: BODY, fontSize: 20, bold: true, color: C.ink, margin: 0, isTextBox: true,
      });
      s.addText(lines.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < lines.length - 1 } })), {
        x: x + 0.35, y: top + 1.55, w: cw - 0.7, h: 1.75, fontFace: BODY, fontSize: 14, color: C.ink2,
        paraSpaceAfter: 3, margin: 0, isTextBox: true, valign: "top",
      });
      s.addText(foot, {
        x: x + 0.35, y: top + ch - 0.6, w: cw - 0.7, h: 0.4, fontFace: BODY, fontSize: 14, bold: true, color: C.ink,
        margin: 0, isTextBox: true,
      });
    }
    s.addText("Precedent can lower confidence, never raise it — so the system can't talk itself into being right.", {
      x: MX, y: 6.2, w: W - 2 * MX, h: 0.45, fontFace: HEAD, fontSize: 18, italic: true, color: C.green, margin: 0, isTextBox: true,
    });
    s.addNotes("Backup for 'how do you know a fix worked?'. The one-change rule is the point: two changes at once can't say which one worked.");
  }

  // ==== B4. Backup: tiers ==================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "BACKUP · CONFIDENCE TIERS", C.muted);
    title(s, "Four confidence tiers — and agreement never raises one");
    const rows = [
      ["Tier", "Reached when", "What the operator sees"],
      ["T1", "A check on this case confirmed the top cause — or: rule engine and critic agree · deciding measurement beats chance · ≥3 similar confirmed cases, none contradicting", "One lead cause, with evidence and matching past cases"],
      ["T2", "They agree, but no precedent or the measurement isn't decisive", "One lead cause, marked provisional, with what would confirm it"],
      ["T3", "They disagree · the measurement beats chance", "Both candidates; the measurement holds the top slot"],
      ["T4", "They disagree · the measurement can't separate them", "No lead cause — the check that would separate them"],
    ];
    s.addTable(rows.map((r, i) => r.map((cell, j) => ({
      text: cell,
      options: {
        bold: i === 0 || j === 0, color: i === 0 ? C.white : C.ink, fill: { color: i === 0 ? C.green : i % 2 ? C.tint : C.white },
        fontFace: BODY, fontSize: 13.5, valign: "middle", margin: [0.08, 0.12, 0.08, 0.12],
      },
    }))), { x: MX, y: 1.85, w: W - 2 * MX, colW: [0.9, 6.0, 5.233], border: { type: "solid", pt: 0.75, color: "D7E3DC" }, rowH: 0.62 });
    s.addText([
      { text: "Gate A — chance. ", options: { bold: true } },
      { text: "Only a signal that separates causes counts: the dispense-order pattern (binomial test, p < 0.05). A size spread is real but shared by several causes, so it can't decide.", options: { breakLine: true } },
      { text: "Gate B — precedent. ", options: { bold: true } },
      { text: "Similar confirmed cases (same material and dispenser, signals within one spread) can demote the lead by up to 0.4 log-odds — never promote it." },
    ], { x: MX, y: 5.45, w: W - 2 * MX, h: 1.3, fontFace: BODY, fontSize: 14, color: C.ink2, margin: 0, isTextBox: true, paraSpaceAfter: 6, valign: "top" });
    s.addNotes("Backup for 'how do you decide confidence?' and 'what if the AI and the rules disagree?'.");
  }

  // ==== B5. Backup: reliability ============================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "BACKUP · EVALUATION", C.muted);
    title(s, "The photo matters most when the answers are worst");
    s.addChart(pres.charts.LINE, [
      { name: "Photo + questions", labels: ["100%", "75%", "50%"], values: [80.5, 66.2, 56.9] },
      { name: "Questions only", labels: ["100%", "75%", "50%"], values: [71.4, 54.3, 40.2] },
    ], {
      x: MX, y: 1.8, w: 8.2, h: 4.7, chartColors: [C.green, "8A958F"], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 10,
      showValue: false,
      valAxisMinVal: 0, valAxisMaxVal: 100, valAxisLabelFormatCode: '0"%"', valAxisLabelColor: C.muted, valAxisLabelFontSize: 12,
      valAxisLabelFontFace: BODY, catAxisLabelFontFace: BODY, catAxisTitleFontFace: BODY,
      valGridLine: { color: "E1E0D9", size: 1 }, catGridLine: { style: "none" },
      catAxisLabelColor: C.ink2, catAxisLabelFontSize: 14, catAxisTitle: "Share of the operator's answers that are right (the rest are random)",
      showCatAxisTitle: true, catAxisTitleColor: C.ink2, catAxisTitleFontSize: 13,
      showLegend: true, legendPos: "b", legendFontSize: 13, legendColor: C.ink2, legendFontFace: BODY,
    });
    s.addText([
      { text: "57% vs 40%", options: { bold: true, color: C.copper, fontSize: 30, breakLine: true } },
      { text: "top cause right when half the answers are guesses — with the photo, and without it.", options: { breakLine: true } },
      { text: " ", options: { breakLine: true } },
      { text: "● ", options: { color: C.green } },
      { text: "With the photo: 81% → 66% → 57%", options: { bold: true, color: C.ink, breakLine: true } },
      { text: "● ", options: { color: "8A958F" } },
      { text: "Questions only: 71% → 54% → 40%", options: { bold: true, color: C.ink, breakLine: true } },
      { text: " ", options: { breakLine: true } },
      { text: "Chance is 14% (one in seven). 420 simulated cases per point; answers from scenario cards written from the NPL guide, not from the rules." },
    ], { x: 9.2, y: 2.0, w: 3.55, h: 4.0, fontFace: BODY, fontSize: 14, color: C.ink2, margin: 0, isTextBox: true, valign: "top" });
    s.addNotes("Backup for 'what does the photo add?' and 'what if the operator answers badly?'.");
  }

  // ==== B6. Backup: stress =================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "BACKUP · EVALUATION", C.muted);
    title(s, "It refuses rather than misleads");
    // Rows listed bottom-up (bar charts plot the first category at the bottom).
    const labels = ["Board clutter (15 pads)", "Glare (+180 grey levels)", "Blur (σ 7 px)", "Zoomed 1.6×", "Phone photo on a desk, 9% tilt", "JPEG quality 5", "Sensor noise (σ 56)", "Undamaged"];
    const correct = [29, 1, 68, 89, 89, 89, 89, 89];
    const refused = [57, 97, 0, 0, 0, 0, 0, 0];
    const missed = [5, 2, 32, 11, 11, 11, 11, 11];
    const falseAlarm = [9, 0, 0, 0, 0, 0, 0, 0];
    s.addChart(pres.charts.BAR, [
      { name: "Correct", labels, values: correct },
      { name: "Refused (safe)", labels, values: refused },
      { name: "Missed", labels, values: missed },
      { name: "False alarm", labels, values: falseAlarm },
    ], {
      x: MX, y: 1.75, w: 9.0, h: 4.95, barDir: "bar", barGrouping: "percentStacked", barGapWidthPct: 55,
      chartColors: [C.good, C.neutral, C.warnFill, C.crit], valAxisHidden: true, valGridLine: { style: "none" },
      catAxisLabelColor: C.ink2, catAxisLabelFontSize: 13, catAxisLabelFontFace: BODY, catGridLine: { style: "none" },
      showLegend: true, legendPos: "b", legendFontSize: 13, legendFontFace: BODY, legendColor: C.ink2,
    });
    s.addText([
      { text: "9%", options: { bold: true, color: C.crit, fontSize: 30, breakLine: true } },
      { text: "false alarms under light board clutter — the only tested fault that misleads. The fix is a bare-board reference photo.", options: { breakLine: true } },
      { text: " ", options: { breakLine: true } },
      { text: "Everything else measures correctly or is refused with a reason. 'Missed' is the dispense-order pattern found in about half of carryover photos — the interview then carries it." },
    ], { x: 9.85, y: 2.0, w: 2.9, h: 4.6, fontFace: BODY, fontSize: 13, color: C.ink2, margin: 0, isTextBox: true, valign: "top" });
    s.addNotes("Backup for 'what if the photo is bad?'. 20 images per condition per level, 6,000 damaged photos in all.");
  }

  // ==== B7. Backup: impact & pilot =========================================
  {
    const s = pres.addSlide();
    s.background = { color: C.dark };
    s.addText("BACKUP · INDUSTRY IMPACT", {
      x: MX, y: 0.42, w: 9, h: 0.3, fontFace: BODY, fontSize: 12, bold: true, color: C.copperSoft, charSpacing: 3, margin: 0, isTextBox: true,
    });
    title(s, "Ready to pilot on an NSW line", C.white);
    const value = [
      ["LuGraduationCap", "A new technician's first check — ranked, with reasons"],
      ["LuFileText", "An audit-ready report for every case, printable as PDF"],
      ["LuDatabase", "A troubleshooting history that only keeps proved fixes"],
      ["LuSmartphone", "Runs offline on a line PC; a phone camera is enough"],
    ];
    s.addText("Value on day one", {
      x: MX, y: 1.85, w: 5.8, h: 0.4, fontFace: BODY, fontSize: 18, bold: true, color: C.mint, margin: 0, isTextBox: true,
    });
    for (let i = 0; i < value.length; i++) {
      const y = 2.45 + i * 0.95;
      await iconCircle(s, value[i][0], MX, y, 0.62, C.green);
      s.addText(value[i][1], {
        x: MX + 0.85, y, w: 5.0, h: 0.62, fontFace: BODY, fontSize: 16, color: C.white, valign: "middle", margin: 0, isTextBox: true,
      });
    }
    const plan = [
      "Validate on 50–100 real NSW photos per product",
      "Subtract a bare-board reference photo to remove clutter false alarms",
      "Rules as data: engineers add causes (e.g. up height, NPL §3.3) without code",
      "Predict: open a case automatically when a line's size spread starts drifting",
    ];
    const px = 7.0;
    s.addText("Pilot plan", {
      x: px, y: 1.85, w: 5.7, h: 0.4, fontFace: BODY, fontSize: 18, bold: true, color: C.mint, margin: 0, isTextBox: true,
    });
    for (let i = 0; i < plan.length; i++) {
      const y = 2.45 + i * 0.95;
      s.addShape("ellipse", { x: px, y: y + 0.03, w: 0.56, h: 0.56, fill: { color: C.copper }, line: { color: C.copper } });
      s.addText(String(i + 1), {
        x: px, y: y + 0.03, w: 0.56, h: 0.56, fontFace: BODY, fontSize: 16, bold: true, color: C.white, align: "center", valign: "middle", margin: 0, isTextBox: true,
      });
      s.addText(plan[i], {
        x: px + 0.8, y, w: 4.9, h: 0.62, fontFace: BODY, fontSize: 15, color: C.white, valign: "middle", margin: 0, isTextBox: true,
      });
    }
    s.addNotes("Backup for 'could NSW actually deploy this?' and feasibility questions.");
  }

  const out = path.join(__dirname, "AI-Dispensing-Defect-Detective.pptx");
  await pres.writeFile({ fileName: out });
  if (missingIcons.size) {
    console.warn("MISSING ICON NAMES (fell back to a circle):", [...missingIcons].join(", "));
  }
  console.log("wrote", out, "— 7 pitch slides + 7 backup slides");
}

build().catch((err) => {
  console.error(err);
  process.exit(1);
});
