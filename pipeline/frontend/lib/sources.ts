/** Rule sources, in words a reader outside the team recognises.
 *
 * Every rule in the backend carries a terse citation — "matc82 sec 3.5
 * p.18-19", "brief p.3" — which is exact but means nothing to someone who
 * hasn't read the repo. These expand it, and SOURCE_NOTES says what each
 * document is, so every percentage on screen can be traced to a page. */

export const SOURCE_NOTES = [
  {
    short: "NPL guide",
    full:
      "NPL Report MATC(A)82 — A Guide to Best Practice for Electronic Materials Dispensing " +
      "(Brewin, Zou & Hunt, National Physical Laboratory, 2001). © Crown copyright; extracts " +
      "reproduced with acknowledgement.",
  },
  { short: "NSW brief", full: "AI Dispensing Defect Detective — NSW Automation challenge statement, AI Horizon 2026." },
] as const;

/** "matc82 sec 3.5 p.18-19" → "NPL guide §3.5, p.18–19". */
export function formatSource(source: string): string {
  const npl = source.match(/^matc82 sec ([\d.]+) p\.([\d-]+)$/);
  if (npl) return `NPL guide §${npl[1]}, p.${npl[2].replace("-", "–")}`;
  const brief = source.match(/^brief p\.([\d-]+)$/);
  if (brief) return `NSW brief p.${brief[1].replace("-", "–")}`;
  if (source === "troubleshooting loop") return "a check on this case";
  return source;
}

/** A rule's log-odds weight as a signed chip: "+1.4", "−0.8". */
export function formatWeight(weight: number): string {
  const sign = weight > 0 ? "+" : weight < 0 ? "−" : "±";
  return `${sign}${Math.abs(weight).toFixed(1)}`;
}

/** The short cause name, without the parenthetical gloss — "Dispensed
 * volume too small to wet the pad" rather than the whole label. */
export function shortCause(label: string): string {
  return label.split(" (")[0];
}

/** The top reasons behind a cause, as the clause after "because". */
export function becauseClause(evidence: { label: string; source: string; weight: number }[], max = 2): string {
  const reasons = evidence
    .filter((e) => e.weight > 0)
    .slice(0, max)
    .map((e) => {
      const reason = e.label.replace(/^Response: /, "").replace(/^Check: /, "check: ");
      return `${reason.charAt(0).toLowerCase()}${reason.slice(1)} (${formatSource(e.source)})`;
    });
  return reasons.join("; ");
}

/** Every terse citation inside a sentence — the written explanation quotes
 * them as the rules carry them — expanded the same way as formatSource. */
export function formatCitations(text: string): string {
  return text
    .replace(/matc82 sec ([\d.]+) p\.([\d-]+)/g, (_, sec: string, page: string) => `NPL guide §${sec}, p.${page.replace("-", "–")}`)
    .replace(/brief p\.([\d-]+)/g, (_, page: string) => `NSW brief p.${page.replace("-", "–")}`);
}

/** Rule details mention the guide by its file name ("matc82's fix for big
 * dot / small dot…"). On screen it is the NPL guide, as every citation is. */
export function plainDetail(text: string): string {
  return formatCitations(text)
    .replace(/^matc82\b/, "The NPL guide")
    .replace(/\bmatc82\b/g, "the NPL guide");
}
