/** Shared by the rules page's list and map: how a rule's weight is shown
 * and said. Weights are log-odds, as ranking/rules.py states them. */

import { formatWeight } from "@/lib/sources";

/** Column headers have room for two short lines; the full label is one
 * click away in the detail strip. */
export const SHORT_NAMES: Record<string, string> = {
  volume_too_small_carryover: "Carryover",
  pressure_time_instability: "Pressure-time",
  air_in_fluid_path: "Air in syringe",
  material_rheology_change: "Material change",
  nozzle_blockage: "Needle blockage",
  dispense_height_or_board_bending: "Height or board bend",
  equipment_condition: "Equipment",
};

/** Green for, red against, deeper for stronger; grey when an engineer
 * switched the rule off. Literal class names so Tailwind can see them. */
export function tone(weight: number): string {
  const w = Math.abs(weight);
  if (weight === 0) return "bg-muted text-muted-foreground";
  if (weight > 0) {
    if (w >= 2) return "bg-emerald-600 text-white dark:bg-emerald-500 dark:text-emerald-950";
    if (w >= 1.2) return "bg-emerald-500/35 text-emerald-950 dark:text-emerald-100";
    if (w >= 0.7) return "bg-emerald-500/20 text-emerald-900 dark:text-emerald-200";
    return "bg-emerald-500/10 text-emerald-800 dark:text-emerald-300";
  }
  return w >= 0.7
    ? "bg-rose-500/25 text-rose-900 dark:text-rose-200"
    : "bg-rose-500/15 text-rose-800 dark:text-rose-300";
}

/** A weight as its chip shows it: "+1.1", "−0.8", or "off". */
export function weightText(weight: number): string {
  return weight === 0 ? "off" : formatWeight(weight);
}

/** "Response: purging or a new syringe helps" → "Purging or a new syringe helps". */
export function ruleName(label: string): string {
  const name = label.replace(/^Response: /, "");
  return name.charAt(0).toUpperCase() + name.slice(1);
}

/** What a log-odds weight does, in words: +1.1 multiplies the odds by 3.0. */
export function oddsEffect(weight: number, cause: string): string {
  const factor = Math.exp(weight);
  return factor >= 1
    ? `multiplies the odds of ${cause} by ${factor >= 10 ? Math.round(factor) : factor.toFixed(1)}`
    : `cuts the odds of ${cause} to ${Math.round(factor * 100)}% of what they were`;
}
