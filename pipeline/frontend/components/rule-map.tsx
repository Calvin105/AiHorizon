"use client";

import * as React from "react";
import { Check, Play, RotateCcw, TrendingUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { EvidenceGroup, EvidenceRow, RuleCell, RuleMap as RuleTable } from "@/lib/api/types";
import { SHORT_NAMES, oddsEffect, ruleName, tone, weightText } from "@/lib/rules";
import { formatSource, formatWeight, plainDetail, shortCause } from "@/lib/sources";
import { cn } from "@/lib/utils";

/** The demo case's photo and answers, before its follow-ups
 * (docs/final/demo-runbook.md). Air and pressure-time tie at 59%. */
const DEMO_CASE = ["photo:size_cv", "trajectory:random", "footprint:material", "response:purge_or_prime"];

const logit = (p: number) => Math.log(p / (1 - p));
const sigmoid = (x: number) => 1 / (1 + Math.exp(-x));
const asPct = (p: number) => `${Math.round(p * 100)}%`;

type Focus =
  | { kind: "row"; rowId: string }
  | { kind: "cell"; rowId: string; causeId: string }
  | { kind: "cause"; causeId: string };

interface Indexed {
  row: EvidenceRow;
  group: EvidenceGroup;
}

/** Ticking follows the interview: one answer per single-choice question,
 * and measurements that can't both count replace each other. */
function withToggled(ticked: string[], entry: Indexed): string[] {
  const { row, group } = entry;
  if (ticked.includes(row.id)) return ticked.filter((id) => id !== row.id);
  const siblings = new Set(group.single ? group.rows.map((r) => r.id) : []);
  return [...ticked.filter((id) => !siblings.has(id) && !row.excludes.includes(id)), row.id];
}

function scoresFor(table: RuleTable, index: Map<string, Indexed>, ticked: string[]): Record<string, number> {
  const totals: Record<string, number> = {};
  for (const cause of table.causes) totals[cause.cause_id] = logit(table.prior);
  for (const id of ticked) {
    for (const cell of index.get(id)?.row.cells ?? []) totals[cell.cause_id] += cell.weight;
  }
  return Object.fromEntries(Object.entries(totals).map(([id, x]) => [id, sigmoid(x)]));
}

/**
 * The rule engine as a table: every answer and measurement it knows (rows)
 * against every cause (columns), each cell a cited rule. Ticking rows adds
 * them up exactly as the engine does, so the percentages in the header are
 * the ones a case with those answers would get from the rule engine.
 */
export function RuleMap({ table, className }: { table: RuleTable; className?: string }) {
  const [ticked, setTicked] = React.useState<string[]>([]);
  const [hovered, setHovered] = React.useState<Focus | null>(null);
  const [pinned, setPinned] = React.useState<Focus | null>(null);

  const index = React.useMemo(() => {
    const out = new Map<string, Indexed>();
    for (const group of table.groups) for (const row of group.rows) out.set(row.id, { row, group });
    return out;
  }, [table]);

  const scores = React.useMemo(() => scoresFor(table, index, ticked), [table, index, ticked]);

  // Hovering an answer previews what ticking it would do to every cause.
  const previewRowId = hovered?.kind === "row" ? hovered.rowId : null;
  const preview = React.useMemo(() => {
    const entry = previewRowId ? index.get(previewRowId) : undefined;
    return entry ? scoresFor(table, index, withToggled(ticked, entry)) : null;
  }, [table, index, ticked, previewRowId]);

  const name = (causeId: string) =>
    SHORT_NAMES[causeId] ?? shortCause(table.causes.find((c) => c.cause_id === causeId)?.label ?? causeId);
  const ranked = [...table.causes].sort((a, b) => scores[b.cause_id] - scores[a.cause_id]);
  // Within half a point of the top is a tie, and a tie names no leader.
  const top = scores[ranked[0].cause_id];
  const leaders = ticked.length > 0 ? ranked.filter((c) => top - scores[c.cause_id] < 0.005).map((c) => c.cause_id) : [];
  const focus = hovered ?? pinned;
  const focusCause = focus && focus.kind !== "row" ? focus.causeId : null;
  const focusRow = focus && focus.kind !== "cause" ? focus.rowId : null;

  function toggle(entry: Indexed) {
    setTicked((prev) => withToggled(prev, entry));
  }

  function pin(next: Focus) {
    setPinned((prev) => (JSON.stringify(prev) === JSON.stringify(next) ? null : next));
  }

  return (
    <section
      className={cn("space-y-3", className)}
      aria-label="Rule map"
      onKeyDown={(e) => {
        if (e.key === "Escape") setPinned(null);
      }}
    >
      <div className="flex flex-wrap items-end justify-between gap-x-4 gap-y-2">
        <p className="min-w-0 max-w-2xl text-sm text-muted-foreground">
          Rows are what the photo and the operator can tell it; columns are the causes. Tick what you
          see and each cause&apos;s percentage builds up from {asPct(table.prior)}, exactly as a case
          would be ranked: green adds, red takes away.
        </p>
        <div className="flex shrink-0 gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setTicked(DEMO_CASE.filter((id) => index.has(id)));
              setPinned(null);
            }}
          >
            <Play /> Load the demo case
          </Button>
          <Button
            variant="ghost"
            size="sm"
            disabled={ticked.length === 0}
            onClick={() => {
              setTicked([]);
              setPinned(null);
            }}
          >
            <RotateCcw /> Clear
          </Button>
        </div>
      </div>

      <div
        className="max-h-[min(64vh,40rem)] overflow-auto rounded-xl border"
        onMouseLeave={() => setHovered(null)}
      >
        <table className="w-full min-w-[37rem] border-separate border-spacing-0 text-sm">
          <thead>
            <tr>
              <th
                scope="col"
                className="sticky top-0 left-0 z-30 w-[34%] border-b bg-background px-3 py-2 text-left align-bottom text-xs font-normal text-muted-foreground"
              >
                Tick what you see
              </th>
              {table.causes.map((cause) => {
                const score = scores[cause.cause_id];
                const next = preview?.[cause.cause_id];
                const moves = next !== undefined && Math.round(next * 100) !== Math.round(score * 100);
                const leads = leaders.includes(cause.cause_id);
                return (
                  <th
                    key={cause.cause_id}
                    scope="col"
                    className={cn(
                      "sticky top-0 z-20 border-b bg-background px-1 pt-2 pb-1.5 align-bottom font-normal",
                      focusCause === cause.cause_id && "bg-muted",
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => pin({ kind: "cause", causeId: cause.cause_id })}
                      onMouseEnter={() => setHovered({ kind: "cause", causeId: cause.cause_id })}
                      onFocus={() => setHovered({ kind: "cause", causeId: cause.cause_id })}
                      onBlur={() => setHovered(null)}
                      className="flex w-full flex-col items-center gap-1 rounded-md px-0.5 py-0.5 hover:bg-muted"
                      aria-label={`${cause.label}: ${asPct(score)}. Show why.`}
                    >
                      <span className="line-clamp-2 flex h-[2.3em] items-end text-center text-[0.68rem] leading-tight font-medium text-muted-foreground">
                        {name(cause.cause_id)}
                      </span>
                      <span
                        className={cn(
                          "text-base leading-none font-semibold tabular-nums",
                          leads ? "text-emerald-700 dark:text-emerald-400" : ticked.length === 0 && "text-muted-foreground",
                        )}
                      >
                        {asPct(score)}
                      </span>
                      <span className="h-3.5 text-[0.65rem] leading-none font-medium tabular-nums">
                        {moves ? (
                          <span className={next > score ? "text-emerald-700 dark:text-emerald-400" : "text-rose-700 dark:text-rose-400"}>
                            → {asPct(next)}
                          </span>
                        ) : leads ? (
                          <span className="text-emerald-700 dark:text-emerald-400">
                            {leaders.length > 1 ? "tied" : "leads"}
                          </span>
                        ) : null}
                      </span>
                      <span className="block h-1.5 w-full overflow-hidden rounded-full bg-muted">
                        <span
                          className={cn(
                            "block h-full rounded-full transition-[width] duration-300",
                            leads ? "bg-emerald-600" : "bg-foreground/35",
                          )}
                          style={{ width: `${score * 100}%` }}
                        />
                      </span>
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>
          {table.groups.map((group) => {
            const rows = group.rows.filter((r) => r.cells.length > 0);
            const silent = group.rows.filter((r) => r.cells.length === 0);
            return (
              <tbody key={group.id}>
                <tr>
                  <th colSpan={table.causes.length + 1} scope="rowgroup" className="border-b bg-muted/70 p-0 text-left font-normal">
                    <div className="sticky left-0 w-max max-w-[min(calc(100vw_-_2.75rem),44rem)] px-3 py-1.5">
                      <p className="text-[0.68rem] font-semibold tracking-wide text-foreground uppercase">
                        {group.title}
                        <span className="ml-2 font-normal tracking-normal text-muted-foreground normal-case">
                          {group.prompt}
                        </span>
                      </p>
                      {group.note && <p className="text-[0.68rem] text-muted-foreground">{group.note}</p>}
                    </div>
                  </th>
                </tr>
                {rows.map((row) => {
                  const entry = index.get(row.id)!;
                  const on = ticked.includes(row.id);
                  return (
                    <tr key={row.id} className={cn(on && "bg-emerald-50 dark:bg-emerald-950/40")}>
                      <th
                        scope="row"
                        className={cn(
                          "sticky left-0 z-10 border-b px-1.5 py-0.5 text-left font-normal",
                          on ? "bg-emerald-50 dark:bg-emerald-950" : "bg-background",
                        )}
                      >
                        <button
                          type="button"
                          aria-pressed={on}
                          onClick={() => toggle(entry)}
                          onMouseEnter={() => setHovered({ kind: "row", rowId: row.id })}
                          onFocus={() => setHovered({ kind: "row", rowId: row.id })}
                          onBlur={() => setHovered(null)}
                          className={cn(
                            "flex w-full items-center gap-2 rounded-md px-1.5 py-1 text-left hover:bg-muted",
                            focusRow === row.id && "bg-muted",
                          )}
                        >
                          <span
                            className={cn(
                              "flex size-4 shrink-0 items-center justify-center border",
                              group.single ? "rounded-full" : "rounded",
                              on ? "border-emerald-600 bg-emerald-600 text-white" : "border-foreground/30 bg-background",
                            )}
                            aria-hidden
                          >
                            {on && <Check className="size-3" strokeWidth={3} />}
                          </span>
                          <span className="min-w-0 text-[0.78rem] leading-snug">{row.label}</span>
                        </button>
                      </th>
                      {table.causes.map((cause) => {
                        const cell = row.cells.find((c) => c.cause_id === cause.cause_id);
                        return (
                          <td
                            key={cause.cause_id}
                            className={cn(
                              "border-b px-1 py-0.5 text-center",
                              focusCause === cause.cause_id && !on && "bg-muted/70",
                            )}
                          >
                            {cell && (
                              <button
                                type="button"
                                onClick={() => pin({ kind: "cell", rowId: row.id, causeId: cause.cause_id })}
                                onMouseEnter={() => setHovered({ kind: "cell", rowId: row.id, causeId: cause.cause_id })}
                                onFocus={() => setHovered({ kind: "cell", rowId: row.id, causeId: cause.cause_id })}
                                onBlur={() => setHovered(null)}
                                className={cn(
                                  "inline-flex min-w-[2.9rem] items-center justify-center gap-0.5 rounded-md px-1.5 py-0.5 font-mono text-xs font-semibold tabular-nums transition-shadow",
                                  tone(cell.weight),
                                  on && "ring-2 ring-emerald-700/50 ring-offset-1 ring-offset-emerald-50 dark:ring-offset-emerald-950",
                                  focus?.kind === "cell" && focus.rowId === row.id && focus.causeId === cause.cause_id && "ring-2 ring-foreground/60",
                                )}
                                aria-label={`${row.label}: ${weightText(cell.weight)} for ${cause.label}, from ${formatSource(cell.source)}`}
                              >
                                {row.mild_text && cell.weight !== 0 && <TrendingUp className="size-3" aria-hidden />}
                                {weightText(cell.weight)}
                              </button>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
                {silent.length > 0 && (
                  <tr>
                    <td colSpan={table.causes.length + 1} className="border-b p-0">
                      <p className="sticky left-0 w-max max-w-[min(calc(100vw_-_2.75rem),44rem)] px-3 py-1 text-[0.68rem] text-muted-foreground">
                        No evidence either way: {silent.map((r) => r.label).join(" · ")}
                      </p>
                    </td>
                  </tr>
                )}
              </tbody>
            );
          })}
        </table>
      </div>

      <div className="min-h-[5.75rem] rounded-xl bg-muted/60 px-4 py-3 text-sm" aria-live="polite">
        <Detail
          table={table}
          index={index}
          ticked={ticked}
          scores={scores}
          ranked={ranked.map((c) => c.cause_id)}
          focus={focus}
          name={name}
        />
      </div>

      <p className="text-xs leading-relaxed text-muted-foreground">
        Weights are log-odds: +1 multiplies a cause&apos;s odds by 2.7. Each cause has its own %, so they
        don&apos;t add up to 100. A logged check adds {formatWeight(table.check_confirms)} to a cause it
        confirms and {formatWeight(table.check_rules_out)} to one it rules out. This is the rule engine
        alone; the LLM critic and the two gates then decide how sure to be.
      </p>
    </section>
  );
}

function Detail({
  table, index, ticked, scores, ranked, focus, name,
}: {
  table: RuleTable;
  index: Map<string, Indexed>;
  ticked: string[];
  scores: Record<string, number>;
  ranked: string[];
  focus: Focus | null;
  name: (causeId: string) => string;
}) {
  if (focus?.kind === "cell") {
    const entry = index.get(focus.rowId);
    const cell = entry?.row.cells.find((c) => c.cause_id === focus.causeId);
    if (entry && cell) return <CellDetail row={entry.row} cell={cell} causeName={name(cell.cause_id)} />;
  }

  if (focus?.kind === "row") {
    const entry = index.get(focus.rowId);
    if (entry) {
      return (
        <div className="space-y-1.5">
          <p>
            <span className="font-medium">{entry.row.label}</span>
            {entry.row.help && <span className="text-muted-foreground"> — {entry.row.help}</span>}
          </p>
          <p className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
            {ticked.includes(entry.row.id) ? "Ticked. Click again to untick." : "Ticking it moves"}
            {!ticked.includes(entry.row.id) &&
              entry.row.cells.map((cell) => (
                <span key={cell.cause_id} className="inline-flex items-center gap-1">
                  <span className={cn("rounded px-1 font-mono font-semibold", tone(cell.weight))}>
                    {weightText(cell.weight)}
                  </span>
                  <span className="text-foreground">{name(cell.cause_id)}</span>
                </span>
              ))}
          </p>
          <p className="text-xs text-muted-foreground">{entry.group.title} · {entry.group.prompt}</p>
        </div>
      );
    }
  }

  if (focus?.kind === "cause") {
    const cause = table.causes.find((c) => c.cause_id === focus.causeId);
    if (cause) {
      const parts = ticked.flatMap((id) => {
        const entry = index.get(id);
        const cell = entry?.row.cells.find((c) => c.cause_id === cause.cause_id);
        return entry && cell ? [{ row: entry.row, cell }] : [];
      });
      return (
        <div className="space-y-1.5">
          <p>
            <span className="font-medium">Why {asPct(scores[cause.cause_id])}?</span>{" "}
            <span className="text-muted-foreground">{cause.label}</span>
          </p>
          <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
            <span className="rounded bg-background px-1.5 py-0.5">starts at {asPct(table.prior)}</span>
            {parts.map(({ row, cell }) => (
              <span key={row.id} className="inline-flex items-center gap-1">
                <span className={cn("rounded px-1 font-mono font-semibold", tone(cell.weight))}>
                  {weightText(cell.weight)}
                </span>
                {row.label}
                <span className="text-muted-foreground italic">({formatSource(cell.source)})</span>
              </span>
            ))}
            <span className="font-semibold">= {asPct(scores[cause.cause_id])}</span>
          </p>
          <p className="text-xs text-muted-foreground">
            {parts.length === 0 ? "Nothing ticked moves it yet. " : ""}
            {cause.rule_count} rules can move it: read down its column.
          </p>
        </div>
      );
    }
  }

  // Nothing in focus: say what to do, or what the ticks add up to.
  if (ticked.length === 0) {
    return (
      <p className="text-muted-foreground">
        <span className="font-medium text-foreground">Try it.</span> Tick what you see on the line, or load
        the demo case, and watch the percentages above. Hover an answer to preview its effect, hover a
        number for its rule and page, and click a cause to see why it sits where it does.
      </p>
    );
  }
  const [first, second] = ranked;
  const isDemo = ticked.length === DEMO_CASE.length && DEMO_CASE.every((id) => ticked.includes(id));
  const tied = second !== undefined && Math.abs(scores[first] - scores[second]) < 0.005;
  if (isDemo) {
    return (
      <p>
        <span className="font-medium">The demo case, before its follow-ups:</span>{" "}
        {name(first).toLowerCase()} and {name(second).toLowerCase()} tie at {asPct(scores[first])}. A tie is
        when the system asks a follow-up, and here it asks about the pressure gauge. Hover the answers under{" "}
        <span className="font-medium">Follow-up · Pressure gauge</span> to see which way each one breaks it.
      </p>
    );
  }
  if (tied) {
    return (
      <p>
        {name(first)} and {name(second).toLowerCase()} are tied at {asPct(scores[first])}. In a real case
        the system would now ask the follow-up whose answer moves them most.
      </p>
    );
  }
  return (
    <p>
      <span className="font-medium">{name(first)} leads at {asPct(scores[first])}</span>
      <span className="text-muted-foreground">
        {" "}— click its column to see why, or tick more to see what changes.
      </span>
    </p>
  );
}

function CellDetail({ row, cell, causeName }: { row: EvidenceRow; cell: RuleCell; causeName: string }) {
  return (
    <div className="space-y-1">
      <p className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
        <span className={cn("rounded px-1.5 font-mono text-xs font-semibold", tone(cell.weight))}>
          {weightText(cell.weight)}
        </span>
        <span className="font-medium">{ruleName(cell.label)}</span>
        <span className="text-muted-foreground">→ {causeName}</span>
        <span className="ml-auto text-xs whitespace-nowrap text-sky-700 italic dark:text-sky-400">
          {formatSource(cell.source)}
        </span>
      </p>
      <p className="text-[0.8rem] text-muted-foreground">{plainDetail(cell.detail)}</p>
      <p className="text-xs text-muted-foreground">
        {cell.weight === 0
          ? "Switched off on the List tab, so it adds nothing until it is restored."
          : (row.mild_text && cell.weight_mild !== null
              ? `Grows with the reading: ${formatWeight(cell.weight_mild)} at ${row.mild_text}, ` +
                `${formatWeight(cell.weight)} at ${row.strong_text}. `
              : "") + `${formatWeight(cell.weight)} ${oddsEffect(cell.weight, causeName.toLowerCase())}.`}
      </p>
    </div>
  );
}
