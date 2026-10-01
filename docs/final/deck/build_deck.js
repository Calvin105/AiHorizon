// Builds the AI Horizon final-round deck: 8 slides for the 3-minute pitch,
// then backup slides for Q&A. Native, editable charts; speaker notes on
// every slide. Numbers come from evaluation/results/latest.json (2026-10-02).
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

async function icon(name, color = "#FFFFFF") {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(lu[name], { size: 256, color }));
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

async function build() {
  const pres = new PptxGenJS();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "Calvin Khoo";
  pres.title = "AI Dispensing Defect Detective — AI Horizon 2026 final";

  // ==== 1. Title ===========================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.dark };
    s.addText("AI HORIZON 2026  ·  CHALLENGE 2  ·  NSW AUTOMATION", {
      x: MX + 0.1, y: 0.75, w: 6.4, h: 0.3, fontFace: BODY, fontSize: 11, bold: true, color: C.mint,
      charSpacing: 2, margin: 0, isTextBox: true,
    });
    s.addText("AI Dispensing\nDefect Detective", {
      x: MX + 0.1, y: 1.3, w: 6.2, h: 2.0, fontFace: HEAD, fontSize: 46, bold: true, color: C.white,
      margin: 0, isTextBox: true, valign: "top",
    });
    s.addText("A phone photo and five questions → the likely cause, the reasons behind it, and what to check first.", {
      x: MX + 0.1, y: 3.45, w: 5.9, h: 1.1, fontFace: BODY, fontSize: 19, color: C.mintSoft,
      margin: 0, isTextBox: true, valign: "top",
    });
    s.addText("And a case history that only learns from fixes that were proved.", {
      x: MX + 0.1, y: 4.6, w: 5.9, h: 0.75, fontFace: BODY, fontSize: 17, italic: true, color: C.copperSoft,
      margin: 0, isTextBox: true, valign: "top",
    });
    s.addText("Calvin Khoo", {
      x: MX + 0.1, y: 6.35, w: 5.5, h: 0.35, fontFace: BODY, fontSize: 14, color: C.mint, margin: 0, isTextBox: true,
    });
    s.addImage({ path: asset("phone_annotated_slide.png"), x: 6.95, y: 1.05, w: 5.8, h: 4.13, shadow: shadow() });
    s.addText("A phone photo of a printed sample card. Each missing deposit is followed by an oversized one: the system reads carryover, p = 0.010.", {
      x: 6.95, y: 5.32, w: 5.8, h: 0.7, fontFace: BODY, fontSize: 12, color: C.mint, margin: 0, isTextBox: true, valign: "top",
    });
    s.addNotes(
      "~10 s. Good morning. We built the AI Dispensing Defect Detective for NSW Automation's challenge. " +
      "On the right is what it does with a phone photo: it lines the recipe up with the picture, finds three missing deposits, " +
      "each followed by an oversized one — and recognises that pattern as carryover.",
    );
  }

  // ==== 2. Problem =========================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "THE PROBLEM");
    title(s, "Dispensing defects are diagnosed by experience — and experience doesn't scale");
    const cards = [
      ["LuUserRound", "New technicians guess",
        "Inconsistent dots have at least five plausible causes. Without the experience to tell them apart, the first check is a hunch — and a wrong strip-down costs a shift."],
      ["LuShuffle", "Three changes at once",
        "Re-prime, raise the pressure, swap the needle: the defect goes away, and nobody can say which change fixed it. The next case starts from zero."],
      ["LuHistory", "Knowledge walks out the door",
        "What the senior engineer knows isn't recorded anywhere the next case can use it."],
    ];
    const cw = 3.85, gap = 0.28, top = 2.1, ch = 4.0;
    for (let i = 0; i < cards.length; i++) {
      const x = MX + i * (cw + gap);
      s.addShape("roundRect", { x, y: top, w: cw, h: ch, fill: { color: C.tint }, line: { color: C.tint }, rectRadius: 0.12 });
      await iconCircle(s, cards[i][0], x + 0.35, top + 0.35, 0.8);
      s.addText(cards[i][1], {
        x: x + 0.35, y: top + 1.35, w: cw - 0.7, h: 0.8, fontFace: BODY, fontSize: 20, bold: true, color: C.ink,
        margin: 0, isTextBox: true, valign: "top",
      });
      s.addText(cards[i][2], {
        x: x + 0.35, y: top + 2.2, w: cw - 0.7, h: 1.6, fontFace: BODY, fontSize: 15, color: C.ink2,
        margin: 0, isTextBox: true, valign: "top",
      });
    }
    footnote(s, "NSW Automation's brief: help engineers and technicians perform faster preliminary troubleshooting — not replace them.", C.muted, 6.5);
    s.addNotes(
      "~25 s. When dots come out wrong, an experienced engineer knows where to look. A new technician doesn't — " +
      "inconsistent size alone has at least five plausible causes, and a wrong guess can mean stripping a valve for nothing. " +
      "Worse: people change three things at once, the defect disappears, and nobody learns which change fixed it. " +
      "NSW asked for faster preliminary troubleshooting that helps engineers, not replaces them.",
    );
  }

  // ==== 3. How it works ====================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "HOW IT WORKS");
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
    const cy = 2.2, d = 0.95;
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
    const facts = [
      ["LuWifiOff", "Runs offline on a laptop or line PC"],
      ["LuShieldCheck", "No training data — classical, auditable vision"],
      ["LuSparkles", "LLM optional: it can disagree, it never sets a %"],
    ];
    const by = 5.55, bh = 0.9;
    s.addShape("roundRect", { x: MX, y: by, w: W - 2 * MX, h: bh, fill: { color: C.tint }, line: { color: C.tint }, rectRadius: 0.1 });
    const fw = (W - 2 * MX) / facts.length;
    for (let i = 0; i < facts.length; i++) {
      const fx = MX + i * fw + 0.35;
      await iconCircle(s, facts[i][0], fx, by + 0.2, 0.5);
      s.addText(facts[i][1], {
        x: fx + 0.65, y: by + 0.2, w: fw - 1.1, h: 0.5, fontFace: BODY, fontSize: 15, bold: true, color: C.ink,
        valign: "middle", margin: 0, isTextBox: true,
      });
    }
    s.addNotes(
      "~30 s. The operator photographs the deposits — any framing, even a phone held at an angle. " +
      "Five questions, then at most two follow-ups that the system picks because their answer would change its mind. " +
      "Seven causes from NPL's dispensing guide are ranked, every percentage built from cited reasons. " +
      "The operator looks first and changes one thing; the ranking updates live. A fresh photo verifies the fix, " +
      "and only proved fixes teach the next case. It runs offline, uses no training data, and the LLM is optional.",
    );
  }

  // ==== 4. The AI explains itself ==========================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "THE AI");
    title(s, "It asks what would change its mind — and shows why");
    const lx = MX, lw = 5.75;
    s.addText("A follow-up, chosen live", {
      x: lx, y: 1.85, w: lw, h: 0.35, fontFace: BODY, fontSize: 15, bold: true, color: C.green, margin: 0, isTextBox: true,
    });
    s.addImage({ path: asset("followup_bubble.png"), x: lx, y: 2.25, w: lw, h: lw * 250 / 1230 });
    s.addImage({ path: asset("followup_chips.png"), x: lx + 0.62, y: 3.5, w: 4.9, h: 4.9 * 150 / 1100 });
    s.addText("Every candidate question is run through the rule engine; the one asked is the one whose answer would move the ranking most.", {
      x: lx, y: 4.28, w: lw, h: 0.75, fontFace: BODY, fontSize: 14, color: C.ink2, margin: 0, isTextBox: true, valign: "top",
    });
    s.addText("The lead, explained in the brief's own terms", {
      x: lx, y: 5.15, w: lw, h: 0.35, fontFace: BODY, fontSize: 15, bold: true, color: C.green, margin: 0, isTextBox: true,
    });
    s.addImage({ path: asset("chat_because.png"), x: lx, y: 5.52, w: 5.0, h: 5.0 * 330 / 1230 });
    const rx = 6.85, rw = 5.85;
    s.addImage({ path: asset("ranking_why.png"), x: rx, y: 1.85, w: rw, h: rw * 1122 / 1400, shadow: shadow() });
    s.addText("Each reason shows its weight and the page it came from: the NPL Best Practice Guide or the NSW brief.", {
      x: rx, y: 6.67, w: rw, h: 0.5, fontFace: BODY, fontSize: 12, italic: true, color: C.muted, margin: 0, isTextBox: true, valign: "top",
    });
    s.addNotes(
      "~30 s. This is where the AI is. After the five questions it doesn't just ask more — it simulates every answer to every candidate " +
      "question and asks the one that could change its mind. Here: if the pressure gauge wanders, pressure-time variability jumps from 59 to 84 percent. " +
      "And it says why a cause leads, the way the brief asked — 'occasional, comes and goes' points at air. " +
      "On the right, every reason with its weight and the manual page. An LLM can run as a critic and disagree, but it never sets a number.",
    );
  }

  // ==== 5. Evidence ========================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "THE EVIDENCE");
    title(s, "When it says it's confident, it's right");
    s.addChart(pres.charts.BAR, [{
      name: "Top cause correct",
      labels: ["★", "★★", "★★★", "★★★★"],
      values: [52, 75, 95, 97],
    }], {
      x: MX, y: 1.8, w: 6.7, h: 4.55, barDir: "col", chartColors: [C.green], barGapWidthPct: 85,
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0"%"', dataLabelFontSize: 16,
      dataLabelFontFace: BODY, dataLabelColor: C.ink, dataLabelFontBold: true,
      valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 110, valGridLine: { style: "none" },
      catAxisLabelFontSize: 20, catAxisLabelColor: C.ink2, catAxisLabelFontFace: BODY, catAxisLineShow: true,
      catAxisLineColor: "C3C2B7", catGridLine: { style: "none" }, showLegend: false,
      showTitle: true, title: "Top cause correct, by stars shown to the operator", titleFontSize: 14,
      titleColor: C.ink2, titleFontFace: BODY,
    });
    s.addText("Photo + answers · 420 simulated cases at three answer-reliability levels · chance = 14%", {
      x: MX, y: 6.38, w: 6.7, h: 0.3, fontFace: BODY, fontSize: 12, color: C.muted, margin: 0, isTextBox: true, align: "center",
    });
    const stats = [
      ["66%", "top cause right from one photo and five answers, with an operator whose answers are only 75% reliable — chance is 14%"],
      ["6,600", "synthetic photos and 420 simulated cases through the real code, in every evaluation run (about a minute)"],
      ["79", "automated checks — 52 backend tests, 25 measurement oracles, 2 golden cases — plus a browser run of the whole wizard"],
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
    s.addNotes(
      "~25 s. We measured confidence instead of asserting it. When the system shows three stars, the top cause is right 95 percent of the time; " +
      "at one star, 52 — so the stars mean something an operator can act on. From one photo and five answers it gets the cause right 66 percent " +
      "of the time even when a quarter of the answers are wrong; chance is 14. Every number comes from 6,600 synthetic photos run through the real code — " +
      "synthetic, because no production photos were available.",
    );
  }

  // ==== 6. Phone photo =====================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "FEASIBILITY");
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
    s.addNotes(
      "~20 s. A photo-based tool is only useful if it works on the photo people actually take. Our own stress test showed it only measured photos framed " +
      "exactly like the recipe — so we fixed that. It now lines the recipe up with the photo — scale, rotation, even camera tilt — so a phone photo of the part on a desk measures " +
      "the same as a perfect one: 89 percent, zero false alarms. You'll see it live in the demo.",
    );
  }

  // ==== 7. Proved vs fixed =================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "TRUST");
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
    s.addNotes(
      "~25 s. This is what makes the history trustworthy. A case closes CONFIRMED only when five things were proved — one cause confirmed, " +
      "exactly one change aimed at it, re-measured against a before photo, in spec on everything a photo can check, and held for 20 shots. " +
      "Anything less is filed as PLAUSIBLE or UNVERIFIED with the gap named, and doesn't teach future cases. " +
      "And history can only lower confidence, never raise it — otherwise the system would grow more confident the longer it ran, right or not.",
    );
  }

  // ==== 8. Impact & pilot ==================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.dark };
    s.addText("INDUSTRY IMPACT", {
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
    s.addText("Live demo next →", {
      x: MX, y: 6.45, w: W - 2 * MX, h: 0.5, fontFace: HEAD, fontSize: 22, bold: true, color: C.copperSoft, align: "right", margin: 0, isTextBox: true,
    });
    s.addNotes(
      "~15 s. On day one: a new technician's first check, ranked with reasons; an audit-ready report; and a history that only keeps proved fixes — " +
      "all offline on a line PC with a phone camera. To pilot it: validate on real NSW photos, remove clutter with a bare-board reference, let engineers " +
      "add causes as data, and open cases automatically when a line starts drifting. Let me show you.",
    );
  }

  // ==== Backup: tiers ======================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "BACKUP · CONFIDENCE TIERS", C.muted);
    title(s, "Four confidence tiers — and agreement never raises one");
    const rows = [
      ["Tier", "Reached when", "What the operator sees"],
      ["T1", "Rule engine and critic agree · deciding measurement beats chance · ≥3 similar confirmed cases, none contradicting", "One lead cause, with evidence and matching past cases"],
      ["T2", "They agree, but no precedent or the measurement isn't decisive", "One lead cause, marked provisional, with what would confirm it"],
      ["T3", "They disagree · the measurement beats chance", "Both candidates; the measurement holds the top slot"],
      ["T4", "They disagree · the measurement can't separate them", "No lead cause — the check that would separate them"],
    ];
    s.addTable(rows.map((r, i) => r.map((cell, j) => ({
      text: cell,
      options: {
        bold: i === 0 || j === 0, color: i === 0 ? C.white : C.ink, fill: { color: i === 0 ? C.green : i % 2 ? C.tint : C.white },
        fontFace: BODY, fontSize: 14, valign: "middle", margin: [0.08, 0.12, 0.08, 0.12],
      },
    }))), { x: MX, y: 1.85, w: W - 2 * MX, colW: [0.9, 6.0, 5.233], border: { type: "solid", pt: 0.75, color: "D7E3DC" }, rowH: 0.62 });
    s.addText([
      { text: "Gate A — chance. ", options: { bold: true } },
      { text: "Only a signal that separates causes counts: the dispense-order pattern (binomial test, p < 0.05). A size spread is real but shared by several causes, so it can't decide.", options: { breakLine: true } },
      { text: "Gate B — precedent. ", options: { bold: true } },
      { text: "Similar confirmed cases (same material and dispenser, signals within one spread) can demote the lead by up to 0.4 log-odds — never promote it." },
    ], { x: MX, y: 5.35, w: W - 2 * MX, h: 1.3, fontFace: BODY, fontSize: 14, color: C.ink2, margin: 0, isTextBox: true, paraSpaceAfter: 6, valign: "top" });
    s.addNotes("Backup for 'how do you decide confidence?' and 'what if the AI and the rules disagree?'.");
  }

  // ==== Backup: reliability ================================================
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

  // ==== Backup: stress =====================================================
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

  // ==== Backup: what's ours ================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "BACKUP · RULE c.2 DECLARATION", C.muted);
    title(s, "What we built, and what we used");
    const ours = [
      "Fault tree and its weighted, cited rules",
      "Two-pass ranking, chance and precedent gates, T1–T4",
      "The five-condition close rule",
      "Five-axis interview and follow-up selection",
      "Retrieval and precedent counting",
      "Photo registration, desk masking, metrology",
      "Synthetic defect generator and the evaluation",
    ];
    const theirs = [
      "NPL Report MATC(A)82 — Best Practice for Electronic Materials Dispensing (2001), © Crown copyright",
      "NSW Automation challenge brief",
      "FastAPI, Pydantic, SQLAlchemy, Alembic · OpenCV, NumPy",
      "Next.js, React, Tailwind, shadcn/ui, Base UI, lucide",
      "Groq API, openai/gpt-oss-20b — optional critic, mapping, explanation",
      "Dev only: pytest, Playwright, matplotlib",
    ];
    const col = (x, head, items, fill) => {
      s.addShape("roundRect", { x, y: 1.85, w: 5.85, h: 4.65, fill: { color: fill }, line: { color: fill }, rectRadius: 0.12 });
      s.addText(head, { x: x + 0.35, y: 2.05, w: 5.15, h: 0.45, fontFace: BODY, fontSize: 19, bold: true, color: C.ink, margin: 0, isTextBox: true });
      s.addText(items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < items.length - 1 } })), {
        x: x + 0.35, y: 2.65, w: 5.15, h: 3.7, fontFace: BODY, fontSize: 16, color: C.ink2, paraSpaceAfter: 8, margin: 0, isTextBox: true, valign: "top",
      });
    };
    col(MX, "Our own work", ours, C.tint);
    col(MX + 6.25, "Third-party, declared", theirs, "F4F4F2");
    footnote(s, "No model was trained or fine-tuned, and no training data was used. Every measurement is reproducible by an engineer with a microscope.", C.muted, 6.6);
    s.addNotes("Backup for originality questions (rule c.2/c.3).");
  }

  // ==== Backup: limitations ================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    kicker(s, "BACKUP · LIMITATIONS", C.muted);
    title(s, "Known limitations, stated up front");
    const lim = [
      ["No real production photos", "Every threshold is tuned on synthetic images; the stress test measures how far that holds, it doesn't claim real-photo accuracy."],
      ["Seven causes", "Stringing, smearing and satellites (up height, NPL §3.3) have no cause yet — they're reported as 'no cause ahead' and escalated."],
      ["Busy boards", "A trace touching a deposit can read as a distorted shape: 9% false alarms under light clutter."],
      ["Pixels, not microns", "Absolute volume needs a scale reference; today everything is relative to the recipe."],
      ["The LLM isn't reproducible", "Critic and explanation can vary between runs — which is why neither can change a likelihood."],
    ];
    for (let i = 0; i < lim.length; i++) {
      const y = 1.9 + i * 0.95;
      await iconCircle(s, "LuTriangleAlert", MX, y + 0.05, 0.55, "8A8984");
      s.addText(lim[i][0], { x: MX + 0.8, y, w: 3.6, h: 0.65, fontFace: BODY, fontSize: 16, bold: true, color: C.ink, valign: "middle", margin: 0, isTextBox: true });
      s.addText(lim[i][1], { x: MX + 4.5, y, w: 7.6, h: 0.65, fontFace: BODY, fontSize: 14, color: C.ink2, valign: "middle", margin: 0, isTextBox: true });
    }
    s.addNotes("Backup for 'what doesn't it do?' — say these before a judge has to find them.");
  }

  const out = path.join(__dirname, "AI-Dispensing-Defect-Detective.pptx");
  await pres.writeFile({ fileName: out });
  console.log("wrote", out);
}

build().catch((err) => {
  console.error(err);
  process.exit(1);
});
